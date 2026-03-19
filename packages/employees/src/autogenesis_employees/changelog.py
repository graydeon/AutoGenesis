"""ChangelogManager — append-only markdown changelog."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from autogenesis_employees.models import ChangelogEntry


class ChangelogManager:
    def __init__(self, path: Path) -> None:
        self._path = path

    def write(self, entry: ChangelogEntry) -> None:
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M")
        files_str = ", ".join(entry.files) if entry.files else "none"
        block = (
            f"\n## {ts} — {entry.employee_id}\n"
            f"**Task:** {entry.task}\n"
            f"**Changes:** {entry.changes}\n"
            f"**Files:** {files_str}\n"
        )
        if entry.notes:
            block += f"**Notes:** {entry.notes}\n"
        block += "\n"

        with self._path.open("a") as f:
            f.write(block)

    def read_recent(self, limit: int = 10) -> list[str]:
        if not self._path.exists():
            return []
        content = self._path.read_text()
        entries = re.split(r"\n(?=## \d{4}-\d{2}-\d{2})", content)
        entries = [e.strip() for e in entries if e.strip()]
        return entries[-limit:]
