"""Read-only access to the shop catalogue in data/campus_customs.db.

Shared by the product API routes (main.py) and the chatbot's tools (tools.py), so the website
and the agent always describe products, prices and stock the same way.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import closing
from pathlib import Path

HW4 = Path(__file__).resolve().parent.parent
DATA_DIR = HW4 / "data"
# CAMPUS_CUSTOMS_DB can point at a copy of the database (used for tests, so they never touch real data).
DB_PATH = Path(os.getenv("CAMPUS_CUSTOMS_DB", DATA_DIR / "campus_customs.db"))
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]

# The catalogue has 22 color spellings; group them into the swatches shoppers filter by.
COLOR_FAMILIES = {
    "Navy": ["navy blue", "navy"],
    "White": ["white"],
    "Gray": ["heather gray", "gray", "charcoal gray", "dark heather gray", "light gray", "dark heather charcoal", "heather charcoal gray"],
    "Blue": ["blue", "light blue", "royal blue"],
    "Red": ["red"],
    "Black": ["black"],
    "Yellow & Gold": ["yellow", "gold"],
    "Green": ["green"],
    "Cream": ["cream", "ivory"],
    "Coral": ["dusty coral"],
    "Multicolor": ["multicolor"],
}
_COLOR_TO_FAMILY = {c: fam for fam, colors in COLOR_FAMILIES.items() for c in colors}

# "Shop For": the catalogue has no gender column, so audiences come from explicit labels only:
# "men's"/"mens" in the name/tags/type, and family gift names like "Yale Mom Hoodie".
FAMILY = {
    "mom": ("family-mom", "women"), "grandma": ("family-grandparents", "women"), "aunt": ("family-aunt-uncle", "women"),
    "sister": ("family-siblings", "women"), "dad": ("family-dad", "men"), "grandpa": ("family-grandparents", "men"),
    "uncle": ("family-aunt-uncle", "men"), "brother": ("family-siblings", "men"),
}
SHOP_FOR_LABELS = {
    "women": "Women", "men": "Men", "unisex": "Unisex",
    "family": "Family gifts", "family-mom": "Mom", "family-dad": "Dad", "family-grandparents": "Grandparents",
    "family-aunt-uncle": "Aunt & Uncle", "family-siblings": "Siblings",
}
PRICE_BANDS = {"under-40": (0, 40), "40-60": (40, 60), "60-80": (60, 80), "80-plus": (80, 10_000)}
PRICE_LABELS = {"under-40": "Under $40", "40-60": "$40–$60", "60-80": "$60–$80", "80-plus": "$80 & up"}


def connect() -> sqlite3.Connection:
    # Read-only: neither the website nor the chatbot can modify the shop database through this module.
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def category_for(garment_type: str) -> str:
    """The catalogue has 22 spellings of ~8 garment types; map them to clean shop categories."""
    g = garment_type.lower()
    if "quarter-zip" in g:
        return "Quarter-Zips"
    if "jacket" in g or "fleece" in g:
        return "Jackets & Fleece"
    if "hood" in g:
        return "Hoodies"
    if "long-sleeve" in g:
        return "Long Sleeves"
    if "t-shirt" in g:
        return "T-Shirts"
    if "crewneck" in g or "mockneck" in g or "sweatshirt" in g:
        return "Crewnecks"
    return "Other"


def is_long_sleeve(garment_type: str, description: str, search_tags: list[str]) -> bool:
    text = " ".join([garment_type, description, *search_tags]).lower()
    return "long-sleeve" in text or "long sleeve" in text


def product_types(garment_type: str, description: str, search_tags: list[str]) -> list[str]:
    """Product Type memberships: the main category, plus "Long Sleeves" for every long-sleeved item
    (crewnecks, hoodies, quarter-zips… not just the 2 long-sleeve shirts), so that filter matches what shoppers mean."""
    types = [category_for(garment_type)]
    if "Long Sleeves" not in types and is_long_sleeve(garment_type, description, search_tags):
        types.append("Long Sleeves")
    return types


def color_families(colors: list[str]) -> list[str]:
    return sorted({_COLOR_TO_FAMILY.get(c.lower(), "Multicolor") for c in colors})


def shop_for(name: str, garment_type: str, search_tags: list[str]) -> list[str]:
    """Audience ids for the "Shop For" filter, from explicit labels in the catalogue only."""
    out: set[str] = set()
    family = re.match(r"^yale (mom|dad|grandma|grandpa|aunt|uncle|sister|brother)\b", name.lower())
    if family:
        sub, gender = FAMILY[family.group(1)]
        out |= {"family", sub, gender}
    labels = " ".join([name, garment_type, *search_tags]).lower()
    if re.search(r"\bmen'?s\b", labels):
        out.add("men")
    if re.search(r"\b(women'?s|ladies)\b", labels):
        out.add("women")
    if not out & {"men", "women"}:
        out.add("unisex")
    return sorted(out)


def price_band(price: float) -> str:
    return next(b for b, (lo, hi) in PRICE_BANDS.items() if lo <= price < hi)


def short_description(text: str, limit: int = 110) -> str:
    first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=1)[0]
    return first if len(first) <= limit else first[: limit - 1].rsplit(" ", 1)[0] + "…"


def image_url(path: str) -> str:
    return "/images/" + Path(path).name


def summary(row: sqlite3.Row, total_stock: int, sizes_in_stock: list[str] | None = None) -> dict:
    colors = json.loads(row["colors"])
    tags = json.loads(row["search_tags"])
    if sizes_in_stock is None and "sizes_in_stock" in row.keys():
        sizes_in_stock = [s for s in SIZE_ORDER if s in (row["sizes_in_stock"] or "").split(",")]
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "category": category_for(row["garment_type"]),
        "product_types": product_types(row["garment_type"], row["description"], tags),
        "garment_type": row["garment_type"],
        "price": row["price"],
        "short_description": short_description(row["description"]),
        "colors": colors,
        "color_families": color_families(colors),
        "shop_for": shop_for(row["name"], row["garment_type"], tags),
        "sizes_in_stock": sizes_in_stock or [],
        "image_url": image_url(row["image_file_path"]),
        "total_stock": total_stock,
    }


def all_products() -> list[sqlite3.Row]:
    """Every catalogue row plus its total stock, sorted by name."""
    with closing(connect()) as conn:
        return conn.execute(
            """SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock,
                      GROUP_CONCAT(CASE WHEN i.quantity > 0 THEN i.size END) AS sizes_in_stock
               FROM catalogue c LEFT JOIN inventory i ON i.product_id = c.product_id
               GROUP BY c.product_id ORDER BY c.name"""
        ).fetchall()


def stock_by_size(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[dict]]:
    """product_id -> [{"size", "quantity"}, …] in XS→XXL order."""
    if not product_ids:
        return {}
    marks = ",".join("?" * len(product_ids))
    rows = conn.execute(f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})", product_ids)
    out: dict[str, list[dict]] = {pid: [] for pid in product_ids}
    for r in rows:
        out[r["product_id"]].append({"size": r["size"], "quantity": r["quantity"]})
    for sizes in out.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else len(SIZE_ORDER))
    return out


def product_detail(product_id: str) -> dict | None:
    with closing(connect()) as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        inventory = stock_by_size(conn, [product_id])[product_id]
    return {
        **summary(row, sum(s["quantity"] for s in inventory), [s["size"] for s in inventory if s["quantity"] > 0]),
        "description": row["description"],
        "search_tags": json.loads(row["search_tags"]),
        "inventory": inventory,
    }


def search_text(products: list[dict], rows: list[sqlite3.Row], q: str | None) -> list[dict]:
    """Website search box: every word must appear in the name, description, colors or tags."""
    if not q:
        return products
    terms = q.lower().split()
    haystack = {r["product_id"]: " ".join([r["name"], r["description"], r["colors"], r["search_tags"]]).lower() for r in rows}
    return [p for p in products if all(t in haystack[p["product_id"]] for t in terms)]


def filter_products(
    products: list[dict],
    shop_for_ids: list[str] | None = None,
    categories: list[str] | None = None,
    colors: list[str] | None = None,
    sizes: list[str] | None = None,
    prices: list[str] | None = None,
) -> list[dict]:
    """Website filters: any option within one filter matches (OR); different filters must all match (AND)."""
    def lower(xs: list[str] | None) -> set[str]:
        return {x.lower() for x in xs or [] if x}

    want_for, want_cat, want_col = lower(shop_for_ids), lower(categories), lower(colors)
    want_size = {s.upper() for s in sizes or [] if s}
    want_price = lower(prices)
    out = []
    for p in products:
        if want_for and not want_for & set(p["shop_for"]):
            continue
        if want_cat and not want_cat & lower(p["product_types"]):
            continue
        if want_col and not want_col & lower(p["color_families"]):
            continue
        if want_size and not want_size & set(p["sizes_in_stock"]):
            continue
        if want_price and price_band(p["price"]) not in want_price:
            continue
        out.append(p)
    return out


LOW_STOCK = 3  # 1-3 units left in a size counts as "low"


def going_fast(limit: int = 12) -> list[dict]:
    """The "Going fast" list: products closest to selling out (fewest units left), with honest stock facts."""
    with closing(connect()) as conn:
        rows = all_products()
        stock = stock_by_size(conn, [r["product_id"] for r in rows])
    items = []
    for r in rows:
        sizes = stock[r["product_id"]]
        sold_out = [s["size"] for s in sizes if s["quantity"] == 0]
        low = [s for s in sizes if 0 < s["quantity"] <= LOW_STOCK]
        total = r["total_stock"]
        if total == 0:
            continue  # completely gone: nothing to buy
        items.append(
            {
                **summary(r, total),
                "units_left": total,
                "sold_out_sizes": sold_out,
                "low_sizes": [{"size": s["size"], "quantity": s["quantity"]} for s in low],
            }
        )
    items.sort(key=lambda p: (p["units_left"], -len(p["sold_out_sizes"])))
    return items[:limit]
