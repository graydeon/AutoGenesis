"""Project setup commands."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

import typer
import yaml
from rich.console import Console

console = Console()

project_app = typer.Typer(
    name="project",
    help="Project setup helpers.",
    no_args_is_help=True,
)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


@project_app.command(name="init")
def project_init(
    path: str = typer.Argument(".", help="Project path to initialize."),
    skip_index: bool = typer.Option(
        False,
        "--skip-index",
        help="Skip `gitnexus analyze` during init.",
    ),
    force_index: bool = typer.Option(
        False,
        "--force-index",
        help="Force full GitNexus re-index.",
    ),
) -> None:
    """Initialize per-project AutoGenesis + GitNexus context."""
    project_root = Path(path).resolve()
    if not project_root.exists():
        console.print(f"[red]Path does not exist:[/red] {project_root}")
        raise typer.Exit(code=1)

    autogenesis_dir = project_root / ".autogenesis"
    autogenesis_dir.mkdir(parents=True, exist_ok=True)
    config_path = autogenesis_dir / "config.yaml"

    current: dict[str, Any] = {}
    if config_path.exists():
        try:
            with config_path.open() as f:
                loaded = yaml.safe_load(f)
            if isinstance(loaded, dict):
                current = loaded
        except (OSError, yaml.YAMLError):
            current = {}

    defaults: dict[str, Any] = {
        "project_name": project_root.name,
        "gitnexus": {
            "enabled": True,
            "binary": "gitnexus",
            "auto_index": True,
            "query_limit": 3,
            "max_context_chars": 3000,
            "command_timeout_seconds": 20.0,
            "index_timeout_seconds": 600.0,
        },
    }
    merged = _deep_merge(defaults, current)
    with config_path.open("w") as f:
        yaml.safe_dump(merged, f, sort_keys=False)

    console.print(f"[green]Initialized config:[/green] {config_path}")

    if skip_index:
        console.print("[dim]Skipped GitNexus indexing (--skip-index).[/dim]")
        return

    binary = shutil.which("gitnexus")
    if not binary:
        console.print("[yellow]gitnexus not found in PATH. Install it, then run:[/yellow]")
        console.print(f"  gitnexus analyze {project_root}")
        return

    cmd = [binary, "analyze"]
    if force_index:
        cmd.append("--force")
    cmd.append(str(project_root))
    try:
        subprocess.run(cmd, check=True, cwd=project_root)  # noqa: S603
        console.print(f"[green]GitNexus index ready for:[/green] {project_root}")
    except subprocess.CalledProcessError as exc:
        console.print(f"[red]GitNexus indexing failed (exit {exc.returncode}).[/red]")
        raise typer.Exit(code=1) from exc
