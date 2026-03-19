"""Changelog write tool for documenting completed work."""

from __future__ import annotations

import os
from typing import Any

from autogenesis_employees.models import ChangelogEntry

from autogenesis_tools.base import Tool


class ChangelogWriteTool(Tool):
    def __init__(self, changelog_manager: Any = None) -> None:  # noqa: ANN401
        self._changelog = changelog_manager

    @property
    def name(self) -> str:
        return "changelog_write"

    @property
    def description(self) -> str:
        return "Document your completed work in the team changelog."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "What task was completed"},
                "changes": {"type": "string", "description": "What changes were made"},
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Files changed",
                },
                "notes": {"type": "string", "description": "Additional notes"},
            },
            "required": ["task", "changes"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._changelog is None:
            return "Error: ChangelogManager not configured"
        entry = ChangelogEntry(
            employee_id=os.environ.get("ROLE", "unknown"),
            task=arguments["task"],
            changes=arguments["changes"],
            files=arguments.get("files", []),
            notes=arguments.get("notes", ""),
        )
        self._changelog.write(entry)
        return f"Changelog updated: {arguments['task']}"
