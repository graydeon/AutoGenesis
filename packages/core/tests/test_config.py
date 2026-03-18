"""Tests for XDG-compliant configuration system."""

from __future__ import annotations

import yaml
from autogenesis_core.config import (
    AutoGenesisConfig,
    ModelConfig,
    load_config,
)


class TestAutoGenesisConfig:
    def test_default_config(self):
        config = AutoGenesisConfig()
        assert config.models is not None
        assert config.tokens is not None
        assert config.security is not None
        assert config.models.default_tier == "standard"

    def test_from_yaml(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)  # avoid picking up repo's .autogenesis/
        config_file = tmp_path / "config.yaml"
        config_file.write_text(yaml.dump({"models": {"default_tier": "premium"}}))
        config = load_config(config_path=config_file)
        assert config.models.default_tier == "premium"

    def test_env_var_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("AUTOGENESIS_MODELS__DEFAULT_TIER", "fast")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config = load_config()
        assert config.models.default_tier == "fast"

    def test_config_precedence(self, tmp_path, monkeypatch):
        user_config = tmp_path / "config" / "autogenesis" / "config.yaml"
        user_config.parent.mkdir(parents=True)
        user_config.write_text(yaml.dump({"models": {"default_tier": "standard"}}))
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))

        project_config = tmp_path / "project" / ".autogenesis" / "config.yaml"
        project_config.parent.mkdir(parents=True)
        project_config.write_text(yaml.dump({"models": {"default_tier": "premium"}}))

        config = load_config(project_path=project_config)
        assert config.models.default_tier == "premium"

    def test_model_config_defaults(self):
        mc = ModelConfig()
        assert mc.default_tier == "standard"
        assert "fast" in mc.tiers
        assert "standard" in mc.tiers
        assert "premium" in mc.tiers

    def test_config_serialization(self):
        config = AutoGenesisConfig()
        data = config.model_dump()
        restored = AutoGenesisConfig.model_validate(data)
        assert restored.models.default_tier == config.models.default_tier

    def test_token_config_defaults(self):
        config = AutoGenesisConfig()
        assert config.tokens.max_tokens_per_session == 100_000
        assert config.tokens.max_cost_per_session == 5.0

    def test_security_config_defaults(self):
        config = AutoGenesisConfig()
        assert config.security.guardrails_enabled is True
        assert config.security.sandbox_provider == "subprocess"

    def test_empty_yaml_returns_defaults(self, tmp_path):
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")
        config = load_config(config_path=config_file)
        assert config.models.default_tier == "standard"
