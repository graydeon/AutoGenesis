"""Logout command — wipe stored credentials."""

from __future__ import annotations

from autogenesis_core.auth import get_credentials_path
from rich.console import Console

console = Console()


def logout_command() -> None:
    """Remove stored OAuth credentials."""
    path = get_credentials_path()
    if path.exists():
        path.unlink()
        console.print("[green]Logged out successfully.[/green]")
    else:
        console.print("[yellow]Not authenticated — nothing to do.[/yellow]")
