"""MCP tool invocation."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class MCPCallTool(Tool):
    """Invoke a tool on an MCP server."""

    @property
    def name(self) -> str:
        return "mcp_call"

    @property
    def description(self) -> str:
        return "Call a tool on a connected MCP server."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {"type": "string", "description": "MCP server name"},
                "tool": {"type": "string", "description": "Tool name on the server"},
                "arguments": {"type": "object", "description": "Tool arguments"},
            },
            "required": ["server", "tool"],
        }

    @property
    def hidden(self) -> bool:
        return True

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Invoke MCP tool via lazy import of MCP client."""
        try:
            from autogenesis_mcp.client import MCPClient  # type: ignore[attr-defined]
        except ImportError:
            return "Error: MCP package not available"

        server_name = arguments["server"]
        tool_name = arguments["tool"]
        tool_args = arguments.get("arguments", {})

        client = MCPClient()
        result: str = await client.call_tool(
            server=server_name,
            tool=tool_name,
            arguments=tool_args,
        )
        return result
