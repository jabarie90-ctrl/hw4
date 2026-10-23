"""Append-only audit trail for agent loops."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
_LOCK = Lock()


def append_audit(
    *,
    tool_name: str,
    args: dict | str | None = None,
    result: str | dict | list | None = None,
    stop_reason: str | None = None,
    user_id: int | None = None,
) -> None:
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "tool_name": tool_name,
        "args": args if args is not None else {},
        "result": _clip(result),
        "stop_reason": stop_reason,
        "user_id": user_id,
    }
    with _LOCK:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        if AUDIT_PATH.exists():
            try:
                data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    data = []
            except json.JSONDecodeError:
                data = []
        else:
            data = []
        data.append(entry)
        AUDIT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _clip(value: object, limit: int = 500) -> object:
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        text = json.dumps(value, default=str)
        if len(text) > limit:
            return text[: limit - 1] + "…"
        return value
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"
