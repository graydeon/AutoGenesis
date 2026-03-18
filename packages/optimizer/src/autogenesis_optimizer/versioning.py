"""Prompt version control."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path  # noqa: TC003
from typing import Any

import yaml
from autogenesis_core.models import PromptVersion


class PromptVersionManager:
    """Manage versioned prompt templates with YAML manifest."""

    def __init__(self, prompts_dir: Path) -> None:
        self._dir = prompts_dir
        self._manifest_path = prompts_dir / "manifest.yaml"
        self._manifest: dict[str, Any] = {}
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self._manifest_path.exists():
            data = yaml.safe_load(self._manifest_path.read_text())
            self._manifest = data if isinstance(data, dict) else {}

    def _save_manifest(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._manifest_path.write_text(yaml.dump(self._manifest, default_flow_style=False))

    def create_version(
        self,
        name: str,
        content: str,
        version: str,
        parent_version: str | None = None,
    ) -> PromptVersion:
        """Create a new prompt version."""
        checksum = f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

        pv = PromptVersion(
            version=version,
            content=content,
            checksum=checksum,
            parent_version=parent_version,
        )

        # Update manifest
        prompts = self._manifest.setdefault("prompts", {})
        prompt_entry = prompts.setdefault(name, {"versions": {}})
        prompt_entry["versions"][version] = {
            "checksum": checksum,
            "created_at": datetime.now(UTC).isoformat(),
            "parent_version": parent_version,
        }

        # Set as active if first version
        if "active_version" not in prompt_entry:
            prompt_entry["active_version"] = version

        self._save_manifest()
        return pv

    def get_active_version(self, name: str) -> str | None:
        """Get active version string for a prompt."""
        prompts = self._manifest.get("prompts", {})
        entry = prompts.get(name)
        if not entry:
            return None
        return entry.get("active_version")  # type: ignore[no-any-return]

    def set_active_version(self, name: str, version: str) -> None:
        """Set the active version for a prompt."""
        prompts = self._manifest.get("prompts", {})
        if name not in prompts:
            msg = f"Prompt {name!r} not found"
            raise KeyError(msg)
        if version not in prompts[name].get("versions", {}):
            msg = f"Version {version!r} not found for {name!r}"
            raise KeyError(msg)
        prompts[name]["active_version"] = version
        self._save_manifest()

    def rollback(self, name: str) -> str | None:
        """Rollback to parent version. Returns new active version or None."""
        prompts = self._manifest.get("prompts", {})
        entry = prompts.get(name)
        if not entry:
            return None
        current = entry.get("active_version")
        if not current:
            return None
        versions = entry.get("versions", {})
        current_info = versions.get(current, {})
        parent = current_info.get("parent_version")
        if parent and parent in versions:
            entry["active_version"] = parent
            self._save_manifest()
            return parent  # type: ignore[no-any-return]
        return None

    def list_versions(self, name: str) -> list[str]:
        """List all versions for a prompt."""
        prompts = self._manifest.get("prompts", {})
        entry = prompts.get(name, {})
        return list(entry.get("versions", {}).keys())

    def get_checksum(self, name: str, version: str) -> str | None:
        """Get checksum for a specific version."""
        prompts = self._manifest.get("prompts", {})
        entry = prompts.get(name, {})
        version_info = entry.get("versions", {}).get(version, {})
        return version_info.get("checksum")  # type: ignore[no-any-return]
