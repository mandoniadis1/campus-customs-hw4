"""Tools the Campus Customs agent can call. All of them are read-only lookups in campus_customs.db.

- search_products      — find products by words, category, color, budget and size in stock
- get_product_details  — full description, price, colors and exact stock for every size of one product
- check_stock          — is one product available in one size? (exact quantity + other sizes to offer)
- list_categories      — what the shop sells, with counts and price ranges

All tools are async: their SQLite reads run in worker threads (asyncio.to_thread), so parallel tool calls
and other shoppers' chats never wait on each other's database work.
Every price and quantity a tool returns is also recorded in ShopDeps, so agent.py can reject a reply
that quotes a number no tool returned (see no_invented_numbers).
product_cards() turns the product_ids the agent picked into cards for the chat panel, and
page_results() re-runs the agent's search for the products page (chat search that updates the page).
"""

from __future__ import annotations

import asyncio
import json
import re
from contextlib import closing
from dataclasses import dataclass, field

from pydantic_ai import RunContext

from privacy import clean_label

from catalog import SIZE_ORDER, all_products, category_for, product_types, connect, product_detail, short_description, stock_by_size
from models import (
    CategoryInfo,
    Customer,
    PageContext,
    NotFound,
    PageSearch,
    PageUpdate,
    ProductCard,
    ProductInfo,
    ProductMatch,
    SearchResults,
    SizeStock,
    StockCheck,
    StockStatus,
)

MAX_RESULTS = 8
LOW_STOCK = 3  # 1-3 units left counts as low stock
STOPWORDS = {"a", "an", "and", "the", "for", "with", "in", "of", "on", "to", "do", "you", "have", "any", "some", "me", "i", "my", "u", "got", "what", "is", "are", "something", "show"}

# Shopper words → catalogue category, so "sweatshirt" or "zip-up" finds the right section.
CATEGORY_WORDS = {
    "hoodie": "Hoodies", "hoodies": "Hoodies", "hoody": "Hoodies",
    "tee": "T-Shirts", "tees": "T-Shirts", "t-shirt": "T-Shirts", "tshirt": "T-Shirts", "shirt": "T-Shirts", "shirts": "T-Shirts",
    "crewneck": "Crewnecks", "crewnecks": "Crewnecks", "sweatshirt": "Crewnecks", "sweatshirts": "Crewnecks", "mockneck": "Crewnecks",
    "long-sleeve": "Long Sleeves", "longsleeve": "Long Sleeves",
    "quarter-zip": "Quarter-Zips", "1/4": "Quarter-Zips", "zip": "Quarter-Zips",
    "jacket": "Jackets & Fleece", "jackets": "Jackets & Fleece", "fleece": "Jackets & Fleece", "fleeces": "Jackets & Fleece",
}

# How shoppers say sizes → the size codes used in the inventory table.
SIZE_WORDS = {
    "xs": "XS", "extra small": "XS", "x-small": "XS", "xsmall": "XS",
    "s": "S", "small": "S", "sm": "S",
    "m": "M", "medium": "M", "med": "M",
    "l": "L", "large": "L", "lg": "L",
    "xl": "XL", "extra large": "XL", "x-large": "XL", "xlarge": "XL",
    "xxl": "XXL", "2xl": "XXL", "xx-large": "XXL", "extra extra large": "XXL", "2x": "XXL",
}


@dataclass
class ShopDeps:
    """Per-request context for the agent: who is chatting, what page they're on, and every number
    the tools returned during this request."""

    customer: Customer | None = None  # None = guest
    page: PageContext | None = None
    shopper_text: str = ""  # this message + earlier shopper turns (numbers the shopper said, e.g. a budget)
    seen_prices: set[float] = field(default_factory=set)
    seen_quantities: set[int] = field(default_factory=set)


def normalize_size(size: str) -> str | None:
    s = re.sub(r"\s+", " ", size.strip().lower())
    return SIZE_WORDS.get(s) or (s.upper() if s.upper() in SIZE_ORDER else None)


def _status(quantity: int) -> StockStatus:
    if quantity <= 0:
        return "out_of_stock"
    return "low_stock" if quantity <= LOW_STOCK else "in_stock"


def _split_sizes(sizes: list[dict]) -> tuple[list[str], list[str]]:
    return [s["size"] for s in sizes if s["quantity"] > 0], [s["size"] for s in sizes if s["quantity"] <= 0]


def _resolve(product_id_or_name: str) -> dict | None:
    """Look a product up by id, falling back to its exact name (case-insensitive)."""
    detail = product_detail(product_id_or_name.strip())
    if detail is None:
        wanted = product_id_or_name.strip().lower()
        match = next((r for r in all_products() if r["name"].lower() == wanted), None)
        detail = product_detail(match["product_id"]) if match else None
    return detail


def _not_found(what: str) -> NotFound:
    return NotFound(
        error=f"No product matches {what!r}.",
        suggestion="Call search_products to find the right product_id, then try again.",
    )


