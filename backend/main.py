"""Campus Customs API: products, stock, images, accounts and the shopping chatbot.

Run from the backend/ folder (with the hw4 virtualenv):
    cd backend
    ../.venv/bin/uvicorn main:app --reload --port 8000

Product routes are read-only (catalog.py); account routes live in auth.py; the chatbot is the
PydanticAI agent in agent.py (prompt: prompts/prompt.md, tools: tools.py, types: models.py).
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict

from fastapi import Cookie, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent import MissingAPIKey, run_chat
from audit import AuditTrail, short
from auth import UserOut, current_user, init_auth_tables, router as auth_router
from catalog import (
    COLOR_FAMILIES,
    DATA_DIR,
    PRICE_BANDS,
    PRICE_LABELS,
    SHOP_FOR_LABELS,
    SIZE_ORDER,
    all_products,
    category_for,
    filter_products,
    going_fast,
    price_band,
    product_detail,
    search_text,
    summary,
)
from chat_history import clear_history, init_chat_tables, load_history, model_history, save_exchange
from models import ChatHistory, ChatRequest, ChatResponse, ChatTurn, Customer
from privacy import RateLimiter, redact_sensitive

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
    allow_credentials=True,  # session cookie
)
app.include_router(auth_router)
init_auth_tables()
init_chat_tables()
# Product photos: /images/<file>.jpg -> data/products/<file>.jpg
app.mount("/images", StaticFiles(directory=DATA_DIR / "products"), name="images")


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ProductSummary(BaseModel):
    product_id: str
    name: str
    category: str
    product_types: list[str]
    garment_type: str
    price: float
    short_description: str
    colors: list[str]
    color_families: list[str]
    shop_for: list[str]
    sizes_in_stock: list[str]
    image_url: str
    total_stock: int


class FilterOption(BaseModel):
    value: str
    label: str
    count: int
    group: str | None = None
    swatch: str | None = None


class Filters(BaseModel):
    shop_for: list[FilterOption]
    product_type: list[FilterOption]
    color: list[FilterOption]
    size: list[FilterOption]
    price: list[FilterOption]


class LowSize(BaseModel):
    size: str
    quantity: int


class GoingFastItem(ProductSummary):
    units_left: int
    sold_out_sizes: list[str]
    low_sizes: list[LowSize]


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductDetail(ProductSummary):
    description: str
    search_tags: list[str]
    inventory: list[SizeStock]


class Category(BaseModel):
    category: str
    count: int


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/products", response_model=list[ProductSummary])
def list_products(
    q: str | None = Query(None, description="Search name, description, colors and tags."),
    category: str | None = Query(None, description="Product type(s) from /api/categories, comma-separated."),
    shop_for: str | None = Query(None, description="Audience ids from /api/filters (women, men, unisex, family-mom, …), comma-separated."),
    color: str | None = Query(None, description="Color families from /api/filters (Navy, Gray, …), comma-separated."),
    size: str | None = Query(None, description="Sizes that must be in stock (XS–XXL), comma-separated."),
    price: str | None = Query(None, description="Price bands (under-40, 40-60, 60-80, 80-plus), comma-separated."),
    ids: str | None = Query(None, description="Comma-separated product_ids, returned in that order (chat search results page)."),
) -> list[dict]:
    rows = all_products()
    products = [summary(r, r["total_stock"]) for r in rows]
    if ids:
        by_id = {p["product_id"]: p for p in products}
        products = [by_id[i] for i in dict.fromkeys(ids.split(",")) if i in by_id]
    products = filter_products(products, _split(shop_for), _split(category), _split(color), _split(size), _split(price))
    products = search_text(products, rows, q)
    return products


@app.get("/api/categories", response_model=list[Category])
def list_categories() -> list[dict]:
    types = [r["garment_type"] for r in all_products()]
    counts: dict[str, int] = {}
    for t in types:
        counts[category_for(t)] = counts.get(category_for(t), 0) + 1
    return [{"category": c, "count": n} for c, n in sorted(counts.items())]


SWATCHES = {
    "Navy": "#0b2a5b", "White": "#ffffff", "Gray": "#9aa3ad", "Blue": "#3d7bff", "Red": "#d62839",
    "Black": "#111111", "Yellow & Gold": "#f2c230", "Green": "#2e8b57", "Cream": "#f3ead7", "Coral": "#f08a7e",
    "Multicolor": "conic-gradient(#d62839, #f2c230, #2e8b57, #3d7bff, #d62839)",
}


def _split(value: str | None) -> list[str] | None:
    return [x.strip() for x in value.split(",") if x.strip()] if value else None


@app.get("/api/filters", response_model=Filters)
def list_filters(
    q: str | None = None,
    shop_for: str | None = None,
    category: str | None = None,
    color: str | None = None,
    size: str | None = None,
    price: str | None = None,
) -> dict:
    """Every filter option with how many products it would show, given the current search and the
    OTHER filters (standard faceted counts), so an option never promises results it can't deliver."""
    rows = all_products()
    base = search_text([summary(r, r["total_stock"]) for r in rows], rows, q)
    chosen = {"shop_for": _split(shop_for), "category": _split(category), "color": _split(color),
              "size": _split(size), "price": _split(price)}

    def pool(skip: str) -> list[dict]:
        args = {k: (None if k == skip else v) for k, v in chosen.items()}
        return filter_products(base, args["shop_for"], args["category"], args["color"], args["size"], args["price"])

    pools = {k: pool(k) for k in chosen}

    def count(pred, facet: str) -> int:
        return sum(1 for p in pools[facet] if pred(p))

    family = [k for k in SHOP_FOR_LABELS if k.startswith("family-")]
    shop = [
        {"value": k, "label": SHOP_FOR_LABELS[k], "count": count(lambda p, k=k: k in p["shop_for"], "shop_for"),
         "group": "Family" if k in family else None}
        for k in ["women", "men", "unisex", *family]
    ]
    types = sorted({t for p in base for t in p["product_types"]} | {category_for(r["garment_type"]) for r in rows})
    return {
        "shop_for": shop,
        "product_type": [{"value": t, "label": t, "count": count(lambda p, t=t: t in p["product_types"], "category")} for t in types],
        "color": [
            {"value": f, "label": f, "count": count(lambda p, f=f: f in p["color_families"], "color"), "swatch": SWATCHES[f]}
            for f in COLOR_FAMILIES
        ],
        "size": [{"value": z, "label": z, "count": count(lambda p, z=z: z in p["sizes_in_stock"], "size")} for z in SIZE_ORDER],
        "price": [
            {"value": b, "label": PRICE_LABELS[b], "count": count(lambda p, b=b: price_band(p["price"]) == b, "price")}
            for b in PRICE_BANDS
        ],
    }


