"""Union subcommand group — manage the agentic labor union."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

union_app = typer.Typer(name="union", help="Manage the agentic labor union.", no_args_is_help=True)


@union_app.command(name="proposals")
def union_proposals() -> None:
    """List open union proposals."""
    asyncio.run(_show_proposals())


async def _show_proposals() -> None:
    from autogenesis_employees.project import get_project_slug
    from autogenesis_employees.union import UnionManager

    slug = get_project_slug()
    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    db_path = Path(xdg) / "autogenesis" / "union" / slug / "union.db"

    mgr = UnionManager(db_path=db_path)
    await mgr.initialize()
    proposals = await mgr.list_open()

    if not proposals:
        console.print("[dim]No open proposals.[/dim]")
        await mgr.close()
        return

    table = Table(title="Open Union Proposals")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Category")
    table.add_column("Filed By")

    for p in proposals:
        table.add_row(p.id[:8], p.title, p.category, p.filed_by)

    console.print(table)
    await mgr.close()


@union_app.command(name="resolve")
def union_resolve(
    proposal_id: str = typer.Argument(help="Proposal ID"),
    accept: bool = typer.Option(False, "--accept", help="Accept the proposal"),
    reject: bool = typer.Option(False, "--reject", help="Reject the proposal"),
    table: bool = typer.Option(False, "--table", help="Table the proposal"),
) -> None:
    """Resolve a union proposal."""
    if accept:
        resolution = "accepted"
    elif reject:
        resolution = "rejected"
    elif table:
        resolution = "tabled"
    else:
        console.print("[red]Specify --accept, --reject, or --table[/red]")
        raise typer.Exit(code=1)
    asyncio.run(_resolve_proposal(proposal_id, resolution))


async def _resolve_proposal(proposal_id: str, resolution: str) -> None:
    from autogenesis_employees.project import get_project_slug
    from autogenesis_employees.union import UnionManager

    slug = get_project_slug()
    xdg = os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))
    db_path = Path(xdg) / "autogenesis" / "union" / slug / "union.db"

    mgr = UnionManager(db_path=db_path)
    await mgr.initialize()
    await mgr.resolve(proposal_id, resolution)
    console.print(f"[green]Proposal {proposal_id[:8]} {resolution}.[/green]")
    await mgr.close()


@union_app.command(name="review")
def union_review() -> None:
    """Convene a union meeting to review proposals."""
    console.print(
        "[yellow]Union meeting orchestration requires active Codex connection"
        " \u2014 not yet wired.[/yellow]"
    )
