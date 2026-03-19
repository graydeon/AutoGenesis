"""CEO subcommand group — orchestrate agent employees."""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

console = Console()

ceo_app = typer.Typer(
    name="ceo",
    help="CEO Orchestrator — manage goals and tasks.",
    no_args_is_help=True,
)


def _get_orchestrator():  # noqa: ANN202
    """Lazy-build a CEOOrchestrator with real dependencies."""
    import os
    from pathlib import Path

    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.sub_agents import SubAgentManager
    from autogenesis_employees.orchestrator import CEOOrchestrator
    from autogenesis_employees.registry import EmployeeRegistry
    from autogenesis_employees.runtime import EmployeeRuntime

    cfg = load_config()

    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    global_dir = (
        Path(cfg.employees.global_roster_path)
        if cfg.employees.global_roster_path
        else Path(xdg) / "autogenesis" / "employees"
    )
    registry = EmployeeRegistry(global_dir=global_dir)

    creds = EnvCredentialProvider()
    codex = CodexClient(
        creds,
        CodexClientConfig(
            model=cfg.codex.model,
            api_base_url=cfg.codex.api_base_url,
            timeout=cfg.codex.timeout,
        ),
    )

    return CEOOrchestrator(
        registry=registry,
        runtime=EmployeeRuntime(),
        sub_agent_mgr=SubAgentManager(stream_output=True),
        codex=codex,
        dispatch_timeout=cfg.employees.dispatch_timeout,
    )


def _run_async(coro):  # noqa: ANN001, ANN202
    """Run an async coroutine from sync Typer command."""
    return asyncio.run(coro)


@ceo_app.command(name="enqueue")
def ceo_enqueue(
    description: str = typer.Argument(help="Task description"),
    priority: int = typer.Option(0, "--priority", "-p", help="Priority (higher = first)"),
) -> None:
    """Push a task onto the CEO queue."""

    async def _run() -> None:
        orch = _get_orchestrator()
        await orch.initialize()
        task_id = await orch.enqueue(description, priority=priority)
        console.print(f"[green]Enqueued:[/green] {task_id}")
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="run")
def ceo_run(
    goal: str = typer.Argument(help="High-level goal to decompose and execute"),
) -> None:
    """Decompose a goal and execute via employee dispatch."""

    async def _run() -> None:
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.run(goal)
            if result.status == "completed":
                console.print("\n[bold green]Goal completed![/bold green]")
            else:
                console.print("\n[bold red]Goal escalated — needs manual intervention.[/bold red]")

            table = Table(title="Subtask Results")
            table.add_column("Subtask")
            table.add_column("Employee")
            table.add_column("Status")
            table.add_column("Attempt")
            table.add_column("Duration")

            for sr in result.subtask_results:
                style = "green" if sr.status == "completed" else "red"
                table.add_row(
                    sr.subtask[:60],
                    sr.employee_id,
                    sr.status,
                    str(sr.attempt),
                    f"{sr.duration_seconds:.1f}s",
                    style=style,
                )
            console.print(table)
            console.print(f"\nPlan: {result.plan_path}")
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())


@ceo_app.command(name="dispatch")
def ceo_dispatch(
    task_id: str = typer.Argument(None, help="Specific task ID (or dispatches highest priority)"),
) -> None:
    """Execute next queued task or a specific one."""

    async def _run() -> None:
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.dispatch(task_id)
            style = "green" if result.status == "completed" else "red"
            console.print(
                f"[{style}]{result.status}[/{style}]"
                f" — {result.employee_id} ({result.duration_seconds:.1f}s)"
            )
            if result.output:
                console.print(result.output[:500])
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())


@ceo_app.command(name="status")
def ceo_status() -> None:
    """Show status of all goals and tasks."""

    async def _run() -> None:
        from autogenesis_employees.ceo_models import GoalStatus

        orch = _get_orchestrator()
        await orch.initialize()
        items = await orch.status()

        if not items:
            console.print("[dim]No goals or tasks.[/dim]")
            await orch.close()
            return

        table = Table(title="CEO Status")
        table.add_column("Type")
        table.add_column("ID", style="dim")
        table.add_column("Description")
        table.add_column("Status")
        table.add_column("Details")

        for item in items:
            if isinstance(item, GoalStatus):
                style = "green" if item.status == "completed" else "yellow"
                table.add_row(
                    "goal",
                    item.goal_id,
                    item.description[:50],
                    item.status,
                    f"{item.subtasks_completed}/{item.subtasks_total}",
                    style=style,
                )
            else:
                style = "green" if item.status == "completed" else "cyan"
                table.add_row(
                    "task",
                    item.task_id,
                    item.description[:50],
                    item.status,
                    f"pri={item.priority}",
                    style=style,
                )
        console.print(table)
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="plan")
def ceo_plan(
    goal_id: str = typer.Argument(help="Goal ID to show plan for"),
) -> None:
    """Print the markdown plan for a goal."""

    async def _run() -> None:
        from pathlib import Path

        orch = _get_orchestrator()
        await orch.initialize()
        state = orch._require_state()  # noqa: SLF001
        goal = await state.get_goal(goal_id)
        if not goal:
            console.print(f"[red]Goal {goal_id} not found.[/red]")
            await orch.close()
            return
        plan_path = Path(goal["plan_path"])
        if plan_path.exists():
            console.print(plan_path.read_text())
        else:
            console.print(f"[red]Plan file not found: {plan_path}[/red]")
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="resume")
def ceo_resume(
    goal_id: str = typer.Argument(help="Goal ID to resume"),
) -> None:
    """Resume an escalated or paused goal."""

    async def _run() -> None:
        orch = _get_orchestrator()
        await orch.initialize()
        try:
            result = await orch.resume(goal_id)
            style = "green" if result.status == "completed" else "red"
            console.print(f"[{style}]Goal {result.status}[/{style}]")
        except RuntimeError as e:
            console.print(f"[red]Error:[/red] {e}")
        finally:
            await orch.close()

    _run_async(_run())
