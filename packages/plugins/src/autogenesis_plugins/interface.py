"""Plugin ABC and manifest schema."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class PluginManifest(BaseModel):
    """Plugin metadata and requirements."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    permissions: list[str] = Field(default_factory=list)
    token_budget: int = 500
    dependencies: list[str] = Field(default_factory=list)


class Plugin(ABC):
    """Abstract base for plugins."""

    @property
    @abstractmethod
    def manifest(self) -> PluginManifest:
        """Return the plugin manifest."""

    @abstractmethod
    def get_tools(self) -> list[Any]:
        """Return tools provided by this plugin."""

    def on_load(self) -> None:  # noqa: B027
        """Run setup when plugin is loaded. Override in subclass."""

    def on_unload(self) -> None:  # noqa: B027
        """Run cleanup when plugin is unloaded. Override in subclass."""
