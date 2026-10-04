"""Structured types for the Campus Customs chatbot.

- ShopReply   — what the PydanticAI agent must return (its output_type)
- ProductCard — a product shown under a chat reply, always built from the database
- ChatRequest / ChatResponse — the /api/chat request and response bodies
- PageSearch / PageUpdate — chat search that updates the page (agent asks; API returns the results to show)
- Customer, PageContext, ChatHistory — customer memory: who is chatting, what page they're on, saved chats
- Tool return types (SearchResults, ProductInfo, StockCheck, CategoryInfo, NotFound) — what the
  agent's lookup tools hand back to the model
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PageSearch(BaseModel):
    """The agent's request to open the shop page with a search's results (Problem 7).
    The backend re-runs this exact search, so the page always matches the catalogue."""

    title: str = Field(description='Short heading for the results page, e.g. "Hoodies", "Pink tees under $40", "Bulldog gear in XS".')
    query: str = Field(default="", description="Same free-text words you used in search_products (can be empty).")
    category: str | None = Field(default=None, description="Same category filter you used, if any.")
    color: str | None = Field(default=None, description="Same color filter you used, if any.")
    max_price: float | None = Field(default=None, description="Same budget filter you used, if any.")
    size: str | None = Field(default=None, description="Same size filter you used, if any (page then shows only items in stock in it).")


class ShopReply(BaseModel):
    """The agent's answer to the shopper."""

    reply: str = Field(description="The message to show the shopper: friendly, concise, plain text (short lists are fine).")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="product_ids (from tool results only) of up to 4 products to show as cards under the reply, best match first.",
    )
    show_on_page: PageSearch | None = Field(
        default=None,
        description="Set when the shopper is looking for an item or type of item: opens the shop page showing every match.",
    )


class ProductCard(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    image_url: str
    colors: list[str]
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str] = Field(default_factory=list)
    short_description: str


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1000)
    history: list[ChatTurn] = Field(
        default_factory=list, max_length=20,
        description="Guests only: earlier turns, oldest first. Logged-in shoppers' history is loaded from the database instead.",
    )
    page: PageContext | None = Field(default=None, description="What the shopper is looking at right now.")


class PageUpdate(BaseModel):
    """Tells the website to open the products page with these results (part of ChatResponse)."""

    title: str
    product_ids: list[str] = Field(description="Matching products in ranked order (max 48).")
    total: int = Field(description="How many products matched in total.")
    search: PageSearch = Field(description="The search that produced these results.")


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)
    page: PageUpdate | None = Field(default=None, description="Present when the page should show search results.")
    privacy_notice: str | None = Field(
        default=None, description="Set when sensitive data was removed from the shopper's message before processing."
    )


# ---------------------------------------------------------------------------
# Tool return types (Problem 6). Every number in these comes straight from campus_customs.db.
# ---------------------------------------------------------------------------

StockStatus = Literal["in_stock", "low_stock", "out_of_stock"]


class SizeStock(BaseModel):
    """Stock for one size of one product."""

    size: str = Field(description="XS, S, M, L, XL or XXL.")
    quantity: int = Field(description="Exact units in stock right now. 0 means out of stock.")
    status: StockStatus = Field(description="in_stock, low_stock (1-3 left) or out_of_stock (0).")


class ProductMatch(BaseModel):
    """One search hit: enough to compare products and pick which to look up in detail."""

    product_id: str
    name: str
    category: str
    price: float = Field(description="Price in USD from the catalogue.")
    colors: list[str]
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str]
    requested_size_in_stock: bool | None = Field(
        default=None, description="Only set when the search asked for a size: is THAT size in stock for this product?"
    )
    short_description: str


class SearchResults(BaseModel):
    total_matches: int = Field(description="How many products matched before the result limit.")
    matches_in_requested_size: int | None = Field(
        default=None, description="Only set when a size was asked for: how many matches are in stock in THAT size (this is what the page shows)."
    )
    products: list[ProductMatch]
    note: str | None = Field(default=None, description="Hints, e.g. when filters were relaxed or nothing matched.")


