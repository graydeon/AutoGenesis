"""Token usage reporting."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from autogenesis_core.models import TokenUsage


class TokenReporter:
    """Aggregate and report token usage data."""

    def __init__(self) -> None:
        self._session_usage: list[dict[str, Any]] = []
        self._tool_usage: dict[str, dict[str, int]] = {}

    def record(
        self,
        usage: TokenUsage,
        model: str = "",
        tool: str | None = None,
    ) -> None:
        """Record a usage entry."""
        entry = {
            "model": model,
            "input_tokens": usage.input_tokens,
            "output_tokens": usage.output_tokens,
            "total_tokens": usage.total_tokens,
        }
        self._session_usage.append(entry)

        if tool:
            self._tool_usage.setdefault(tool, {"calls": 0, "tokens": 0})
            self._tool_usage[tool]["calls"] += 1
            self._tool_usage[tool]["tokens"] += usage.total_tokens

    def summary(self) -> dict[str, Any]:
        """Return per-session summary."""
        total_input = sum(e["input_tokens"] for e in self._session_usage)
        total_output = sum(e["output_tokens"] for e in self._session_usage)
        return {
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "api_calls": len(self._session_usage),
        }

    def tool_breakdown(self) -> dict[str, dict[str, int]]:
        """Return per-tool usage breakdown."""
        return dict(self._tool_usage)

    def to_json(self) -> str:
        """Export report as JSON string."""
        return json.dumps(
            {
                "summary": self.summary(),
                "tool_breakdown": self.tool_breakdown(),
                "entries": self._session_usage,
            },
            indent=2,
        )
