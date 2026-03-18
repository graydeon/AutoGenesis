"""Tests for plugin interface."""

from __future__ import annotations

import pytest
from autogenesis_plugins.interface import Plugin, PluginManifest


class TestPluginManifest:
    def test_valid_manifest(self):
        m = PluginManifest(name="test-plugin", version="1.0.0")
        assert m.name == "test-plugin"
        assert m.token_budget == 500

    def test_manifest_with_permissions(self):
        m = PluginManifest(
            name="test",
            version="1.0.0",
            permissions=["bash", "file_read"],
            token_budget=1000,
        )
        assert len(m.permissions) == 2

    def test_manifest_serialization(self):
        m = PluginManifest(name="test", version="1.0.0")
        data = m.model_dump()
        restored = PluginManifest.model_validate(data)
        assert restored.name == m.name


class TestPluginABC:
    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            Plugin()

    def test_concrete_subclass(self):
        class TestPlugin(Plugin):
            @property
            def manifest(self):
                return PluginManifest(name="test", version="1.0.0")

            def get_tools(self):
                return []

        p = TestPlugin()
        assert p.manifest.name == "test"
        assert p.get_tools() == []
