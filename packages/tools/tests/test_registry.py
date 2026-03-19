"""Tests for tool registry with progressive disclosure."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool
from autogenesis_tools.registry import ToolRegistry


class FakeTool(Tool):
    def __init__(self, name: str, *, hidden: bool = False, cost: int = 100) -> None:
        self._name = name
        self._hidden = hidden
        self._cost = cost

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return f"Fake tool: {self._name}"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object"}

    @property
    def hidden(self) -> bool:
        return self._hidden

    @property
    def token_cost_estimate(self) -> int:
        return self._cost

    async def execute(self, arguments: dict[str, Any]) -> str:
        return "ok"


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        tool = FakeTool("bash")
        registry.register(tool)
        assert registry.get("bash") is tool
        assert registry.get("nonexistent") is None

    def test_list_names(self):
        registry = ToolRegistry()
        registry.register(FakeTool("bash"))
        registry.register(FakeTool("file_read"))
        names = registry.list_names()
        assert "bash" in names
        assert "file_read" in names

    def test_progressive_disclosure_budget(self):
        registry = ToolRegistry()
        for i in range(20):
            registry.register(FakeTool(f"tool_{i}", cost=100))
        defs = registry.get_definitions_for_context(token_budget=500)
        assert len(defs) <= 5

    def test_required_tools_always_included(self):
        registry = ToolRegistry()
        registry.register(FakeTool("bash", cost=100))
        registry.register(FakeTool("important", cost=100))
        defs = registry.get_definitions_for_context(
            token_budget=50,
            required_tools=["important"],
        )
        names = [d.name for d in defs]
        assert "important" in names

    def test_hidden_tools_excluded(self):
        registry = ToolRegistry()
        registry.register(FakeTool("visible", cost=100))
        registry.register(FakeTool("hidden_tool", hidden=True, cost=100))
        defs = registry.get_definitions_for_context(token_budget=10_000)
        names = [d.name for d in defs]
        assert "visible" in names
        assert "hidden_tool" not in names

    def test_usage_frequency_priority(self):
        registry = ToolRegistry()
        registry.register(FakeTool("rarely_used", cost=100))
        registry.register(FakeTool("often_used", cost=100))
        for _ in range(10):
            registry.record_usage("often_used")
        defs = registry.get_definitions_for_context(token_budget=150)
        names = [d.name for d in defs]
        assert "often_used" in names

    def test_empty_registry(self):
        registry = ToolRegistry()
        defs = registry.get_definitions_for_context()
        assert defs == []
