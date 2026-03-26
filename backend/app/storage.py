from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from app.schemas import SessionState

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def _session_path(session_id: str) -> Path:
    return DATA_DIR / f"{session_id}.json"


def save_session(state: SessionState) -> None:
    _session_path(state.session_id).write_text(
        state.model_dump_json(indent=2), encoding="utf-8"
    )


def load_session(session_id: str) -> Optional[SessionState]:
    path = _session_path(session_id)
    if not path.exists():
        return None
    return SessionState.model_validate_json(path.read_text(encoding="utf-8"))