"""Project slug derivation.

Determines a stable identifier for the current project used
in brain.db, inbox, and union storage paths.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import yaml


def slugify(name: str) -> str:
    """Convert a name to a URL-safe slug."""
    slug = name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def get_project_slug() -> str:
    """Derive project slug from config, git, or cwd."""
    cwd = Path.cwd()

    # 1. Check .autogenesis/config.yaml for project_name
    config_path = cwd / ".autogenesis" / "config.yaml"
    if config_path.exists():
        try:
            with config_path.open() as f:
                data = yaml.safe_load(f)
            if isinstance(data, dict) and "project_name" in data:
                return slugify(str(data["project_name"]))
        except (OSError, yaml.YAMLError):
            pass

    # 2. Try git repo root basename
    git = shutil.which("git")
    if git:
        try:
            result = subprocess.run(  # noqa: S603
                [git, "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
                cwd=cwd,
            )
            return slugify(Path(result.stdout.strip()).name)
        except subprocess.CalledProcessError:
            pass

    # 3. Fall back to cwd basename
    return slugify(cwd.name)
