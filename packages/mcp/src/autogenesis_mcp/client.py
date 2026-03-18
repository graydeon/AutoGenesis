"""MCP client for external tool consumption."""

from __future__ import annotations

import os
import re
from typing import Any

import structlog

logger = structlog.get_logger()

# Regex for ${ENV_VAR} substitution
_ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _substitute_env_vars(value: str) -> str:
    """Replace ${VAR} patterns with environment variable values."""

    def _replacer(match: re.Match[str]) -> str:
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return _ENV_VAR_PATTERN.sub(_replacer, value)


class MCPClient:
    """Client for connecting to MCP servers."""

    def __init__(
        self,
        server_name: str = "",
        command: str = "",
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self._server_name = server_name
        self._command = _substitute_env_vars(command)
        self._args = [_substitute_env_vars(a) for a in (args or [])]
        self._env = {k: _substitute_env_vars(v) for k, v in (env or {}).items()}
        self._connected = False
        self._tools: dict[str, dict[str, Any]] = {}
        self._session: Any = None

    @property
    def connected(self) -> bool:
        """Whether the client is currently connected."""
        return self._connected

    async def connect(self) -> None:
        """Connect to the MCP server via stdio transport."""
        if self._connected:
            return

        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client

            server_params = StdioServerParameters(
                command=self._command,
                args=self._args,
                env={**os.environ, **self._env} if self._env else None,
            )

            self._stdio_context = stdio_client(server_params)
            read, write = await self._stdio_context.__aenter__()

            self._session = ClientSession(read, write)
            await self._session.__aenter__()
            await self._session.initialize()

            self._connected = True
            logger.info("mcp_connected", server=self._server_name)
        except Exception as exc:
            logger.warning("mcp_connect_failed", server=self._server_name, error=str(exc))
            raise

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if not self._connected:
            return

        try:
            if self._session:
                await self._session.__aexit__(None, None, None)
            if hasattr(self, "_stdio_context"):
                await self._stdio_context.__aexit__(None, None, None)
        except Exception:  # noqa: BLE001
            logger.warning("mcp_disconnect_error", server=self._server_name)
        finally:
            self._connected = False
            self._session = None
            self._tools = {}

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the connected server."""
        if not self._connected or not self._session:
            msg = "Not connected"
            raise ConnectionError(msg)

        result = await self._session.list_tools()
        tools = []
        for tool in result.tools:
            tool_info = {
                "name": tool.name,
                "description": getattr(tool, "description", ""),
                "input_schema": getattr(tool, "inputSchema", {}),
            }
            self._tools[tool.name] = tool_info
            tools.append(tool_info)
        return tools

    async def call_tool(
        self,
        tool: str = "",
        arguments: dict[str, Any] | None = None,
        *,
        server: str = "",  # noqa: ARG002
    ) -> str:
        """Call a tool on the connected server."""
        if not self._connected or not self._session:
            msg = "Not connected"
            raise ConnectionError(msg)

        result = await self._session.call_tool(tool, arguments=arguments or {})

        # Extract text content from result
        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
            else:
                parts.append(str(content))
        return "\n".join(parts)
