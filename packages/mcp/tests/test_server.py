"""Tests for MCP server."""

from __future__ import annotations

from autogenesis_mcp.server import (
    autogenesis_optimize,
    autogenesis_run,
    autogenesis_scan,
    autogenesis_tokens_report,
    mcp_server,
)


class TestMCPServer:
    def test_server_has_name(self):
        assert mcp_server.name == "autogenesis"

    async def test_autogenesis_run(self):
        result = await autogenesis_run(prompt="Hello", tier="fast")
        assert "Hello" in result
        assert "fast" in result

    async def test_autogenesis_optimize(self):
        result = await autogenesis_optimize(prompt_name="core")
        assert "core" in result

    async def test_autogenesis_tokens_report(self):
        result = await autogenesis_tokens_report(session_id="abc123")
        assert "abc123" in result

    async def test_autogenesis_scan(self):
        result = await autogenesis_scan(path="/home/user/project")
        assert "/home/user/project" in result

    async def test_server_tools_registered(self):
        # FastMCP registers tools, verify they exist
        tools = await mcp_server.list_tools()
        tool_names = [t.name for t in tools]
        assert "autogenesis_run" in tool_names
        assert "autogenesis_optimize" in tool_names
        assert "autogenesis_tokens_report" in tool_names
        assert "autogenesis_scan" in tool_names
