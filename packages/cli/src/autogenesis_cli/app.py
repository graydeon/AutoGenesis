"""Typer CLI application."""

from __future__ import annotations

import typer
from rich.console import Console

from autogenesis_cli.commands import chat, config, init, run

app = typer.Typer(
    name="autogenesis",
    help="The token-efficient agent framework. CLI-first. Self-improving.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

console = Console()

# Register command groups
app.command(name="chat")(chat.chat)
app.command(name="run")(run.run)
app.command(name="init")(init.init)
app.command(name="config")(config.config)


def _version_callback(value: bool) -> None:
    if value:
        from autogenesis_cli import __version__

        console.print(f"autogenesis {__version__}")
        raise typer.Exit


@app.callback(invoke_without_command=True)
def main_callback(
    version: bool | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=_version_callback,
        is_eager=True,
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress formatting."),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """AutoGenesis CLI."""


def main() -> None:
    """Entry point for the AutoGenesis CLI."""
    app()
