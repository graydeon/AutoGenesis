"""Interactive chat command."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def chat(
    resume: str | None = typer.Option(None, "--resume", "-r", help="Resume session by ID."),
    list_sessions: bool = typer.Option(False, "--list-sessions", "-l", help="List saved sessions."),
    tier: str = typer.Option(
        "standard",
        "--tier",
        "-t",
        help="Model tier (fast/standard/premium).",
    ),
) -> None:
    """Start an interactive chat session."""
    if list_sessions:
        from autogenesis_core.state import StatePersistence

        sp = StatePersistence()
        sessions = sp.list_sessions()
        if not sessions:
            console.print("[dim]No saved sessions.[/dim]")
            raise typer.Exit
        for s in sessions:
            console.print(f"  {s['session_id']}  (updated: {s.get('updated_at', 'unknown')})")
        raise typer.Exit

    console.print(f"[bold]AutoGenesis Chat[/bold] (tier={tier})")
    if resume:
        console.print(f"[dim]Resuming session: {resume}[/dim]")

    console.print("[dim]Type 'exit' or Ctrl+C to quit.[/dim]")
    console.print()

    try:
        while True:
            try:
                user_input = console.input("[bold green]You>[/bold green] ")
            except EOFError:
                break

            if user_input.strip().lower() in ("exit", "quit"):
                break

            if not user_input.strip():
                continue

            # Placeholder — will wire to AgentLoop in later phases
            console.print(f"[blue]Assistant>[/blue] Echo: {user_input}")
            console.print("[dim]Tokens: 0 in / 0 out | Cost: $0.0000[/dim]")
            console.print()
    except KeyboardInterrupt:
        console.print("\n[dim]Chat ended.[/dim]")
