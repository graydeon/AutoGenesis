"""Web fetch and think tools."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class ThinkTool(Tool):
    """No-op tool for model reasoning. Content stays in context."""

    @property
    def name(self) -> str:
        return "think"

    @property
    def description(self) -> str:
        return "Use this to think through complex problems. Content stays in context."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "thought": {"type": "string", "description": "Your reasoning"},
            },
            "required": ["thought"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 80

    async def execute(self, arguments: dict[str, Any]) -> str:  # noqa: ARG002
        """No-op — thought is captured in context via tool call."""
        return ""


class WebFetchTool(Tool):
    """Fetch a URL and return content as text. Disabled by default."""

    @property
    def name(self) -> str:
        return "web_fetch"

    @property
    def description(self) -> str:
        return "Fetch a URL and return its content as text."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to fetch"},
            },
            "required": ["url"],
        }

    @property
    def hidden(self) -> bool:
        return True

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:  # noqa: ARG002
        """Fetch URL content."""
        return "Error: web_fetch is disabled. Enable in config: security.tools.web_fetch.enabled"
