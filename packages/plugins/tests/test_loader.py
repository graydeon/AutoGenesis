"""Tests for plugin loader."""

from __future__ import annotations

from autogenesis_plugins.interface import Plugin, PluginManifest
from autogenesis_plugins.loader import PluginLoader


class FakePlugin(Plugin):
    def __init__(self, name: str = "fake", version: str = "1.0.0", **kwargs) -> None:
        self._manifest = PluginManifest(name=name, version=version, **kwargs)
        self._loaded = False

    @property
    def manifest(self) -> PluginManifest:
        return self._manifest

    def get_tools(self) -> list:
        return ["tool1", "tool2"]

    def on_load(self) -> None:
        self._loaded = True

    def on_unload(self) -> None:
        self._loaded = False


class TestPluginLoader:
    def test_load_valid_plugin(self):
        loader = PluginLoader()
        plugin = FakePlugin()
        assert loader.load(plugin) is True
        assert len(loader.list_plugins()) == 1

    def test_reject_invalid_manifest(self):
        loader = PluginLoader()
        plugin = FakePlugin(name="", version="1.0.0")
        assert loader.load(plugin) is False

    def test_reject_excessive_token_budget(self):
        loader = PluginLoader(max_token_budget=100)
        plugin = FakePlugin(token_budget=500)
        assert loader.load(plugin) is False

    def test_reject_disallowed_permissions(self):
        loader = PluginLoader(allowed_permissions={"file_read"})
        plugin = FakePlugin(permissions=["bash", "file_read"])
        assert loader.load(plugin) is False

    def test_allowed_permissions(self):
        loader = PluginLoader(allowed_permissions={"bash", "file_read"})
        plugin = FakePlugin(permissions=["bash"])
        assert loader.load(plugin) is True

    def test_unload_plugin(self):
        loader = PluginLoader()
        plugin = FakePlugin()
        loader.load(plugin)
        assert loader.unload("fake") is True
        assert len(loader.list_plugins()) == 0

    def test_list_installed_plugins(self):
        loader = PluginLoader()
        loader.load(FakePlugin(name="a"))
        loader.load(FakePlugin(name="b"))

        plugins = loader.list_plugins()
        names = [p["name"] for p in plugins]
        assert "a" in names
        assert "b" in names

    def test_get_all_tools(self):
        loader = PluginLoader()
        loader.load(FakePlugin(name="a"))
        loader.load(FakePlugin(name="b"))

        tools = loader.get_all_tools()
        assert len(tools) == 4  # 2 tools per plugin
