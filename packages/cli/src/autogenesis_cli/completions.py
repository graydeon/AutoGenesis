"""Shell completion generation."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()

SHELLS = ("bash", "zsh", "fish")


def install_completion(shell: str = typer.Argument("bash", help="Shell type.")) -> None:
    """Generate shell completions."""
    if shell not in SHELLS:
        console.print(f"[red]Unsupported shell: {shell}. Use: {', '.join(SHELLS)}[/red]")
        raise typer.Exit(code=1)
    console.print(f'[dim]Run: eval "$(autogenesis --show-completion {shell})"[/dim]')
