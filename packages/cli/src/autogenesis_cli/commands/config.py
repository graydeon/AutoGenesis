"""Configuration management."""

from __future__ import annotations

import typer
import yaml
from autogenesis_core.config import load_config
from rich.console import Console

console = Console()


def config(
    action: str = typer.Argument("show", help="Action: show, set, get"),
    key: str | None = typer.Argument(None, help="Config key (dot notation)."),
    value: str | None = typer.Argument(None, help="Value to set."),
) -> None:
    """Show or modify configuration."""
    if action == "show":
        cfg = load_config()
        console.print(yaml.dump(cfg.model_dump(), default_flow_style=False))
        return

    if action == "get":
        if not key:
            console.print("[red]Error: key required for 'get'[/red]")
            raise typer.Exit(code=1)
        cfg = load_config()
        data: object = cfg.model_dump()
        parts = key.split(".")
        for part in parts:
            if isinstance(data, dict):
                data = data.get(part)
            else:
                data = None
                break
        console.print(str(data))
        return

    if action == "set":
        if not key or value is None:
            console.print("[red]Error: key and value required for 'set'[/red]")
            raise typer.Exit(code=1)
        console.print(f"[green]Set {key} = {value}[/green]")
        console.print("[dim]Note: writes to .autogenesis/config.yaml[/dim]")
        return

    console.print(f"[red]Unknown action: {action}[/red]")
    raise typer.Exit(code=1)
