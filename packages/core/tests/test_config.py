"""Tests for configuration system."""

from __future__ import annotations

from autogenesis_core.config import (
    AutoGenesisConfig,
    CodexConfig,
    CredentialProviderType,
    EmployeesConfig,
    TwitterConfig,
    load_config,
)


class TestCodexConfig:
    def test_defaults(self):
        cfg = CodexConfig()
        assert cfg.model == "gpt-5.3-codex"
        assert cfg.api_base_url == "https://api.openai.com/v1"

    def test_custom_model(self):
        cfg = CodexConfig(model="gpt-5.4")
        assert cfg.model == "gpt-5.4"


class TestAutoGenesisConfig:
    def test_defaults(self):
        cfg = AutoGenesisConfig()
        assert isinstance(cfg.codex, CodexConfig)
        assert cfg.credential_provider == CredentialProviderType.ENV

    def test_serialization_roundtrip(self):
        cfg = AutoGenesisConfig()
        data = cfg.model_dump()
        restored = AutoGenesisConfig.model_validate(data)
        assert restored.codex.model == cfg.codex.model

    def test_no_tier_config(self):
        """TierConfig and ModelConfig are removed."""
        cfg = AutoGenesisConfig()
        assert not hasattr(cfg, "models")


class TestTwitterConfig:
    def test_defaults(self):
        cfg = TwitterConfig()
        assert cfg.enabled is False
        assert cfg.active_hours_start == "09:00"
        assert cfg.gateway_url == "http://127.0.0.1:1456"

    def test_in_root_config(self):
        cfg = AutoGenesisConfig()
        assert isinstance(cfg.twitter, TwitterConfig)
        assert cfg.twitter.enabled is False

    def test_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("AUTOGENESIS_TWITTER__ENABLED", "true")
        cfg = load_config()
        assert cfg.twitter.enabled is True


class TestEmployeesConfig:
    def test_defaults(self):
        cfg = EmployeesConfig()
        assert cfg.enabled is False
        assert cfg.standup_enabled is True
        assert cfg.brain_memory_limit == 1000

    def test_in_root_config(self):
        cfg = AutoGenesisConfig()
        assert isinstance(cfg.employees, EmployeesConfig)


class TestLoadConfig:
    def test_returns_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.delenv("AUTOGENESIS_CODEX__MODEL", raising=False)
        cfg = load_config()
        assert isinstance(cfg, AutoGenesisConfig)

    def test_env_override(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        monkeypatch.setenv("AUTOGENESIS_CODEX__MODEL", "gpt-5.4")
        cfg = load_config()
        assert cfg.codex.model == "gpt-5.4"
