"""Campus Customs PydanticAI agent — chat brain for the FastAPI backend."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools as shop_tools
from audit import append_audit
from models import ChatResponse, PageContext, ProductCard, UserOut

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "prompt.md"

load_dotenv(ROOT.parent / ".env", override=True)
load_dotenv(ROOT.parent.parent / ".env", override=True)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


@dataclass
class ShopDeps:
    user: UserOut | None = None
    page: PageContext | None = None
    products: list[ProductCard] = field(default_factory=list)
    tool_events: list[dict] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def note(self, name: str, detail: str = "") -> None:
        self.tool_events.append({"name": name, "detail": detail})
        append_audit(
            tool_name=name,
            args=detail,
            result="ok",
            user_id=self.user.id if self.user else None,
        )


_AGENT: Agent[ShopDeps, str] | None = None


def _has_api_key() -> bool:
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("PORTKEY_API_KEY"))


def _model():
    """OpenAI direct (this machine) or Portkey if only that key is present."""
    portkey = os.getenv("PORTKEY_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(api_key=openai_key))
    if portkey:
        return OpenAIChatModel(
            MODEL_NAME,
            provider=OpenAIProvider(
                api_key=portkey,
                base_url=os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1"),
            ),
        )
    raise RuntimeError("No OPENAI_API_KEY or PORTKEY_API_KEY configured.")


def _build_agent() -> Agent[ShopDeps, str]:
    agent = Agent(
        _model(),
        deps_type=ShopDeps,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        name="campus_customs_shop",
    )

    @agent.instructions
    def runtime_context(ctx: RunContext[ShopDeps]) -> str:
        parts: list[str] = []
        if ctx.deps.user:
            parts.append(
                f"Logged-in shopper: {ctx.deps.user.first_name} {ctx.deps.user.last_name} "
                f"<{ctx.deps.user.email}> (user_id={ctx.deps.user.id})."
            )
        else:
            parts.append("Shopper is a guest (not logged in).")
        page = ctx.deps.page
        if page and (page.product_id or page.product_name):
            parts.append(
                "Page context: shopper is viewing "
                f"product_id={page.product_id!r} name={page.product_name!r} path={page.path!r}. "
                "If they say 'this' or ask about a color/size without naming an item, use this product."
            )
        elif page and page.path:
            parts.append(f"Page path: {page.path}")
        return "\n".join(parts)

    @agent.tool
    def lookup_product(ctx: RunContext[ShopDeps], product_query: str) -> dict:
        """Get description, price, colors, and stock for one product by name or id."""
        ctx.deps.note("lookup_product", product_query)
        info = shop_tools.get_product_info(product_query)
        if info is None:
            return {"found": False, "message": f"No match for {product_query!r}."}
        card = ProductCard(
            product_id=info.product_id,
            name=info.name,
            price=info.price,
            garment_type=info.garment_type,
            short_description=info.description[:140],
            image_file_path=info.image_file_path,
            colors=info.colors,
        )
        ctx.deps.products = [card]
        return info.model_dump()

    @agent.tool
    def get_price(ctx: RunContext[ShopDeps], product_query: str) -> dict:
        """Return the catalogue price for a product. Never invent prices."""
        ctx.deps.note("get_price", product_query)
        return shop_tools.get_price(product_query)

    @agent.tool
    def get_stock(ctx: RunContext[ShopDeps], product_query: str, size: str | None = None) -> dict:
        """Return inventory quantities by size. Say clearly when a size is out of stock."""
        ctx.deps.note("get_stock", f"{product_query} size={size}")
        return shop_tools.get_stock(product_query, size)

    @agent.tool
    def search_catalogue(ctx: RunContext[ShopDeps], query: str) -> list[dict]:
        """Search the catalogue (e.g. hoodies, crewnecks). Results appear as cards on the website."""
        ctx.deps.note("search_catalogue", query)
        cards = shop_tools.search_products(query)
        ctx.deps.products = cards
        if cards:
            ctx.deps.suggestions = [
                f"Do you want {cards[0].name} in a specific size?",
                "Want me to check stock for one of these?",
            ]
        return [c.model_dump() for c in cards]

    @agent.tool
    def list_categories(ctx: RunContext[ShopDeps]) -> list[str]:
        """List garment types available in the catalogue."""
        ctx.deps.note("list_categories", "")
        return shop_tools.list_garment_types()

    return agent


def get_agent() -> Agent[ShopDeps, str]:
    global _AGENT
    if _AGENT is None:
        _AGENT = _build_agent()
    return _AGENT


def _local_shop_reply(message: str, deps: ShopDeps) -> str:
    """Deterministic tool-using fallback when no API key is configured (demo / offline)."""
    text = message.strip()
    lower = text.lower()

    # Prefer page context for "this"
    focus = None
    if deps.page and deps.page.product_id and re.search(r"\b(this|it)\b", lower):
        focus = deps.page.product_id

    size_match = re.search(r"\b(xxl|xl|xs|s|m|l)\b", lower)
    size = size_match.group(1).upper() if size_match else None

    stock_ask = any(w in lower for w in ("stock", "inventory", "in stock", "available")) or (
        "size" in lower and not any(w in lower for w in ("what", "show", "which", "have you"))
    )
    price_ask = "price" in lower or "cost" in lower or "how much" in lower
    category_ask = any(
        w in lower
        for w in (
            "hoodie",
            "hoodies",
            "crewneck",
            "jacket",
            "tee",
            "t-shirt",
            "shirt",
            "what do you have",
            "show me",
        )
    ) and not stock_ask and not price_ask

    def _clean_query(raw: str) -> str:
        cleaned = re.sub(
            r"\b(what|is|the|price|of|how|much|does|cost|stock|do|you|have|in|size|available|inventory|for)\b",
            " ",
            raw,
            flags=re.I,
        )
        # Drop size tokens so "Basic Hoodie … size M" still resolves to the product name.
        cleaned = re.sub(r"\b(xxl|xl|xs|s|m|l)\b", " ", cleaned, flags=re.I)
        return re.sub(r"\s+", " ", cleaned).strip(" ?.") or (
            deps.page.product_name if deps.page and deps.page.product_name else raw
        )

    if stock_ask:
        target = focus or _clean_query(text)
        deps.note("get_stock", f"{target} size={size}")
        result = shop_tools.get_stock(target, size)
        if not result.get("found"):
            return result.get("message", "I could not find that product.")
        if size:
            return result["message"]
        lines = [f"{s['size']}: {s['quantity']}" for s in result.get("all_sizes", [])]
        return f"{result['name']} stock — " + "; ".join(lines)

    if price_ask or (focus and not category_ask):
        target = focus or _clean_query(text)
        deps.note("lookup_product", target)
        info = shop_tools.get_product_info(target)
        if info is None:
            return f"I could not find a product matching {target!r}."
        deps.products = [
            ProductCard(
                product_id=info.product_id,
                name=info.name,
                price=info.price,
                garment_type=info.garment_type,
                short_description=info.description[:140],
                image_file_path=info.image_file_path,
                colors=info.colors,
            )
        ]
        stock_bits = ", ".join(f"{s.size}={s.quantity}" for s in info.stock)
        return (
            f"{info.name} is ${info.price:.2f}. {info.description[:220]} "
            f"Stock by size: {stock_bits}."
        )

    if category_ask:
        query = "hoodie" if "hoodie" in lower else text
        for key in ("hoodie", "crewneck", "jacket", "t-shirt", "tee", "zip"):
            if key in lower:
                query = key
                break
        deps.note("search_catalogue", query)
        cards = shop_tools.search_products(query)
        deps.products = cards
        deps.suggestions = ["Want stock for a size?", "Tell me a college name to narrow it."]
        if not cards:
            return "I could not find matching items in the catalogue for that."
        names = ", ".join(c.name for c in cards[:4])
        return (
            f"I found {len(cards)} matching item(s), including {names}. "
            "They should appear as product cards on the page — tap one for full details."
        )

    greeting = f"Hi {deps.user.first_name} — " if deps.user else ""
    return (
        f"{greeting}I can look up prices, stock by size, or search the catalogue "
        "(try “what hoodies do you have?”)."
    )


def run_shop_agent(
    message: str,
    *,
    user: UserOut | None = None,
    page: PageContext | None = None,
) -> ChatResponse:
    load_dotenv(ROOT.parent / ".env", override=True)
    load_dotenv(ROOT.parent.parent / ".env", override=True)

    deps = ShopDeps(user=user, page=page)
    append_audit(
        tool_name="chat_turn_start",
        args={"message": message[:200], "page": page.model_dump() if page else None},
        user_id=user.id if user else None,
    )

    if not _has_api_key():
        reply = _local_shop_reply(message, deps)
        append_audit(
            tool_name="chat_turn_end",
            result=reply[:300],
            stop_reason="local_fallback_no_api_key",
            user_id=user.id if user else None,
        )
        return ChatResponse(
            reply=reply,
            products=deps.products,
            suggestions=deps.suggestions,
            tool_events=deps.tool_events,
        )

    try:
        result = get_agent().run_sync(
            message,
            deps=deps,
            usage_limits=UsageLimits(request_limit=8, tool_calls_limit=6),
        )
        reply = str(result.output)
        stop = "agent_completed"
    except Exception as exc:  # noqa: BLE001 — surface a friendly shop reply
        reply = (
            "Sorry — the assistant hit a snag talking to the model. "
            f"({type(exc).__name__}) You can still browse Products while we retry."
        )
        stop = f"error:{type(exc).__name__}"
        append_audit(
            tool_name="chat_error",
            result=str(exc)[:400],
            stop_reason=stop,
            user_id=user.id if user else None,
        )

    append_audit(
        tool_name="chat_turn_end",
        result=reply[:300],
        stop_reason=stop,
        user_id=user.id if user else None,
    )
    return ChatResponse(
        reply=reply,
        products=deps.products,
        suggestions=deps.suggestions,
        tool_events=deps.tool_events,
    )
