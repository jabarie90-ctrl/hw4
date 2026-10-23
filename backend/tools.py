"""Database tools for the Campus Customs shop agent.

Every price, description, and stock number comes from campus_customs.db.
"""

from __future__ import annotations

import re
import sqlite3
from typing import Any

from db import get_connection
from models import ProductCard, ProductInfo, StockBySize

# Cap search results so the page stays scannable (usability improvement).
SEARCH_RESULT_CAP = 8


def _short(text: str, n: int = 140) -> str:
    text = (text or "").strip()
    if len(text) <= n:
        return text
    return text[: n - 1].rstrip() + "…"


def _row_card(row: sqlite3.Row) -> ProductCard:
    return ProductCard(
        product_id=row["product_id"],
        name=row["name"],
        price=float(row["price"]),
        garment_type=row["garment_type"],
        short_description=_short(row["description"]),
        image_file_path=row["image_file_path"],
        colors=row["colors"] or "",
    )


def get_product_info(product_query: str) -> ProductInfo | None:
    """Look up one product by id or fuzzy name. Returns None if not found."""
    q = product_query.strip()
    if not q:
        return None
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT product_id, name, description, price, garment_type, colors, image_file_path
            FROM catalogue
            WHERE lower(product_id) = lower(?)
               OR lower(name) = lower(?)
            LIMIT 1
            """,
            (q, q),
        ).fetchone()
        if row is None:
            row = conn.execute(
                """
                SELECT product_id, name, description, price, garment_type, colors, image_file_path
                FROM catalogue
                WHERE lower(name) LIKE '%' || lower(?) || '%'
                   OR lower(search_tags) LIKE '%' || lower(?) || '%'
                   OR lower(product_id) LIKE '%' || lower(?) || '%'
                ORDER BY length(name) ASC
                LIMIT 1
                """,
                (q, q, q),
            ).fetchone()
        if row is None:
            return None
        stock_rows = conn.execute(
            """
            SELECT size, quantity FROM inventory
            WHERE product_id = ?
            ORDER BY
              CASE size
                WHEN 'XS' THEN 1 WHEN 'S' THEN 2 WHEN 'M' THEN 3
                WHEN 'L' THEN 4 WHEN 'XL' THEN 5 WHEN 'XXL' THEN 6
                ELSE 99 END
            """,
            (row["product_id"],),
        ).fetchall()
    return ProductInfo(
        product_id=row["product_id"],
        name=row["name"],
        description=row["description"],
        price=float(row["price"]),
        garment_type=row["garment_type"],
        colors=row["colors"],
        image_file_path=row["image_file_path"],
        stock=[StockBySize(size=r["size"], quantity=int(r["quantity"])) for r in stock_rows],
    )


def get_price(product_query: str) -> dict[str, Any]:
    info = get_product_info(product_query)
    if info is None:
        return {"found": False, "message": f"No product matched {product_query!r}."}
    return {
        "found": True,
        "product_id": info.product_id,
        "name": info.name,
        "price": info.price,
    }


def get_stock(product_query: str, size: str | None = None) -> dict[str, Any]:
    """Return stock by size. Honest about out-of-stock sizes."""
    info = get_product_info(product_query)
    if info is None:
        return {"found": False, "message": f"No product matched {product_query!r}."}
    stock = info.stock
    if size:
        size_u = size.strip().upper()
        match = next((s for s in stock if s.size.upper() == size_u), None)
        if match is None:
            return {
                "found": True,
                "product_id": info.product_id,
                "name": info.name,
                "size": size_u,
                "quantity": 0,
                "in_stock": False,
                "message": f"{info.name} is not carried in size {size_u}.",
                "all_sizes": [s.model_dump() for s in stock],
            }
        return {
            "found": True,
            "product_id": info.product_id,
            "name": info.name,
            "size": match.size,
            "quantity": match.quantity,
            "in_stock": match.quantity > 0,
            "message": (
                f"{info.name} size {match.size}: {match.quantity} in stock."
                if match.quantity > 0
                else f"{info.name} size {match.size} is out of stock."
            ),
            "all_sizes": [s.model_dump() for s in stock],
        }
    return {
        "found": True,
        "product_id": info.product_id,
        "name": info.name,
        "all_sizes": [s.model_dump() for s in stock],
        "any_in_stock": any(s.quantity > 0 for s in stock),
    }


def search_products(query: str, limit: int = SEARCH_RESULT_CAP) -> list[ProductCard]:
    """Search catalogue by garment type, tags, name, or color words."""
    raw = query.strip()
    if not raw:
        return []
    # Expand a few shopper phrases into DB garment_type / tag fragments.
    aliases = {
        "hoodie": "hoodie",
        "hoodies": "hoodie",
        "crewneck": "crewneck",
        "crewnecks": "crewneck",
        "sweater": "sweater",
        "sweaters": "sweater",
        "jacket": "jacket",
        "jackets": "jacket",
        "tee": "t-shirt",
        "tees": "t-shirt",
        "tshirt": "t-shirt",
        "t-shirt": "t-shirt",
        "t-shirts": "t-shirt",
        "shirt": "t-shirt",
        "zip": "zip",
        "quarter zip": "quarter-zip",
        "college": "college",
    }
    q = aliases.get(raw.lower(), raw)
    tokens = [t for t in re.split(r"\s+", q) if t]
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT product_id, name, description, price, garment_type, colors, image_file_path, search_tags
            FROM catalogue
            WHERE lower(garment_type) LIKE '%' || lower(?) || '%'
               OR lower(name) LIKE '%' || lower(?) || '%'
               OR lower(search_tags) LIKE '%' || lower(?) || '%'
               OR lower(description) LIKE '%' || lower(?) || '%'
               OR lower(colors) LIKE '%' || lower(?) || '%'
            ORDER BY
              CASE WHEN lower(garment_type) LIKE '%' || lower(?) || '%' THEN 0 ELSE 1 END,
              name
            LIMIT ?
            """,
            (q, q, q, q, q, q, max(1, min(limit, SEARCH_RESULT_CAP))),
        ).fetchall()
        if not rows and tokens:
            like = "%" + "%".join(tokens) + "%"
            rows = conn.execute(
                """
                SELECT product_id, name, description, price, garment_type, colors, image_file_path, search_tags
                FROM catalogue
                WHERE lower(name) LIKE lower(?)
                   OR lower(search_tags) LIKE lower(?)
                ORDER BY name
                LIMIT ?
                """,
                (like, like, max(1, min(limit, SEARCH_RESULT_CAP))),
            ).fetchall()
    return [_row_card(r) for r in rows]


def list_garment_types() -> list[str]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT garment_type FROM catalogue ORDER BY garment_type"
        ).fetchall()
    return [r["garment_type"] for r in rows]
