"""Campus Customs chatbot agent: loads the prompt, connects the model through Portkey, wires the tools.

    reply = await run_chat("do you have it in pink?", history=[...], customer=Customer(...), page=PageContext(...))

The system prompt is backend/prompts/prompt.md. It is re-read on every request, so prompt edits
take effect without restarting the server.
"""

from __future__ import annotations

import asyncio
import os
import re
from functools import cache
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, UsageLimits
from pydantic_ai.exceptions import ModelHTTPError, UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from audit import AuditTrail, short
from models import ChatResponse, ChatTurn, Customer, PageContext, ShopReply
from privacy import reply_problems
from tools import SHOP_TOOLS, ShopDeps, describe_page, page_results, product_cards

BACKEND = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND / "prompts" / "prompt.md"

# The key lives in the repository-root .env (my_app/.env); hw4/.env or backend/.env also work.
for env_dir in (BACKEND, BACKEND.parent, BACKEND.parent.parent):
    load_dotenv(env_dir / ".env")

MODEL_NAME = os.getenv("CAMPUS_CUSTOMS_MODEL", "gpt-5.6")
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
REQUEST_LIMIT = 10  # model calls per shopper message (tool calls and retries included)

# Shown when the provider's content filter blocks a message (e.g. jailbreak attempts, card numbers).
FILTERED_REPLY = (
    "Sorry, I can't help with that one. I'm here for Campus Customs gear: hoodies, tees, sizes and gift ideas. "
    "Please don't share passwords or card numbers in chat. What can I help you find?"
)


# Shown if the model keeps quoting prices/quantities it never looked up, even after being told to fix it.
UNVERIFIED_REPLY = (
    "Sorry, I couldn't double-check those prices and stock numbers just now. "
    "Please open the product page for the exact price and sizes, or ask me again."
)

PRICE_RE = re.compile(r"\$\s?(\d+(?:\.\d{1,2})?)")
QUANTITY_RE = re.compile(
    r"\b(\d+)\s+(?:left|in stock|available|units?|remaining|pieces?)\b|\bonly\s+(\d+)\b", re.IGNORECASE
)


# Shown if the agent loop uses up REQUEST_LIMIT model calls without finishing.
LIMIT_REPLY = (
    "Sorry, that one took me too many steps to work out. Could you ask a simpler or more specific question, "
    "like a product name, type or color?"
)
OUTPUT_TOOL = "final_result"  # PydanticAI's tool for returning the structured ShopReply


class MissingAPIKey(RuntimeError):
    pass


@cache
def get_model() -> OpenAIChatModel:
    api_key = os.getenv("PORTKEY_API_KEY", "").strip()
    if not api_key:
        raise MissingAPIKey("PORTKEY_API_KEY is missing from the .env file.")
    client = AsyncOpenAI(
        base_url=PORTKEY_BASE_URL,
        api_key=api_key,
        default_headers={"x-portkey-api-key": api_key},
        max_retries=3,
        timeout=60,
    )
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))


@cache
def build_agent() -> Agent[ShopDeps, ShopReply]:
    agent = Agent(get_model(), deps_type=ShopDeps, output_type=ShopReply, tools=SHOP_TOOLS, retries=2)

    @agent.instructions
    def system_prompt() -> str:
        return PROMPT_PATH.read_text()

    @agent.instructions
    def shopper(ctx: RunContext[ShopDeps]) -> str:
        c = ctx.deps.customer
        if c is None:
            return (
                "## Who you're talking to\nA guest (not logged in). This chat is not saved; if they want you to "
                "remember things next time, suggest creating an account or logging in."
            )
        return (
            f"## Who you're talking to\nLogged-in customer: {c.first_name} {c.last_name}, email {c.email}. "
            "That is everything you know about them; don't ask for more personal details. "
            "Their earlier chats with you are in the message history."
        )

    @agent.instructions
    async def current_page(ctx: RunContext[ShopDeps]) -> str:
        return "## Current page\n" + await asyncio.to_thread(describe_page, ctx.deps.page, ctx.deps)

    @agent.output_validator
    def no_invented_numbers(ctx: RunContext[ShopDeps], output: ShopReply) -> ShopReply:
        """Reject a reply that quotes a price or stock quantity no tool returned in this request.
        Numbers the shopper typed (e.g. "under $70") are allowed."""
        said = {float(n) for n in re.findall(r"\d+(?:\.\d+)?", ctx.deps.shopper_text)}
        bad_prices = [f"${p}" for p in PRICE_RE.findall(output.reply) if float(p) not in ctx.deps.seen_prices | said]
        quantities = [int(a or b) for a, b in QUANTITY_RE.findall(output.reply)]
        bad_quantities = [str(q) for q in quantities if q not in ctx.deps.seen_quantities and q not in said]
        if problems := reply_problems(output.reply, ctx.deps.customer.email if ctx.deps.customer else None):
            raise ModelRetry("Rewrite your reply: " + "; ".join(problems) + ".")
        if bad_prices or bad_quantities:
            raise ModelRetry(
                f"Your reply quotes {', '.join(bad_prices + bad_quantities)}, but no tool returned that number in this "
                "turn. Look it up with get_product_details / check_stock / search_products and use the exact value, "
                "or leave the number out. Never invent prices or quantities."
            )
        return output

    return agent


