"""Tool and MCP server allowlisting."""

from __future__ import annotations

import hashlib
from typing import Any


class ToolAllowlist:
    """Control which tools are allowed to execute."""

    def __init__(self, allowed: list[str] | None = None) -> None:
        self._allowed = set(allowed) if allowed else None  # None = allow all

    def is_allowed(self, tool_name: str) -> bool:
        if self._allowed is None:
            return True
        return tool_name in self._allowed

    def add(self, tool_name: str) -> None:
        if self._allowed is None:
            self._allowed = set()
        self._allowed.add(tool_name)


class MCPAllowlist:
    """Control which MCP servers are allowed with optional hash pinning."""

    def __init__(
        self,
        allowed: list[str] | None = None,
        pinned_hashes: dict[str, str] | None = None,
    ) -> None:
        self._allowed = set(allowed) if allowed else None
        self._pinned = pinned_hashes or {}

    def is_allowed(self, server_name: str) -> bool:
        if self._allowed is None:
            return True
        return server_name in self._allowed

    def verify_hash(self, server_name: str, server_config: dict[str, Any]) -> bool:
        """Verify server config hash matches pinned value."""
        if server_name not in self._pinned:
            return True  # No pin = no check
        config_str = str(sorted(server_config.items()))
        current_hash = hashlib.sha256(config_str.encode()).hexdigest()
        return current_hash == self._pinned[server_name]

    def pin(self, server_name: str, server_config: dict[str, Any]) -> str:
        """Pin a server's configuration hash."""
        config_str = str(sorted(server_config.items()))
        hash_val = hashlib.sha256(config_str.encode()).hexdigest()
        self._pinned[server_name] = hash_val
        return hash_val
