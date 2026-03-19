"""Run command — single-shot task execution via Codex CLI."""

from __future__ import annotations

import os
import subprocess
import sys

import typer
from rich.console import Console

console = Console()


def run_command(
    prompt: str = typer.Argument("", help="Task to execute"),
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("", "--model", help="Model to use (default: Codex default)"),
    quiet: bool = typer.Option(False, "--quiet", help="Minimal output"),  # noqa: ARG001
) -> None:
    """Execute a single task and exit."""
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        if not prompt:
            console.print("[red]No prompt provided.[/red] Usage: autogenesis run 'your task'")
            raise typer.Exit(code=1)

    cmd = ["codex", "exec"]
    if full_auto:
        cmd.append("--full-auto")
    if model:
        cmd.extend(["-m", model])
    cmd.append(prompt)

    try:
        result = subprocess.run(cmd, env=os.environ, check=False)  # noqa: S603
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] codex CLI not found. Install with: npm install -g @openai/codex"
        )
        raise typer.Exit(code=1) from None
    except KeyboardInterrupt:
        pass
