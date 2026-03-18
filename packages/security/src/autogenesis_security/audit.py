"""Tamper-proof audit logging."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from os import environ
from pathlib import Path
from typing import Any


def _default_audit_dir() -> Path:
    xdg_state = environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    return Path(xdg_state) / "autogenesis" / "audit"


class AuditLogger:
    """Append-only JSON Lines audit log with SHA-256 hash chain."""

    def __init__(self, audit_dir: Path | None = None) -> None:
        self._dir = audit_dir or _default_audit_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._last_hash = "genesis"

    def _log_path(self, date: datetime | None = None) -> Path:
        d = date or datetime.now(UTC)
        return self._dir / f"{d.strftime('%Y-%m-%d')}.jsonl"

    def log(self, event_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """Append an audit entry. Returns the entry."""
        now = datetime.now(UTC)
        entry = {
            "timestamp": now.isoformat(),
            "event_type": event_type,
            "data": data or {},
            "prev_hash": self._last_hash,
        }
        entry_str = json.dumps(entry, sort_keys=True)
        hash_val = hashlib.sha256(entry_str.encode()).hexdigest()
        entry["hash"] = hash_val
        self._last_hash = hash_val

        path = self._log_path(now)
        with path.open("a") as f:
            f.write(json.dumps(entry) + "\n")

        return entry

    def query(
        self,
        event_type: str | None = None,
        since: datetime | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query audit entries."""
        results: list[dict[str, Any]] = []
        for path in sorted(self._dir.glob("*.jsonl")):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if event_type and entry.get("event_type") != event_type:
                    continue
                if since:
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if ts < since:
                        continue
                results.append(entry)
                if len(results) >= limit:
                    return results
        return results

    def verify_chain(self) -> bool:
        """Verify the hash chain integrity."""
        prev_hash = "genesis"
        for path in sorted(self._dir.glob("*.jsonl")):
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry.get("prev_hash") != prev_hash:
                    return False
                prev_hash = entry["hash"]
        return True
