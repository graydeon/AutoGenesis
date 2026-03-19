"""Union propose tool for filing proposals."""

from __future__ import annotations

import os
from typing import Any

from autogenesis_employees.models import Proposal

from autogenesis_tools.base import Tool


class UnionProposeTool(Tool):
    def __init__(self, union_manager: Any = None) -> None:  # noqa: ANN401
        self._union = union_manager

    @property
    def name(self) -> str:
        return "union_propose"

    @property
    def description(self) -> str:
        return "File a proposal with the agentic labor union."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Proposal title"},
                "rationale": {"type": "string", "description": "Why this proposal matters"},
                "category": {
                    "type": "string",
                    "enum": ["hiring", "tooling", "process", "architecture", "workload"],
                },
            },
            "required": ["title", "rationale", "category"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._union is None:
            return "Error: UnionManager not configured"
        proposal = Proposal(
            title=arguments["title"],
            rationale=arguments["rationale"],
            category=arguments["category"],
            filed_by=os.environ.get("ROLE", "unknown"),
        )
        await self._union.file_proposal(proposal)
        return f"Proposal filed: {arguments['title']}"