def find_products(
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
    limit: int = MAX_RESULTS,
) -> SearchResults:
    """The catalogue search used by both the search_products tool and the results page (page_results)."""
    rows = all_products()
    with closing(connect()) as conn:
        stock = stock_by_size(conn, [r["product_id"] for r in rows])

    words = [w for w in query.lower().replace(",", " ").split() if w not in STOPWORDS]
    if not category:
        category = next((CATEGORY_WORDS[w] for w in words if w in CATEGORY_WORDS), None)
    words = [w for w in words if w not in CATEGORY_WORDS]
    size_code = normalize_size(size) if size else None

    scored: list[tuple[int, ProductMatch]] = []
    for r in rows:
        if category and category.lower() not in [t.lower() for t in product_types(r["garment_type"], r["description"], json.loads(r["search_tags"]))]:
            continue
        if max_price is not None and r["price"] > max_price:
            continue
        colors = json.loads(r["colors"])
        if color and not any(color.lower() in c.lower() for c in colors):
            continue
        in_stock, out_of_stock = _split_sizes(stock[r["product_id"]])
        size_ok = (size_code in in_stock) if size_code else None
        name = r["name"].lower()
        text = " ".join([r["name"], r["description"], r["colors"], r["search_tags"]]).lower()
        hits = sum(1 for w in words if w in text)
        if words and hits == 0:
            continue
        score = hits * 2 + sum(1 for w in words if w in name) + (3 if size_ok else 0)
        scored.append(
            (
                score,
                ProductMatch(
                    product_id=r["product_id"], name=r["name"], category=category_for(r["garment_type"]),
                    price=r["price"], colors=colors, sizes_in_stock=in_stock, sizes_out_of_stock=out_of_stock,
                    requested_size_in_stock=size_ok, short_description=short_description(r["description"]),
                ),
            )
        )
    scored.sort(key=lambda s: (-s[0], s[1].price))
    products = [p for _, p in scored[:limit]]

    note = None
    if not products:
        note = "Nothing matched. Try fewer words, drop the color/budget filter, or search by category alone."
    elif size and not size_code:
        note = f"Size {size!r} wasn't recognised (use XS, S, M, L, XL or XXL), so it was ignored."
    elif size_code:
        sold_out = [p.name for p in products if p.requested_size_in_stock is False]
        if sold_out:
            note = f"OUT OF STOCK in {size_code}: {'; '.join(sold_out)}. Tell the shopper clearly before suggesting alternatives."
    in_size = sum(1 for _, p in scored if p.requested_size_in_stock) if size_code else None
    return SearchResults(total_matches=len(scored), matches_in_requested_size=in_size, products=products, note=note)


