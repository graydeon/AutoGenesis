"""Brain memory tools for employee agents."""

from __future__ import annotations

import os
from typing import Any

from autogenesis_employees.models import Memory

from autogenesis_tools.base import Tool


class BrainWriteTool(Tool):
    def __init__(self, brain_manager: Any = None) -> None:  # noqa: ANN401
        self._brain = brain_manager

    @property
    def name(self) -> str:
        return "brain_write"

    @property
    def description(self) -> str:
        return "Store a memory in your persistent brain. Memories persist across sessions."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["decision", "pattern", "note", "context"],
                    "description": "Memory category",
                },
                "content": {"type": "string", "description": "What to remember"},
            },
            "required": ["category", "content"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._brain is None:
            return "Error: BrainManager not configured"
        memory = Memory(
            category=arguments["category"],
            content=arguments["content"],
            source=os.environ.get("ROLE", "unknown"),
            project="current",
        )
        await self._brain.write(memory)
        return f"Memory stored: {arguments['content'][:50]}..."


class BrainRecallTool(Tool):
    def __init__(self, brain_manager: Any = None) -> None:  # noqa: ANN401
        self._brain = brain_manager

    @property
    def name(self) -> str:
        return "brain_recall"

    @property
    def description(self) -> str:
        return "Search your persistent memory for relevant information."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)"},
            },
            "required": ["query"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._brain is None:
            return "Error: BrainManager not configured"
        results = await self._brain.recall(arguments["query"], limit=arguments.get("limit", 5))
        if not results:
            return "No matching memories found."
        return "\n".join(f"- [{r.category}] {r.content}" for r in results)
