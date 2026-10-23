# Campus Customs harness

How the shop system is wired end-to-end.

## Database tables

### `catalogue`
- `product_id` — primary key for a SKU
- `name` — shopper-facing title
- `garment_type` — category for browse/search (hoodie, crewneck, …)
- `description` — full copy for detail pages and chat
- `colors` — available colorways
- `search_tags` — keywords for search / agent tools
- `image_file_path` — file under `data/products/`
- `price` — list price; tools must read this, never invent it

### `inventory`
- `id` — row id
- `product_id` — FK to catalogue
- `size` — size label
- `quantity` — units on hand; honest OOS when 0

### `users`
- `id`, `name`, `first_name`, `last_name`, `email`, `password_hash`, `created_at`
- Accounts created via signup; passwords hashed (see Auth)

### `chat_messages`
- `user_id`, `role`, `content`, `products_json`, `created_at`
- Persists chat for logged-in shoppers only

## Auth

**Store:** first/last name, email, and `password_hash` only (format `pbkdf2_sha256$salt$hex`).

**Protect passwords:** PBKDF2-HMAC-SHA256, 120,000 iterations. Login reuses the stored salt, re-hashes, and compares with `hmac.compare_digest`. Seeded user `test@campuscustoms.yale.edu` / `password` must work; new signups use the same settings.

## Front end ↔ FastAPI

- Vite app on `:5173` proxies `/api`, `/auth`, `/media` to Uvicorn `:8000`.
- Product images: `/media/products/...` (StaticFiles over `data/`) so React’s `/products` route is free.
- Products: `GET /api/products`, `GET /api/products/{id}`, garment filter via `?garment=`.
- Auth: `POST /auth/signup`, `POST /auth/login`.
- Chat: `POST /api/chat` with `{ message, user_id?, page? }` → `{ reply, products[], suggestions[], tool_events[] }`.
- History: `GET /api/chat/history?user_id=` reloads bubbles for signed-in users.
- Search handoff: when the agent calls `search_catalogue`, `products` is returned and the Products page spotlight renders those cards; each card still opens the detail route.

## Agent load

- Files: `backend/prompts/prompt.md`, `agent.py`, `tools.py`, `models.py`; app entry `main.py`.
- Model: `OPENAI_MODEL` (default `gpt-5.6-luna`) via `OPENAI_API_KEY` (or Portkey if that key is set).
- Deps carry logged-in profile + page context (`product_id` / name) so “this” resolves on product pages.
- Usage limits: request_limit 8, tool_calls_limit 6.
- If no API key is present, a local tool-using fallback still answers stock/search from SQLite so the UI can be exercised.

## Tools and model fields

| Tool | Why / return shape |
|------|--------------------|
| `lookup_product` | Full `ProductInfo` (description, price, colors, stock[]) for one SKU |
| `get_price` | `{found, name, price}` — price-only questions |
| `get_stock` | Per-size quantities; explicit OOS message when quantity is 0 |
| `search_catalogue` | `ProductCard[]` capped at 8 for page cards |
| `list_categories` | Distinct `garment_type` values |

`ProductCard` fields (`product_id`, `name`, `price`, `garment_type`, `short_description`, `image_file_path`) are exactly what the React grid needs — no extra nested junk.

## Safety

- Prompt forbids inventing inventory/prices, leaking hashes/other accounts, or taking card/SSN data.
- Tools only read SQLite; they never write catalogue or inventory.
- Audit trail appends every tool call to `output/audit_trail.json` (never wiped between runs).

## Specs / how to run

```bash
# data pack unzipped to hw4/data/
cd backend && uvicorn main:app --reload --port 8000
cd frontend && npm install && npm run dev
```

Loop limits as above. Search results capped at 8. Frontend localStorage holds session user + recently viewed ids.
