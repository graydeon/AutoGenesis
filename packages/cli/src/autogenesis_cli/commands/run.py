"""Single-shot task execution."""

from __future__ import annotations

import sys

import typer
from rich.console import Console

console = Console()


def run(
    prompt: str | None = typer.Argument(None, help="Task prompt to execute."),
    tier: str = typer.Option("standard", "--tier", "-t", help="Model tier."),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),  # noqa: ARG001
) -> None:
    """Execute a single task and exit."""
    # Read from stdin if no prompt argument
    if prompt is None:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("[red]Error: No prompt provided.[/red]")
            raise typer.Exit(code=1)

    console.print(f"[dim]Running with tier={tier}...[/dim]")

    # Placeholder — will wire to AgentLoop
    console.print(f"[blue]Result:[/blue] Echo: {prompt}")
    console.print("[dim]Tokens: 0 in / 0 out | Cost: $0.0000[/dim]")
