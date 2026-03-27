from __future__ import annotations

import sqlite3
from pathlib import Path
from threading import Lock
from typing import Any


DB_LOCK = Lock()
_CONN: sqlite3.Connection | None = None


def _get_bootstrap_sql_path() -> Path:
    return Path(__file__).resolve().parent.parent / "data" / "w3schools_bootstrap.sql"


def _init_connection() -> sqlite3.Connection:
    global _CONN

    if _CONN is not None:
        return _CONN

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row

    bootstrap_path = _get_bootstrap_sql_path()
    if not bootstrap_path.exists():
        raise FileNotFoundError(
            f"Missing bootstrap SQL file at {bootstrap_path}. "
            "Create backend/data/w3schools_bootstrap.sql with CREATE TABLE and INSERT statements."
        )

    sql_text = bootstrap_path.read_text(encoding="utf-8")
    conn.executescript(sql_text)
    _CONN = conn
    return conn


def execute_student_sql(sql_query: str) -> dict[str, Any]:
    conn = _init_connection()

    sql_query = (sql_query or "").strip()
    if not sql_query:
        return {
            "executed": False,
            "columns": [],
            "row_count": 0,
            "sample_rows": [],
            "error": "Empty SQL query.",
        }

    # Only allow SELECT-style queries for safety
    lowered = sql_query.lower().strip()
    if not lowered.startswith("select"):
        return {
            "executed": False,
            "columns": [],
            "row_count": 0,
            "sample_rows": [],
            "error": "Only SELECT queries are allowed.",
        }

    try:
        with DB_LOCK:
            cur = conn.cursor()
            cur.execute(sql_query)
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description] if cur.description else []

        sample_rows = [list(row) for row in rows[:5]]

        return {
            "executed": True,
            "columns": columns,
            "row_count": len(rows),
            "sample_rows": sample_rows,
            "error": None,
        }
    except Exception as e:
        return {
            "executed": False,
            "columns": [],
            "row_count": 0,
            "sample_rows": [],
            "error": str(e),
        }