class ProductInfo(BaseModel):
    """Everything the shop knows about one product."""

    product_id: str
    name: str
    category: str
    garment_type: str
    price: float = Field(description="Price in USD from the catalogue. Quote exactly.")
    description: str = Field(description="Full product description from the catalogue.")
    colors: list[str]
    search_tags: list[str]
    stock: list[SizeStock] = Field(description="Every size, XS to XXL, with its exact quantity.")
    sizes_in_stock: list[str]
    sizes_out_of_stock: list[str]
    total_in_stock: int


class StockCheck(BaseModel):
    """Answer to "is product X available in size Y?"."""

    product_id: str
    name: str
    size: str
    quantity: int = Field(description="Exact units in stock for this size.")
    status: StockStatus
    in_stock: bool
    other_sizes_in_stock: list[str] = Field(description="Sizes of the same product that are available, to suggest instead.")
    message: str = Field(description="A plain statement of the result, e.g. 'Size XS is OUT OF STOCK'.")


class CategoryInfo(BaseModel):
    category: str
    products: int
    min_price: float
    max_price: float


class NotFound(BaseModel):
    """Returned instead of a result when a product or size can't be found."""

    error: str
    suggestion: str


# ---------------------------------------------------------------------------
# Customer memory + page context (Problem 8)
# ---------------------------------------------------------------------------


class Customer(BaseModel):
    """The logged-in shopper, as the agent sees them: name and email only (Problem 9 privacy rule).
    `id` stays in code (saving history) and is never written into the prompt."""

    id: int
    first_name: str
    last_name: str
    email: str


class PageContext(BaseModel):
    """What the shopper is looking at when they send a chat message. Sent by the website with every message."""

    path: str = Field(default="/", max_length=300, description='The page URL path, e.g. "/products/basic-hoodie-big-yale".')
    product_id: str | None = Field(default=None, max_length=120, description="Set on a single-product page.")
    selected_size: str | None = Field(default=None, max_length=10, description="The size button picked on that page, if any.")
    listing_title: str | None = Field(default=None, max_length=120, description='Heading of a product list, e.g. "Hoodies".')
    listing_product_ids: list[str] = Field(default_factory=list, max_length=12, description="First products shown in that list, in order.")


class ChatHistoryMessage(BaseModel):
    """One saved message, as reloaded into the chat panel."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)
    page: PageUpdate | None = None
    created_at: str


class ChatHistory(BaseModel):
    logged_in: bool
    messages: list[ChatHistoryMessage] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Audit trail (Problem 12): one record per step of an agent run, appended to output/audit_trail.json
# ---------------------------------------------------------------------------

AuditEvent = Literal[
    "run_start", "request_rejected", "privacy_redaction", "model_request", "retry", "thought",
    "tool_call", "tool_result", "final_output", "run_end",
]


class AuditEntry(BaseModel):
    """One step of agent-loop activity. Short summaries only, never full prompts or personal data."""

    run_id: str = Field(description="Groups every step of one shopper message.")
    step: int = Field(description="Order of the step within the run (1, 2, 3…).")
    timestamp: str = Field(description="UTC time, ISO 8601 with milliseconds.")
    elapsed_s: float = Field(description="Seconds since the run started.")
    event: AuditEvent
    shopper: str | None = Field(default=None, description='"guest" or "customer #<id>" (no names or emails).')
    tool: str | None = Field(default=None, description="Tool name for tool_call / tool_result.")
    args: str | None = Field(default=None, description="Short tool arguments (≤ 200 chars).")
    result: str | None = Field(default=None, description="Short tool result / reply summary (≤ 300 chars).")
    detail: str | None = Field(default=None, description="Message preview, retry reason, removed data kinds, etc.")
    stop_reason: str | None = Field(
        default=None,
        description="run_end only: final_output, content_filter, unverified_numbers, usage_limit, rate_limited or error.",
    )
    model_requests: int | None = None
    total_tokens: int | None = None
