"""Standup write tool for daily updates."""

from __future__ import annotations

import os
from typing import Any

from autogenesis_tools.base import Tool


class StandupWriteTool(Tool):
    def __init__(self) -> None:
        pass

    @property
    def name(self) -> str:
        return "standup_write"

    @property
    def description(self) -> str:
        return "Post your daily standup update."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "yesterday": {"type": "string", "description": "What you did yesterday"},
                "today": {"type": "string", "description": "What you plan to do today"},
                "blockers": {"type": "string", "description": "Any blockers"},
            },
            "required": ["yesterday", "today"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 80

    async def execute(self, arguments: dict[str, Any]) -> str:
        role = os.environ.get("ROLE", "unknown")
        return (
            f"Standup from {role}:\n"
            f"Yesterday: {arguments['yesterday']}\n"
            f"Today: {arguments['today']}\n"
            f"Blockers: {arguments.get('blockers', 'None')}"
        )
