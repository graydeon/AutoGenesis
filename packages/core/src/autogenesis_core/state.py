"""Session state persistence."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from os import environ
from pathlib import Path
from typing import Any

import structlog

from autogenesis_core.models import AgentState

logger = structlog.get_logger()


def _default_state_dir() -> Path:
    """Return XDG state directory for sessions."""
    xdg_state = environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    return Path(xdg_state) / "autogenesis" / "sessions"


class StatePersistence:
    """Save/load AgentState to JSON files with atomic writes."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self._base_dir = base_dir or _default_state_dir()
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._base_dir / f"{session_id}.json"

    def save(self, state: AgentState) -> None:
        """Save state atomically via temp file + rename."""
        target = self._session_path(state.session_id)
        data = state.model_dump_json(indent=2)

        # Atomic write: write to temp file in same directory, then rename
        fd, tmp_path = tempfile.mkstemp(dir=self._base_dir, suffix=".tmp")
        try:
            with open(fd, "w") as f:  # noqa: PTH123
                f.write(data)
            Path(tmp_path).rename(target)
        except BaseException:
            Path(tmp_path).unlink(missing_ok=True)
            raise

        logger.debug("state_saved", session_id=state.session_id)

    def load(self, session_id: str) -> AgentState | None:
        """Load state from JSON file. Returns None if not found."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        try:
            data = path.read_text()
            return AgentState.model_validate_json(data)
        except (json.JSONDecodeError, ValueError):
            logger.warning("state_load_failed", session_id=session_id)
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all saved sessions with basic metadata."""
        sessions = []
        for path in self._base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                sessions.append(
                    {
                        "session_id": data["session_id"],
                        "created_at": data.get("created_at"),
                        "updated_at": data.get("updated_at"),
                    }
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    def cleanup(self, retention_days: int = 30) -> int:
        """Remove sessions older than retention_days. Returns count removed."""
        cutoff = datetime.now(UTC) - __import__("datetime").timedelta(days=retention_days)
        removed = 0
        for path in self._base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text())
                updated = data.get("updated_at", data.get("created_at"))
                if updated and datetime.fromisoformat(updated) < cutoff:
                    path.unlink()
                    removed += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        logger.info("state_cleanup", removed=removed, retention_days=retention_days)
        return removed
