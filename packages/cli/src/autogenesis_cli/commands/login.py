"""Login command — host-side PKCE OAuth flow."""

from __future__ import annotations

import typer
from autogenesis_core.auth import load_credentials, login
from rich.console import Console

console = Console()


def login_command(
    device_code: bool = typer.Option(
        False, "--device-code", help="Use device code flow for headless hosts"
    ),
) -> None:
    """Authenticate with OpenAI via OAuth (ChatGPT Plus subscription)."""
    try:
        existing = load_credentials()
        console.print(f"[yellow]Already authenticated (plan: {existing.plan_type})[/yellow]")
        console.print("Run [bold]autogenesis logout[/bold] first to re-authenticate.")
        raise typer.Exit
    except FileNotFoundError:
        pass

    if device_code:
        console.print("[yellow]Device code flow is a stretch goal — not yet implemented.[/yellow]")
        raise typer.Exit(code=1)

    console.print("[blue]Opening browser for OpenAI login...[/blue]")
    creds = login()
    console.print(f"[green]Authenticated![/green] Plan: {creds.plan_type}")
