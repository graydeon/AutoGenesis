"""Plugin discovery and loading."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from autogenesis_plugins.interface import Plugin, PluginManifest

logger = structlog.get_logger()


class PluginLoader:
    """Discover, validate, and load plugins."""

    def __init__(
        self,
        allowed_permissions: set[str] | None = None,
        max_token_budget: int = 5000,
    ) -> None:
        self._allowed_permissions = allowed_permissions
        self._max_token_budget = max_token_budget
        self._plugins: dict[str, Plugin] = {}

    def validate_manifest(self, manifest: PluginManifest) -> tuple[bool, str]:
        """Validate a plugin manifest."""
        if not manifest.name:
            return (False, "Plugin name is required")
        if not manifest.version:
            return (False, "Plugin version is required")
        if manifest.token_budget > self._max_token_budget:
            return (
                False,
                f"Token budget {manifest.token_budget} exceeds max {self._max_token_budget}",
            )
        if self._allowed_permissions is not None:
            for perm in manifest.permissions:
                if perm not in self._allowed_permissions:
                    return (False, f"Permission {perm!r} not allowed")
        return (True, "")

    def load(self, plugin: Plugin) -> bool:
        """Load a plugin after validation."""
        manifest = plugin.manifest
        valid, reason = self.validate_manifest(manifest)
        if not valid:
            logger.warning("plugin_rejected", name=manifest.name, reason=reason)
            return False

        plugin.on_load()
        self._plugins[manifest.name] = plugin
        logger.info("plugin_loaded", name=manifest.name, version=manifest.version)
        return True

    def unload(self, name: str) -> bool:
        """Unload a plugin by name."""
        plugin = self._plugins.pop(name, None)
        if plugin is None:
            return False
        plugin.on_unload()
        logger.info("plugin_unloaded", name=name)
        return True

    def list_plugins(self) -> list[dict[str, Any]]:
        """List loaded plugins."""
        return [
            {
                "name": p.manifest.name,
                "version": p.manifest.version,
                "description": p.manifest.description,
                "tools": len(p.get_tools()),
            }
            for p in self._plugins.values()
        ]

    def get_all_tools(self) -> list[Any]:
        """Get all tools from all loaded plugins."""
        tools: list[Any] = []
        for plugin in self._plugins.values():
            tools.extend(plugin.get_tools())
        return tools