@app.get("/api/going-fast", response_model=list[GoingFastItem])
def list_going_fast() -> list[dict]:
    """Most popular right now = closest to selling out (fewest units left across all sizes)."""
    return going_fast()


@app.get("/api/products/{product_id}", response_model=ProductDetail)
def get_product(product_id: str) -> dict:
    detail = product_detail(product_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return detail


# ---------------------------------------------------------------------------
# Chatbot
# ---------------------------------------------------------------------------


def as_customer(user: UserOut) -> Customer:
    """The fields the agent may see about the logged-in shopper: name and email only."""
    return Customer(id=user.id, first_name=user.first_name, last_name=user.last_name, email=user.email)


# One lock per logged-in customer: if they send messages from two tabs at once, the agent runs are queued so
# each one sees the previous saved exchange (and history is saved in order). Different customers and guests
# never share a lock, so their agent runs proceed concurrently.
_customer_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
_chat_limit = RateLimiter(max_requests=12, per_seconds=60)  # per customer, or per IP for guests

PRIVACY_NOTICE = (
    "For your safety, we removed the {kinds} from your message before it was processed or saved. "
    "Please don't share personal or payment details in chat."
)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, request: Request, cc_session: str | None = Cookie(default=None)) -> ChatResponse:
    """One shopper message in, one agent reply (plus product cards and an optional page update) out.

    Logged in: history comes from the database and the exchange is saved. Guest: the browser sends
    the history and nothing is saved. Either way `page` says what the shopper is looking at."""
    # Database work runs in worker threads (asyncio.to_thread) so it never blocks other chats on the event loop.
    user = await asyncio.to_thread(current_user, cc_session)
    audit = AuditTrail("guest" if user is None else f"customer #{user.id}")  # never names or emails
    key = f"user:{user.id}" if user else f"ip:{request.client.host if request.client else 'unknown'}"
    if not _chat_limit.allow(key):
        await audit.log("request_rejected", detail="rate limit: more than 12 messages in 60 s")
        await audit.log("run_end", stop_reason="rate_limited")
        raise HTTPException(429, "You're sending messages very quickly. Please wait a moment and try again.")

    # Privacy: strip card numbers, phone numbers, addresses, etc. before the model, the database or the audit trail see them.
    own_email = user.email if user else None
    message, removed = redact_sensitive(body.message, own_email)
    body = body.model_copy(update={"message": message})
    notice = PRIVACY_NOTICE.format(kinds=", ".join(removed)) if removed else None
    await audit.log(
        "run_start", detail=short(message, 200),
        args=f"page: {body.page.path if body.page else 'unknown'}; history: {'database' if user else len(body.history)}",
    )
    if removed:
        await audit.log("privacy_redaction", detail=f"removed before processing: {', '.join(removed)}")

    if user is None:
        history = [ChatTurn(role=t.role, content=redact_sensitive(t.content)[0]) for t in body.history]
        reply = await _answer(body, None, history, audit)
        return reply.model_copy(update={"privacy_notice": notice})
    async with _customer_locks[user.id]:
        history = await asyncio.to_thread(model_history, user.id)
        reply = await _answer(body, as_customer(user), history, audit)
        await asyncio.to_thread(save_exchange, user.id, message, reply)
        return reply.model_copy(update={"privacy_notice": notice})


async def _answer(body: ChatRequest, customer: Customer | None, history, audit: AuditTrail) -> ChatResponse:
    try:
        return await run_chat(body.message, history, customer, body.page, audit)
    except MissingAPIKey:
        raise HTTPException(503, "The shop assistant isn't configured yet (missing API key).")
    except Exception:
        log.exception("chat failed")
        raise HTTPException(502, "The shop assistant hit a snag. Please try again in a moment.")


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    """The logged-in customer's saved chat (guests get an empty list)."""
    user = current_user(cc_session)
    return ChatHistory(logged_in=bool(user), messages=load_history(user.id) if user else [])


@app.delete("/api/chat/history", status_code=204)
def delete_chat_history(cc_session: str | None = Cookie(default=None)) -> None:
    user = current_user(cc_session)
    if not user:
        raise HTTPException(401, "Log in to manage your chat history.")
    clear_history(user.id)
