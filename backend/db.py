"""SQLite helpers for the Campus Customs data pack."""

from __future__ import annotations

import sqlite3
from pathlib import Path

# backend/ → hw4/ → data/campus_customs.db
ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "campus_customs.db"


def get_connection() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Missing database at {DB_PATH}. "
            "Download data.zip from the course site and unzip it into hw4/."
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
