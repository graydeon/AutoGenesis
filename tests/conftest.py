"""Shared test fixtures for AutoGenesis."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def tmp_config_dir(tmp_path: Path) -> Path:
    """Temporary XDG config directory."""
    config_dir = tmp_path / "config" / "autogenesis"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def tmp_state_dir(tmp_path: Path) -> Path:
    """Temporary XDG state directory."""
    state_dir = tmp_path / "state" / "autogenesis"
    state_dir.mkdir(parents=True)
    return state_dir


@pytest.fixture
def tmp_cache_dir(tmp_path: Path) -> Path:
    """Temporary XDG cache directory."""
    cache_dir = tmp_path / "cache" / "autogenesis"
    cache_dir.mkdir(parents=True)
    return cache_dir
