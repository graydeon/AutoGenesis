"""Tests for MCP client."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_mcp.client import MCPClient, _substitute_env_vars


class TestEnvVarSubstitution:
    def test_substitutes_env_var(self, monkeypatch):
        monkeypatch.setenv("MY_TOKEN", "secret123")
        assert _substitute_env_vars("Bearer ${MY_TOKEN}") == "Bearer secret123"

    def test_unset_var_preserved(self):
        result = _substitute_env_vars("${DOES_NOT_EXIST_XYZ}")
        assert result == "${DOES_NOT_EXIST_XYZ}"

    def test_no_vars_unchanged(self):
        assert _substitute_env_vars("plain text") == "plain text"

    def test_multiple_vars(self, monkeypatch):
        monkeypatch.setenv("HOST", "localhost")
        monkeypatch.setenv("PORT", "8080")
        assert _substitute_env_vars("${HOST}:${PORT}") == "localhost:8080"


class TestMCPClient:
    def test_init_substitutes_env(self, monkeypatch):
        monkeypatch.setenv("MCP_CMD", "/usr/bin/node")
        client = MCPClient(
            server_name="test",
            command="${MCP_CMD}",
            args=["--port", "${MCP_CMD}"],
        )
        assert client._command == "/usr/bin/node"
        assert client._args[1] == "/usr/bin/node"

    def test_not_connected_by_default(self):
        client = MCPClient()
        assert client.connected is False

    async def test_list_tools_when_disconnected(self):
        client = MCPClient()
        with pytest.raises(ConnectionError, match="Not connected"):
            await client.list_tools()

    async def test_call_tool_when_disconnected(self):
        client = MCPClient()
        with pytest.raises(ConnectionError, match="Not connected"):
            await client.call_tool(tool="test")

    async def test_list_tools_returns_tool_info(self):
        client = MCPClient(server_name="test")
        client._connected = True

        mock_tool = MagicMock()
        mock_tool.name = "echo"
        mock_tool.description = "Echo input"
        mock_tool.inputSchema = {"type": "object"}

        mock_result = MagicMock()
        mock_result.tools = [mock_tool]

        client._session = MagicMock()
        client._session.list_tools = AsyncMock(return_value=mock_result)

        tools = await client.list_tools()

        assert len(tools) == 1
        assert tools[0]["name"] == "echo"
        assert tools[0]["description"] == "Echo input"

    async def test_call_tool_returns_text(self):
        client = MCPClient(server_name="test")
        client._connected = True

        mock_content = MagicMock()
        mock_content.text = "Hello World"
        mock_result = MagicMock()
        mock_result.content = [mock_content]

        client._session = MagicMock()
        client._session.call_tool = AsyncMock(return_value=mock_result)

        result = await client.call_tool(tool="echo", arguments={"text": "Hello"})

        assert result == "Hello World"

    async def test_disconnect_when_not_connected(self):
        client = MCPClient()
        await client.disconnect()  # Should not raise
        assert client.connected is False
