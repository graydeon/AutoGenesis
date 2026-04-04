"""tui command — launch the AutoGenesis terminal UI."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def tui_command(
    theme: str = typer.Option(
        "dracula",
        "--theme",
        "-t",
        help="Theme name (dracula, midnight-blue, hacker-green)",
    ),
) -> None:
    """Launch the AutoGenesis TUI."""
    try:
        from autogenesis_tui.app import AutogenesisApp
    except ImportError:
        console.print(
            "[red]Error:[/red] autogenesis-tui not installed. Run: uv sync --all-packages"
        )
        raise typer.Exit(code=1) from None

    app = AutogenesisApp(theme_name=theme)
    app.run()
