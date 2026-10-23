"""Campus Customs FastAPI app.

Run from backend/:
  uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
import sqlite3

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from agent import run_shop_agent
from auth import hash_password, verify_password
from db import DB_PATH, ROOT, get_connection
from models import (
    AuthResponse,
    ChatHistoryItem,
    ChatRequest,
    ChatResponse,
    LoginRequest,
    ProductCard,
    SignupRequest,
    UserOut,
)
from tools import get_product_info, search_products

app = FastAPI(title="Campus Customs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve data/ under /media so /media/products/*.jpg works without
# colliding with the React /products route (proxied by Vite).
DATA_DIR = ROOT / "data"
if DATA_DIR.exists():
    app.mount("/media", StaticFiles(directory=DATA_DIR), name="media")


def _row_to_user(row: sqlite3.Row) -> UserOut:
    first = row["first_name"] or ""
    last = row["last_name"] or ""
    name = row["name"] or f"{first} {last}".strip()
    return UserOut(
        id=row["id"],
        first_name=first,
        last_name=last,
        name=name,
        email=row["email"],
    )


def _load_user(user_id: int) -> UserOut | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return _row_to_user(row) if row else None


def _save_chat(
    user_id: int,
    role: str,
    content: str,
    products: list[ProductCard] | None = None,
) -> None:
    payload = json.dumps([p.model_dump() for p in products]) if products else None
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO chat_messages (user_id, role, content, products_json)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, role, content, payload),
        )
        conn.commit()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "database": str(DB_PATH)}


@app.post("/auth/signup", response_model=AuthResponse)
def signup(body: SignupRequest) -> AuthResponse:
    first = body.first_name.strip()
    last = body.last_name.strip()
    email = body.email.strip().lower()
    password = body.password
    confirm = body.confirm_password

    if not first or not last:
        raise HTTPException(status_code=400, detail="First and last name are required.")
    if password != confirm:
        raise HTTPException(status_code=400, detail="Passwords do not match.")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters.")

    password_hash = hash_password(password)
    full_name = f"{first} {last}"

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO users (name, email, password_hash, first_name, last_name)
                VALUES (?, ?, ?, ?, ?)
                """,
                (full_name, email, password_hash, first, last),
            )
            conn.commit()
            user_id = cur.lastrowid
            row = conn.execute(
                "SELECT id, name, email, first_name, last_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AuthResponse(user=_row_to_user(row), message="Account created.")


@app.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest) -> AuthResponse:
    email = body.email.strip().lower()
    password = body.password

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, email, first_name, last_name, password_hash
                FROM users
                WHERE lower(email) = ?
                """,
                (email,),
            ).fetchone()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if row is None or not verify_password(password, row["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    return AuthResponse(user=_row_to_user(row), message="Logged in.")


@app.get("/auth/me", response_model=UserOut)
def me(email: str) -> UserOut:
    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT id, name, email, first_name, last_name
                FROM users
                WHERE lower(email) = ?
                """,
                (email.strip().lower(),),
            ).fetchone()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    if row is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return _row_to_user(row)


@app.post("/auth/logout")
def logout() -> dict[str, str]:
    return {"message": "Logged out."}


@app.get("/api/products")
def list_products(q: str | None = None, garment: str | None = None) -> list[dict]:
    try:
        if q:
            return [c.model_dump() for c in search_products(q)]
        with get_connection() as conn:
            if garment:
                rows = conn.execute(
                    """
                    SELECT product_id, name, garment_type, description, colors,
                           search_tags, image_file_path, price
                    FROM catalogue
                    WHERE lower(garment_type) LIKE '%' || lower(?) || '%'
                    ORDER BY name
                    """,
                    (garment,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT product_id, name, garment_type, description, colors,
                           search_tags, image_file_path, price
                    FROM catalogue
                    ORDER BY name
                    """
                ).fetchall()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return [dict(r) for r in rows]


@app.get("/api/products/{product_id}")
def product_detail(product_id: str) -> dict:
    info = get_product_info(product_id)
    if info is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    return info.model_dump()


@app.get("/api/garment-types")
def garment_types() -> list[str]:
    from tools import list_garment_types

    return list_garment_types()


@app.post("/api/chat", response_model=ChatResponse)
def chat(body: ChatRequest) -> ChatResponse:
    user = _load_user(body.user_id) if body.user_id else None
    if body.user_id and user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    if user:
        _save_chat(user.id, "user", body.message)

    result = run_shop_agent(body.message, user=user, page=body.page)

    if user:
        _save_chat(user.id, "assistant", result.reply, result.products)

    return result


@app.get("/api/chat/history", response_model=list[ChatHistoryItem])
def chat_history(user_id: int = Query(...), limit: int = Query(40, ge=1, le=200)) -> list[ChatHistoryItem]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT role, content, products_json, created_at
            FROM chat_messages
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    items: list[ChatHistoryItem] = []
    for row in reversed(rows):
        products: list[ProductCard] = []
        if row["products_json"]:
            try:
                raw = json.loads(row["products_json"])
                products = [ProductCard.model_validate(p) for p in raw]
            except (json.JSONDecodeError, ValueError):
                products = []
        items.append(
            ChatHistoryItem(
                role=row["role"],
                content=row["content"],
                products=products,
                created_at=row["created_at"],
            )
        )
    return items
