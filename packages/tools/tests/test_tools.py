"""Tests for web, think, agent, interactive, and mcp tools."""

from __future__ import annotations

from autogenesis_core.models import ToolCall
from autogenesis_tools.agent import SubAgentTool
from autogenesis_tools.web import ThinkTool, WebFetchTool


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
        assert defn.hidden is False


class TestWebFetchTool:
    async def test_web_fetch_disabled(self):
        tool = WebFetchTool()
        tc = ToolCall(name="web_fetch", arguments={"url": "https://example.com"})
        result = await tool(tc)
        assert "disabled" in result.lower()

    async def test_web_fetch_hidden(self):
        tool = WebFetchTool()
        assert tool.hidden is True


class TestSubAgentTool:
    async def test_sub_agent_returns_error(self):
        tool = SubAgentTool()
        tc = ToolCall(name="sub_agent", arguments={"task": "do something"})
        result = await tool(tc)
        assert "v0.3.0" in result

    async def test_sub_agent_hidden(self):
        tool = SubAgentTool()
        assert tool.hidden is True