def to_history(turns: list[ChatTurn]) -> list[ModelMessage]:
    """Replay earlier chat turns (sent by the browser) as PydanticAI message history."""
    history: list[ModelMessage] = []
    for t in turns:
        if t.role == "user":
            history.append(ModelRequest(parts=[UserPromptPart(content=t.content)]))
        else:
            history.append(ModelResponse(parts=[TextPart(content=t.content)]))
    return history


def is_content_filtered(exc: ModelHTTPError) -> bool:
    text = str(exc.body).lower()
    return exc.status_code == 400 and ("content management policy" in text or "content_filter" in text)


def _usage(run) -> tuple[int | None, int | None]:
    try:
        u = run.usage() if callable(run.usage) else run.usage
        return u.requests, u.total_tokens
    except Exception:
        return None, None


async def run_chat(
    message: str,
    history: list[ChatTurn],
    customer: Customer | None = None,
    page: PageContext | None = None,
    audit: AuditTrail | None = None,
) -> ChatResponse:
    """Run the agent loop step by step, writing every step to the append-only audit trail."""
    audit = audit or AuditTrail("guest" if customer is None else f"customer #{customer.id}")
    shopper_text = " ".join([*(t.content for t in history if t.role == "user"), message])
    deps = ShopDeps(customer=customer, page=page, shopper_text=shopper_text)
    response: ChatResponse | None = None
    stop_reason = "error"
    run = None
    try:
        async with build_agent().iter(
            message, message_history=to_history(history), deps=deps,
            usage_limits=UsageLimits(request_limit=REQUEST_LIMIT),
        ) as run:
            calls = 0
            async for node in run:
                if Agent.is_model_request_node(node):
                    for part in node.request.parts:
                        if isinstance(part, ToolReturnPart) and part.tool_name != OUTPUT_TOOL:
                            await audit.log("tool_result", tool=part.tool_name, result=short(part.content))
                        elif isinstance(part, RetryPromptPart):  # e.g. the output check rejected a reply
                            await audit.log("retry", tool=part.tool_name, detail=short(part.content))
                    calls += 1
                    await audit.log("model_request", detail=f"model call {calls} of max {REQUEST_LIMIT}")
                elif Agent.is_call_tools_node(node):
                    for part in node.model_response.parts:
                        if isinstance(part, ToolCallPart) and part.tool_name == OUTPUT_TOOL:
                            await audit.log("final_output", result=short(part.args_as_dict()))
                        elif isinstance(part, ToolCallPart):
                            await audit.log("tool_call", tool=part.tool_name, args=short(part.args_as_dict(), 200))
                        elif isinstance(part, TextPart) and part.content.strip():
                            await audit.log("thought", detail=short(part.content, 200))
            out = run.result.output
        # Card and page lookups run concurrently, off the event loop.
        cards, page_update = await asyncio.gather(
            asyncio.to_thread(product_cards, out.product_ids),
            asyncio.to_thread(page_results, out.show_on_page) if out.show_on_page else asyncio.sleep(0, None),
        )
        response = ChatResponse(reply=out.reply, products=cards, page=page_update)
        stop_reason = "final_output"
        return response
    except ModelHTTPError as exc:
        if is_content_filtered(exc):
            stop_reason, response = "content_filter", ChatResponse(reply=FILTERED_REPLY)
            return response
        stop_reason = f"error: model HTTP {exc.status_code}"
        raise
    except UnexpectedModelBehavior:  # output check kept failing: never show unverified numbers or unsafe text
        stop_reason, response = "output_check_failed", ChatResponse(reply=UNVERIFIED_REPLY)
        return response
    except UsageLimitExceeded:  # loop hit REQUEST_LIMIT model calls
        stop_reason, response = "usage_limit", ChatResponse(reply=LIMIT_REPLY)
        return response
    except Exception as exc:
        stop_reason = f"error: {type(exc).__name__}"
        raise
    finally:
        requests, tokens = _usage(run) if run is not None else (None, None)
        await audit.log(
            "run_end", stop_reason=stop_reason, model_requests=requests, total_tokens=tokens,
            result=short(response.reply) if response else None,
            detail=(f"cards: {[p.product_id for p in response.products]}"
                    + (f"; page: {response.page.title} ({response.page.total})" if response.page else ""))
            if response else None,
        )
