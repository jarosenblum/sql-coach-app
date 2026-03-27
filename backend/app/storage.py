from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.schemas import SessionState

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    return SESSIONS_DIR / f"{session_id}.json"


def save_session(state: SessionState) -> None:
    path = _session_path(state.session_id)
    path.write_text(
        state.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_session(session_id: str) -> Optional[SessionState]:
    path = _session_path(session_id)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return SessionState(**data)
    except Exception:
        return None