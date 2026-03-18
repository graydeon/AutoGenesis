"""XDG-compliant configuration system."""

from __future__ import annotations

from os import environ
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class TierConfig(BaseModel):
    """Configuration for a single model tier."""

    primary: str = ""
    fallback: list[str] = []


class ModelConfig(BaseModel):
    """Model routing configuration."""

    default_tier: str = "standard"
    tiers: dict[str, TierConfig] = Field(
        default_factory=lambda: {
            "fast": TierConfig(primary="gpt-4o-mini", fallback=["claude-3-5-haiku-20241022"]),
            "standard": TierConfig(primary="claude-sonnet-4-20250514", fallback=["gpt-4o"]),
            "premium": TierConfig(primary="claude-opus-4-20250918", fallback=["o3"]),
        }
    )


class TokenConfig(BaseModel):
    """Token budget configuration."""

    max_tokens_per_session: int = 100_000
    max_cost_per_session: float = 5.0
    max_cost_per_day: float = 50.0
    max_cost_per_month: float = 500.0


class SecurityConfig(BaseModel):
    """Security configuration."""

    guardrails_enabled: bool = True
    sandbox_provider: str = "subprocess"
    tools: dict[str, Any] = Field(
        default_factory=lambda: {
            "web_fetch": {"enabled": False},
        }
    )


class TelemetryConfig(BaseModel):
    """Telemetry configuration."""

    enabled: bool = False
    endpoint: str = ""


class MCPConfig(BaseModel):
    """MCP server configuration."""

    servers: dict[str, Any] = Field(default_factory=dict)
    allowlist: list[str] = []


class CoreConfig(BaseModel):
    """Core runtime configuration."""

    session_retention_days: int = 30


class AutoGenesisConfig(BaseModel):
    """Merged configuration from all sources."""

    models: ModelConfig = Field(default_factory=ModelConfig)
    tokens: TokenConfig = Field(default_factory=TokenConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)
    mcp: MCPConfig = Field(default_factory=MCPConfig)
    core: CoreConfig = Field(default_factory=CoreConfig)


def _xdg_config_home() -> Path:
    """Get XDG config home directory."""
    return Path(environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))


def _find_project_config(start: Path | None = None) -> Path | None:
    """Walk up from start to find .autogenesis/config.yaml."""
    current = start or Path.cwd()
    for parent in [current, *current.parents]:
        candidate = parent / ".autogenesis" / "config.yaml"
        if candidate.exists():
            return candidate
        if (parent / ".git").exists():
            break
    return None


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict on failure."""
    if not path.exists():
        return {}
    with path.open() as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(
    config_path: Path | None = None,
    project_path: Path | None = None,
    env_prefix: str = "AUTOGENESIS_",
) -> AutoGenesisConfig:
    """Load configuration with 6-layer cascade.

    Order (later overrides earlier):
    1. Built-in defaults (hardcoded in Pydantic models)
    2. System config: /etc/autogenesis/config.yaml
    3. User config: $XDG_CONFIG_HOME/autogenesis/config.yaml
    4. Project config: .autogenesis/config.yaml
    5. Environment variables: AUTOGENESIS_* (nested via __)
    6. CLI flags (applied by caller after load_config)
    """
    merged: dict[str, Any] = {}

    # Layer 2: System config
    system_config = Path("/etc/autogenesis/config.yaml")
    merged = _deep_merge(merged, _load_yaml(system_config))

    # Layer 3: User config
    if config_path:
        merged = _deep_merge(merged, _load_yaml(config_path))
    else:
        user_config = _xdg_config_home() / "autogenesis" / "config.yaml"
        merged = _deep_merge(merged, _load_yaml(user_config))

    # Layer 4: Project config
    if project_path:
        merged = _deep_merge(merged, _load_yaml(project_path))
    else:
        found = _find_project_config()
        if found:
            merged = _deep_merge(merged, _load_yaml(found))

    # Layer 5: Environment variables
    for key, value in environ.items():
        if key.startswith(env_prefix):
            parts = key[len(env_prefix) :].lower().split("__")
            current = merged
            for part in parts[:-1]:
                current = current.setdefault(part, {})
            current[parts[-1]] = value

    return AutoGenesisConfig.model_validate(merged)