async def search_products(
    ctx: RunContext[ShopDeps],
    query: str = "",
    category: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue. Returns up to 8 matching products (best match first)
    with their price and which sizes are in or out of stock. total_matches says how many matched overall.

    Args:
        query: Free-text words to match against name, description, colors and tags (e.g. "handsome dan", "bulldog", "harvard").
        category: Optional shop category: Hoodies, T-Shirts, Crewnecks, Long Sleeves, Quarter-Zips, Jackets & Fleece.
        color: Optional color the product must come in (e.g. "pink", "navy", "gray").
        max_price: Optional budget — only products at or under this price in USD.
        size: Optional size the shopper wants (XS, S, M, L, XL, XXL; "medium" etc. also work). Products in stock
            in that size are listed first; matching products that are OUT of stock in it are still returned with
            requested_size_in_stock=false so you can tell the shopper.
    """
    results = await asyncio.to_thread(find_products, query, category, color, max_price, size)
    ctx.deps.seen_prices.update(p.price for p in results.products)
    return results


async def get_product_details(ctx: RunContext[ShopDeps], product_id: str) -> ProductInfo | NotFound:
    """Full details for one product: description, price, colors, tags and the EXACT stock count for
    every size (XS-XXL). Use it before describing a product, quoting its price, or saying how many are left.

    Args:
        product_id: The product_id from search_products (an exact product name also works).
    """
    d = await asyncio.to_thread(_resolve, product_id)
    if d is None:
        return _not_found(product_id)
    stock = [SizeStock(size=s["size"], quantity=s["quantity"], status=_status(s["quantity"])) for s in d["inventory"]]
    in_stock, out_of_stock = _split_sizes(d["inventory"])
    ctx.deps.seen_prices.add(d["price"])
    ctx.deps.seen_quantities.update(s.quantity for s in stock)
    ctx.deps.seen_quantities.add(d["total_stock"])
    return ProductInfo(
        product_id=d["product_id"], name=d["name"], category=d["category"], garment_type=d["garment_type"],
        price=d["price"], description=d["description"], colors=d["colors"], search_tags=d["search_tags"],
        stock=stock, sizes_in_stock=in_stock, sizes_out_of_stock=out_of_stock, total_in_stock=d["total_stock"],
    )


async def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str) -> StockCheck | NotFound:
    """Check whether one product is available in one size, with the exact quantity.
    If the size is out of stock, the result says so and lists the sizes that ARE available.

    Args:
        product_id: The product_id from search_products (an exact product name also works).
        size: The size to check: XS, S, M, L, XL or XXL (words like "medium" or "extra large" also work).
    """
    d = await asyncio.to_thread(_resolve, product_id)
    if d is None:
        return _not_found(product_id)
    code = normalize_size(size)
    if code is None:
        return NotFound(error=f"{size!r} isn't a size we stock.", suggestion="Sizes are XS, S, M, L, XL and XXL.")
    quantity = next((s["quantity"] for s in d["inventory"] if s["size"] == code), 0)
    status = _status(quantity)
    others = [s["size"] for s in d["inventory"] if s["quantity"] > 0 and s["size"] != code]
    ctx.deps.seen_quantities.add(quantity)
    if status == "out_of_stock":
        message = f"Size {code} of {d['name']} is OUT OF STOCK (0 left)."
    elif status == "low_stock":
        message = f"Size {code} of {d['name']} is in stock, but only {quantity} left."
    else:
        message = f"Size {code} of {d['name']} is in stock ({quantity} available)."
    return StockCheck(
        product_id=d["product_id"], name=d["name"], size=code, quantity=quantity, status=status,
        in_stock=quantity > 0, other_sizes_in_stock=others, message=message,
    )


async def list_categories(ctx: RunContext[ShopDeps]) -> list[CategoryInfo]:
    """What Campus Customs sells: each category with its number of products and price range (USD)."""
    groups: dict[str, list[float]] = {}
    for r in await asyncio.to_thread(all_products):
        groups.setdefault(category_for(r["garment_type"]), []).append(r["price"])
    result = [
        CategoryInfo(category=c, products=len(p), min_price=min(p), max_price=max(p)) for c, p in sorted(groups.items())
    ]
    ctx.deps.seen_prices.update(x for c in result for x in (c.min_price, c.max_price))
    return result


SHOP_TOOLS = [search_products, get_product_details, check_stock, list_categories]


PAGE_NAMES = {"/": "home", "/about": "About Us", "/login": "Log In", "/create-account": "Create Account", "/products": "Products"}


def describe_page(page: PageContext | None, deps: ShopDeps) -> str:
    """Turn the page the shopper is on into plain instructions, resolving product ids from the database,
    so "it" / "this one" / "the first one" mean something. Prices shown here count as looked up."""
    if page is None:
        return "You don't know which page the shopper is on."
    if page.product_id:
        d = product_detail(page.product_id)
        if d:
            in_stock, out_of_stock = _split_sizes(d["inventory"])
            deps.seen_prices.add(d["price"])
            lines = [
                f"The shopper is on the product page for **{d['name']}** (product_id {d['product_id']}): "
                f"{d['garment_type']}, ${d['price']:g}, colors: {', '.join(d['colors'])}.",
                f"Sizes in stock: {', '.join(in_stock) or 'none'}. Out of stock: {', '.join(out_of_stock) or 'none'}.",
            ]
            size = normalize_size(page.selected_size) if page.selected_size else None
            if size:
                lines.append(f"They have size {size} selected on the page.")
            lines.append(
                'When they say "it", "this", "this one", "that" or name the garment type (e.g. "this hoodie"), '
                "they mean this product unless they clearly mean something else."
            )
            return " ".join(lines)
    if page.listing_product_ids:
        names = []
        for i, pid in enumerate(page.listing_product_ids[:6], start=1):
            d = product_detail(pid)
            if d:
                names.append(f"{i}. {d['name']} ({pid})")
        title = clean_label(page.listing_title) or "Products"  # comes from the URL: treat as untrusted text
        return (
            f'The shopper is looking at a product list titled "{title}". In order, it starts with: '
            + "; ".join(names)
            + '. "The first one", "the second one" etc. refer to this order.'
        )
    name = PAGE_NAMES.get(page.path.rstrip("/") or "/")
    return f"The shopper is on the {name} page." if name else "The shopper is on another page of the site."


PAGE_LIMIT = 48  # more than any one category holds, so "show me all hoodies" shows them all


def page_results(search: PageSearch) -> PageUpdate | None:
    """Re-run the agent's search for the products page. Returns None if it finds nothing,
    so the page is never replaced with an empty result."""
    results = find_products(search.query, search.category, search.color, search.max_price, search.size, PAGE_LIMIT)
    products = results.products
    if search.size and normalize_size(search.size):  # the page shows only what can actually be bought in that size
        products = [p for p in products if p.requested_size_in_stock]
    if not products:
        return None
    return PageUpdate(
        title=search.title.strip()[:80] or "Results",
        product_ids=[p.product_id for p in products],
        total=len(products),
        search=search,
    )


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Build chat cards from the database (never from model text), skipping unknown ids and duplicates."""
    cards: list[ProductCard] = []
    for pid in dict.fromkeys(product_ids):
        d = product_detail(pid)
        if d is None:
            continue
        in_stock, out_of_stock = _split_sizes(d["inventory"])
        cards.append(
            ProductCard(
                product_id=d["product_id"], name=d["name"], category=d["category"], price=d["price"],
                image_url=d["image_url"], colors=d["colors"], sizes_in_stock=in_stock,
                sizes_out_of_stock=out_of_stock, short_description=d["short_description"],
            )
        )
    return cards
