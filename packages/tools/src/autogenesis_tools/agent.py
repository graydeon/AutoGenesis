"""Sub-agent tool (stub)."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class SubAgentTool(Tool):
    """Stub sub-agent tool. Hidden until v0.3.0."""

    @property
    def name(self) -> str:
        return "sub_agent"

    @property
    def description(self) -> str:
        return "Delegate a task to a sub-agent."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task to delegate"},
            },
            "required": ["task"],
        }

    @property
    def hidden(self) -> bool:
        return True

    async def execute(self, arguments: dict[str, Any]) -> str:  # noqa: ARG002
        """Not implemented — returns error string."""
        return "Error: Sub-agent support coming in v0.3.0"
