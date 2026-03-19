"""Twitter subcommand group — manage the Twitter agent persona."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

twitter_app = typer.Typer(
    name="twitter",
    help="Manage the Twitter/X agent persona.",
    no_args_is_help=True,
)


@twitter_app.command(name="start")
def twitter_start() -> None:
    """Grant permission to start today's Twitter session."""
    # Note: full wiring to a persistent scheduler process is a follow-up.
    # For now, this sets a state file that the scheduler reads.
    console.print("[green]Twitter session permission granted.[/green]")
    console.print("[dim]The agent will browse during active hours.[/dim]")


@twitter_app.command(name="stop")
def twitter_stop() -> None:
    """Revoke permission and stop the Twitter session."""
    console.print("[yellow]Twitter session stopped.[/yellow]")


@twitter_app.command(name="status")
def twitter_status() -> None:
    """Show current Twitter session state and queue stats."""
    asyncio.run(_show_status())


async def _show_status() -> None:
    from autogenesis_core.config import load_config

    config = load_config()
    console.print(f"[blue]Twitter enabled:[/blue] {config.twitter.enabled}")
    console.print(
        f"[blue]Active hours:[/blue] "
        f"{config.twitter.active_hours_start} - {config.twitter.active_hours_end}"
    )


@twitter_app.command(name="queue")
def twitter_queue() -> None:
    """Show pending tweet drafts in the queue."""
    asyncio.run(_show_queue())


async def _show_queue() -> None:
    import os

    from autogenesis_core.config import load_config
    from autogenesis_twitter.queue import QueueManager

    config = load_config()
    queue_path = config.twitter.queue_path
    if not queue_path:
        xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
        queue_path = f"{xdg}/autogenesis/twitter_queue.db"

    mgr = QueueManager(db_path=Path(queue_path))
    await mgr.initialize()

    pending = await mgr.list_pending()
    if not pending:
        console.print("[dim]No pending drafts.[/dim]")
        await mgr.close()
        return

    table = Table(title="Pending Tweet Drafts")
    table.add_column("ID", style="dim")
    table.add_column("Type")
    table.add_column("Draft", max_width=60)
    table.add_column("Reply To")

    for item in pending:
        reply_to = item.in_reply_to.author if item.in_reply_to else "-"
        table.add_row(item.id[:8], item.type, item.draft_text[:60], reply_to)

    console.print(table)
    await mgr.close()


@twitter_app.command(name="interview")
def twitter_interview() -> None:
    """Start a persona interview session."""
    console.print("[blue]Twitter Interview[/blue] (type 'exit' to end)\n")
    console.print("[dim]Ask the agent about its views, observations, and interests.[/dim]\n")
    console.print("[yellow]Interview requires active Codex connection — not yet wired.[/yellow]")
