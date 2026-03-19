"""AutoGenesis CLI application."""

from __future__ import annotations

import typer

from autogenesis_cli.commands.chat import chat_command
from autogenesis_cli.commands.config import config as config_command
from autogenesis_cli.commands.login import login_command
from autogenesis_cli.commands.logout import logout_command
from autogenesis_cli.commands.run import run_command
from autogenesis_cli.commands.twitter import twitter_app

app = typer.Typer(
    name="autogenesis",
    help="The token-efficient agent harness powered by OpenAI Codex.",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        from autogenesis_cli import __version__

        typer.echo(f"autogenesis {__version__}")
        raise typer.Exit


@app.callback()
def main_callback(
    _version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """AutoGenesis — autonomous agent harness."""


# Register commands
app.command(name="login")(login_command)
app.command(name="logout")(logout_command)
app.command(name="run")(run_command)
app.command(name="chat")(chat_command)
app.command(name="config")(config_command)
app.add_typer(twitter_app, name="twitter")


def main() -> None:
    app()
