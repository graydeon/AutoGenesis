"""Project initialization wizard."""

from __future__ import annotations

from pathlib import Path

import typer
import yaml
from rich.console import Console

console = Console()


def init(
    path: str = typer.Option(".", "--path", "-p", help="Project directory."),
) -> None:
    """Initialize AutoGenesis in a project directory."""
    project_dir = Path(path)
    config_dir = project_dir / ".autogenesis"
    config_file = config_dir / "config.yaml"

    if config_file.exists():
        console.print(f"[yellow]Already initialized:[/yellow] {config_file}")
        raise typer.Exit

    config_dir.mkdir(parents=True, exist_ok=True)

    default_config = {
        "models": {"default_tier": "standard"},
        "tokens": {"max_cost_per_session": 5.0},
        "security": {"guardrails_enabled": True},
    }

    config_file.write_text(yaml.dump(default_config, default_flow_style=False))
    console.print(f"[green]Initialized:[/green] {config_file}")
