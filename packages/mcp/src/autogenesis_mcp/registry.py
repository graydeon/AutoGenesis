"""MCP server discovery and management."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autogenesis_core.config import MCPConfig

    from autogenesis_mcp.client import MCPClient

logger = structlog.get_logger()


class MCPRegistry:
    """Registry of MCP servers with allowlist enforcement and connection pooling."""

    def __init__(self, config: MCPConfig | None = None) -> None:
        self._allowlist: set[str] = set()
        self._servers: dict[str, dict[str, Any]] = {}
        self._clients: dict[str, MCPClient] = {}

        if config:
            self._allowlist = set(config.allowlist)
            self._servers = dict(config.servers)

    @property
    def allowlist(self) -> set[str]:
        """Current server allowlist."""
        return self._allowlist.copy()

    def is_allowed(self, server_name: str) -> bool:
        """Check if a server is on the allowlist."""
        if not self._allowlist:
            return True  # No allowlist = allow all
        return server_name in self._allowlist

    def register_server(self, name: str, config: dict[str, Any]) -> None:
        """Register a server configuration."""
        self._servers[name] = config

    def list_servers(self) -> list[str]:
        """List registered server names."""
        return list(self._servers.keys())

    def get_server_config(self, name: str) -> dict[str, Any] | None:
        """Get configuration for a server."""
        return self._servers.get(name)

    async def connect(self, server_name: str) -> MCPClient:
        """Connect to a server, returning pooled client if available."""
        if not self.is_allowed(server_name):
            msg = f"Server {server_name!r} not in allowlist"
            raise PermissionError(msg)

        # Return pooled client if connected
        if server_name in self._clients and self._clients[server_name].connected:
            return self._clients[server_name]

        config = self._servers.get(server_name)
        if not config:
            msg = f"Server {server_name!r} not registered"
            raise KeyError(msg)

        from autogenesis_mcp.client import MCPClient

        client = MCPClient(
            server_name=server_name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
        )

        await client.connect()
        self._clients[server_name] = client
        logger.info("mcp_server_connected", server=server_name)
        return client

    async def disconnect(self, server_name: str) -> None:
        """Disconnect from a server."""
        client = self._clients.pop(server_name, None)
        if client:
            await client.disconnect()

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for name in list(self._clients.keys()):
            await self.disconnect(name)

    async def health_check(self, server_name: str) -> bool:
        """Check if a server is healthy by listing tools."""
        try:
            client = await self.connect(server_name)
            await client.list_tools()
        except Exception:  # noqa: BLE001
            return False
        else:
            return True
