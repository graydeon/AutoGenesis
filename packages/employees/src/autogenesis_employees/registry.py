"""Employee registry — load, merge, resolve employee YAML configs.

Global configs at ~/.config/autogenesis/employees/.
Project overrides at .autogenesis/employees/.
Project configs deep-merge over global.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
import yaml

from autogenesis_employees.models import EmployeeConfig

if TYPE_CHECKING:
    from pathlib import Path

logger = structlog.get_logger()


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        elif key in result and isinstance(result[key], list) and isinstance(value, list):
            result[key] = result[key] + value
        else:
            result[key] = value
    return result


def _load_yaml_dir(directory: Path) -> dict[str, dict[str, Any]]:
    """Load all YAML files from a directory, keyed by employee id."""
    configs: dict[str, dict[str, Any]] = {}
    for path in sorted(directory.glob("*.yaml")):
        try:
            with path.open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "id" in data:
                configs[data["id"]] = data
        except (OSError, yaml.YAMLError):
            logger.warning("employee_config_load_failed", path=str(path))
    return configs


def _apply_project_overrides(
    configs: dict[str, dict[str, Any]],
    project_dir: Path,
) -> None:
    """Merge project-level overrides into configs in-place."""
    for path in sorted(project_dir.glob("*.yaml")):
        try:
            with path.open() as f:
                override = yaml.safe_load(f)
            if not isinstance(override, dict):
                continue
            employee_id = override.get("id", path.stem)
            if employee_id in configs:
                configs[employee_id] = _deep_merge(configs[employee_id], override)
            elif "id" in override:
                configs[employee_id] = override
        except (OSError, yaml.YAMLError):
            logger.warning("employee_override_load_failed", path=str(path))


class EmployeeRegistry:
    """Loads and resolves employee configurations."""

    def __init__(
        self,
        global_dir: Path | None = None,
        project_dir: Path | None = None,
    ) -> None:
        self._global_dir = global_dir
        self._project_dir = project_dir
        self._cache: dict[str, EmployeeConfig] = {}
        self._load()

    def _load(self) -> None:
        configs: dict[str, dict[str, Any]] = {}

        if self._global_dir and self._global_dir.exists():
            configs.update(_load_yaml_dir(self._global_dir))

        if self._project_dir and self._project_dir.exists():
            _apply_project_overrides(configs, self._project_dir)

        for employee_id, data in configs.items():
            try:
                self._cache[employee_id] = EmployeeConfig.model_validate(data)
            except ValueError:
                logger.warning("employee_config_invalid", id=employee_id)

    def get(self, employee_id: str) -> EmployeeConfig | None:
        return self._cache.get(employee_id)

    def list_active(self) -> list[EmployeeConfig]:
        return [e for e in self._cache.values() if e.status == "active"]

    def list_all(self) -> list[EmployeeConfig]:
        return list(self._cache.values())
