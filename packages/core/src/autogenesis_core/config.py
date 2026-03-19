"""Configuration system for AutoGenesis.

6-layer cascade: defaults → system → user → project → env → CLI flags.
XDG Base Directory compliant.
"""

from __future__ import annotations

import os
from enum import StrEnum
from pathlib import Path
from typing import Any

import structlog
import yaml
from pydantic import BaseModel, Field

logger = structlog.get_logger()


class CredentialProviderType(StrEnum):
    """How AutoGenesis obtains OAuth credentials."""

    ENV = "env"
    FILE = "file"
    GATEWAY = "gateway"


class CodexConfig(BaseModel):
    """OpenAI Codex API configuration."""

    model: str = "gpt-5.3-codex"
    api_base_url: str = "https://api.openai.com/v1"
    timeout: float = 300.0
    max_retries: int = 3


class TokenConfig(BaseModel):
    """Token budget limits (token counts, not USD — subscription billing)."""

    max_tokens_per_session: int = 500_000
    max_tokens_per_day: int = 5_000_000


class SecurityConfig(BaseModel):
    """Security settings."""

    guardrails_enabled: bool = True


class TwitterConfig(BaseModel):
    """Twitter agent persona configuration."""

    enabled: bool = False
    active_hours_start: str = "09:00"
    active_hours_end: str = "17:00"
    timezone: str = "America/New_York"
    session_interval_minutes: int = 30
    max_drafts_per_session: int = 10
    queue_path: str = ""
    worldview_path: str = ""
    gateway_url: str = "http://127.0.0.1:1456"
    selectors_path: str = ""


class AutoGenesisConfig(BaseModel):
    """Root configuration model."""

    codex: CodexConfig = Field(default_factory=CodexConfig)
    tokens: TokenConfig = Field(default_factory=TokenConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    twitter: TwitterConfig = Field(default_factory=TwitterConfig)
    credential_provider: CredentialProviderType = CredentialProviderType.ENV
    credential_path: str = ""  # for file/gateway providers


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def _find_project_config() -> Path | None:
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        candidate = parent / ".autogenesis" / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open() as f:
            data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
    except (OSError, yaml.YAMLError):
        logger.warning("config_load_failed", path=str(path))
        return {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _env_overrides() -> dict[str, Any]:
    """Parse AUTOGENESIS_* env vars into nested dict. Uses __ as separator."""
    prefix = "AUTOGENESIS_"
    result: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix) :].lower().split("__")
        current = result
        for part in parts[:-1]:
            current = current.setdefault(part, {})
        current[parts[-1]] = value
    return result


def load_config() -> AutoGenesisConfig:
    """Load configuration with 6-layer cascade."""
    merged: dict[str, Any] = {}

    # Layer 2: System config
    merged = _deep_merge(merged, _load_yaml(Path("/etc/autogenesis/config.yaml")))

    # Layer 3: User config
    merged = _deep_merge(merged, _load_yaml(_xdg_config_home() / "autogenesis" / "config.yaml"))

    # Layer 4: Project config
    project = _find_project_config()
    if project:
        merged = _deep_merge(merged, _load_yaml(project))

    # Layer 5: Environment variables
    merged = _deep_merge(merged, _env_overrides())

    return AutoGenesisConfig.model_validate(merged)
