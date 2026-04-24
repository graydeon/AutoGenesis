"""MeetingManager — standup and on-demand meeting orchestration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from zoneinfo import ZoneInfo

import structlog

if TYPE_CHECKING:
    from pathlib import Path

    from autogenesis_employees.models import StandupEntry

logger = structlog.get_logger()


def is_standup_due(last_run: str | None, standup_time: str, tz_name: str) -> bool:  # noqa: ARG001
    if last_run is None:
        return True
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date().isoformat()
    return last_run != today


class MeetingManager:
    def __init__(self, meetings_dir: Path) -> None:
        self._dir = meetings_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def write_standup(self, entries: list[StandupEntry]) -> Path:
        now = datetime.now(UTC)
        filename = f"standup-{now.strftime('%Y-%m-%d')}.md"
        path = self._dir / filename
        lines = [f"## Standup — {now.strftime('%Y-%m-%d %H:%M')}\n"]
        for entry in entries:
            lines.append(f"\n### {entry.employee_id}")
            lines.append(f"- **Yesterday:** {entry.yesterday}")
            lines.append(f"- **Today:** {entry.today}")
            lines.append(f"- **Blockers:** {entry.blockers or 'None'}")
        path.write_text("\n".join(lines) + "\n")
        logger.info("standup_written", path=str(path), employees=len(entries))
        return path

    def write_meeting(self, topic: str, rounds: list[dict[str, str]]) -> Path:
        now = datetime.now(UTC)
        filename = f"meeting-{now.strftime('%Y-%m-%d-%H%M%S')}.md"
        path = self._dir / filename
        lines = [f"## Meeting — {now.strftime('%Y-%m-%d %H:%M')}\n"]
        lines.append(f"**Topic:** {topic}\n")
        for i, entry in enumerate(rounds, 1):
            lines.append(f"\n### Round {i} — {entry['employee']}")
            lines.append(entry["response"])
        path.write_text("\n".join(lines) + "\n")
        logger.info("meeting_written", path=str(path), topic=topic[:50])
        return path
