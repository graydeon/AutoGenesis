"""Meeting commands — standup and on-demand meetings."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def meeting_command(
    topic: str = typer.Argument(help="Meeting topic"),
    attendees: str = typer.Option("", "--attendees", help="Comma-separated employee IDs"),
) -> None:
    """Call an on-demand meeting."""
    console.print(f"[blue]Meeting: {topic}[/blue]")
    if attendees:
        console.print(f"[dim]Attendees: {attendees}[/dim]")
    console.print(
        "[yellow]Meeting orchestration requires active Codex connection — not yet wired.[/yellow]"
    )


def standup_command() -> None:
    """Trigger a manual standup."""
    console.print("[blue]Triggering standup...[/blue]")
    console.print(
        "[yellow]Standup orchestration requires active Codex connection — not yet wired.[/yellow]"
    )
