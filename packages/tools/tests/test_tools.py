"""Tests for think and agent tools."""

from __future__ import annotations

from typing import Any

from autogenesis_core.models import ToolCall
from autogenesis_tools.agent import SubAgentTool
from autogenesis_tools.base import Tool
from autogenesis_tools.think import ThinkTool


class FakeTool(Tool):
    @property
    def name(self) -> str:
        return "fake"

    @property
    def description(self) -> str:
        return "A fake tool"

    @property
    def parameters(self) -> dict[str, Any]:
        return {"type": "object", "properties": {}}

    async def execute(self, arguments: dict[str, Any]) -> str:
        return "ok"


class TestThinkTool:
    async def test_think_returns_empty(self):
        tool = ThinkTool()
        tc = ToolCall(name="think", arguments={"thought": "Let me reason about this"})
        result = await tool(tc)
        assert result == ""

    async def test_think_definition(self):
        tool = ThinkTool()
        defn = tool.to_definition()
        assert defn.name == "think"


class TestSubAgentTool:
    async def test_sub_agent_not_configured(self):
        tool = SubAgentTool()
        tc = ToolCall(name="sub_agent", arguments={"task": "do something"})
        result = await tool(tc)
        assert "not configured" in result.lower() or "error" in result.lower()


class TestToolResponsesFormat:
    def test_format_structure(self):
        """Tool.to_responses_api_format() returns Responses API tool schema."""
        tool = FakeTool()
        fmt = tool.to_responses_api_format()
        assert fmt["type"] == "function"
        assert fmt["name"] == tool.name
        assert fmt["description"] == tool.description
        assert "parameters" in fmt

    def test_no_tier_requirement(self):
        """tier_requirement property is removed."""
        tool = FakeTool()
        assert not hasattr(tool, "tier_requirement")
