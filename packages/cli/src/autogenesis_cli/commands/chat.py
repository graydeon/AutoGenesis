"""Chat command — launch interactive Codex session."""

from __future__ import annotations

import os
import subprocess
import sys

import typer
from rich.console import Console

console = Console()


def chat_command(
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("", "--model", help="Model to use (default: Codex default)"),
) -> None:
    """Interactive chat session with the agent."""
    cmd = ["codex"]
    if full_auto:
        cmd.append("--full-auto")
    if model:
        cmd.extend(["-m", model])

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
