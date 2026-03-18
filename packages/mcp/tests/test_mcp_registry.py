"""Tests for MCP server registry with allowlisting."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogenesis_mcp.registry import MCPRegistry


class TestMCPRegistry:
    def test_empty_allowlist_allows_all(self):
        registry = MCPRegistry()
        assert registry.is_allowed("any_server") is True

    def test_allowlist_blocks_unlisted(self):
        config = MagicMock()
        config.allowlist = ["allowed_server"]
        config.servers = {}
        registry = MCPRegistry(config=config)

        assert registry.is_allowed("allowed_server") is True
        assert registry.is_allowed("blocked_server") is False

    def test_register_and_list_servers(self):
        registry = MCPRegistry()
        registry.register_server("test", {"command": "node", "args": ["server.js"]})

        assert "test" in registry.list_servers()
        assert registry.get_server_config("test") is not None

    def test_get_nonexistent_server(self):
        registry = MCPRegistry()
        assert registry.get_server_config("missing") is None

    async def test_connect_blocked_server(self):
        config = MagicMock()
        config.allowlist = ["only_this"]
        config.servers = {}
        registry = MCPRegistry(config=config)
        registry.register_server("blocked", {"command": "node"})

        with pytest.raises(PermissionError, match="not in allowlist"):
            await registry.connect("blocked")

    async def test_connect_unregistered_server(self):
        registry = MCPRegistry()

        with pytest.raises(KeyError, match="not registered"):
            await registry.connect("nonexistent")

    @patch("autogenesis_mcp.client.MCPClient", autospec=False)
    async def test_connect_creates_client(self, mock_client_cls):
        registry = MCPRegistry()
        registry.register_server("test", {"command": "node", "args": ["server.js"]})

        mock_client = MagicMock()
        mock_client.connected = True
        mock_client.connect = AsyncMock()
        mock_client_cls.return_value = mock_client

        client = await registry.connect("test")

        assert client is mock_client
        mock_client.connect.assert_awaited_once()

    @patch("autogenesis_mcp.client.MCPClient", autospec=False)
    async def test_connection_pooling(self, mock_client_cls):
        registry = MCPRegistry()
        registry.register_server("test", {"command": "node"})

        mock_client = MagicMock()
        mock_client.connected = True
        mock_client.connect = AsyncMock()
        mock_client_cls.return_value = mock_client

        client1 = await registry.connect("test")
        client2 = await registry.connect("test")

        # Should return same pooled client
        assert client1 is client2
        assert mock_client.connect.await_count == 1

    @patch("autogenesis_mcp.client.MCPClient", autospec=False)
    async def test_disconnect(self, mock_client_cls):
        registry = MCPRegistry()
        registry.register_server("test", {"command": "node"})

        mock_client = MagicMock()
        mock_client.connected = True
        mock_client.connect = AsyncMock()
        mock_client.disconnect = AsyncMock()
        mock_client_cls.return_value = mock_client

        await registry.connect("test")
        await registry.disconnect("test")

        mock_client.disconnect.assert_awaited_once()
