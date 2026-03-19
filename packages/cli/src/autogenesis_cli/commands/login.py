"""Login command — verify or initiate Codex CLI authentication."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import typer
from rich.console import Console

console = Console()


def login_command(
    device_code: bool = typer.Option(  # noqa: ARG001
        False, "--device-code", help="Use device code flow for headless hosts"
    ),
) -> None:
    """Authenticate with OpenAI via Codex CLI."""
    codex_auth = Path.home() / ".codex" / "auth.json"

    if codex_auth.exists():
        try:
            data = json.loads(codex_auth.read_text())
            tokens = data.get("tokens", {})
            if tokens.get("access_token"):
                console.print("[green]Already authenticated via Codex CLI.[/green]")
                console.print(f"[dim]Auth file: {codex_auth}[/dim]")
                return
        except (json.JSONDecodeError, KeyError):
            pass

    console.print("[blue]Launching Codex CLI login...[/blue]")
    try:
        result = subprocess.run(["codex", "login"], check=False)  # noqa: S603, S607
        if result.returncode == 0:
            console.print("[green]Login successful![/green]")
        else:
            console.print("[red]Login failed.[/red]")
            raise typer.Exit(code=1)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] codex CLI not found. Install with: npm install -g @openai/codex"
        )
        raise typer.Exit(code=1) from None
