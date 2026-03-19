"""Tool registry with progressive disclosure."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from autogenesis_core.models import ToolDefinition

    from autogenesis_tools.base import Tool

logger = structlog.get_logger()


class ToolRegistry:
    """Registry of available tools with progressive disclosure.

    Progressive disclosure: only include tool definitions that fit within
    the token budget, prioritizing by frequency of use and relevance.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._usage_counts: dict[str, int] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool."""
        self._tools[tool.name] = tool
        self._usage_counts.setdefault(tool.name, 0)

    def get(self, name: str) -> Tool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_names(self) -> list[str]:
        """List all registered tool names."""
        return list(self._tools.keys())

    def record_usage(self, name: str) -> None:
        """Record that a tool was used (for progressive disclosure)."""
        if name in self._usage_counts:
            self._usage_counts[name] += 1

    def get_definitions_for_context(
        self,
        token_budget: int = 10_000,
        required_tools: list[str] | None = None,
    ) -> list[ToolDefinition]:
        """Get tool definitions that fit within token budget.

        Progressive disclosure: required tools always included, then
        sorted by usage frequency. Hidden tools excluded.
        """
        required = set(required_tools or [])
        definitions: list[ToolDefinition] = []
        remaining_budget = token_budget

        # Sort tools: required first, then by usage count (descending)
        sorted_tools = sorted(
            self._tools.values(),
            key=lambda t: (
                t.name not in required,  # required first (False < True)
                -self._usage_counts.get(t.name, 0),  # then by usage
            ),
        )

        for tool in sorted_tools:
            # Skip hidden tools
            if tool.hidden and tool.name not in required:
                continue

            defn = tool.to_definition()
            cost = defn.token_cost_estimate or 100  # default estimate

            # Required tools always included regardless of budget
            if tool.name in required:
                definitions.append(defn)
                remaining_budget -= cost
                continue

            # Budget check for non-required tools
            if remaining_budget - cost < 0:
                continue

            definitions.append(defn)
            remaining_budget -= cost

        logger.debug(
            "progressive_disclosure",
            total_tools=len(self._tools),
            included=len(definitions),
            budget_remaining=remaining_budget,
        )
        return definitions
