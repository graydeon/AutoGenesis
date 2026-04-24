"""CEO subcommand group — orchestrate agent employees."""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING, Any, TypeVar

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

    from autogenesis_core.events import Event
    from autogenesis_employees.orchestrator import CEOOrchestrator

    from autogenesis_cli.live_display import AgentLiveDisplay

console = Console()
_T = TypeVar("_T")

ceo_app = typer.Typer(
    name="ceo",
    help="CEO Orchestrator — manage goals and tasks.",
    no_args_is_help=True,
)

# Patterns to extract meaningful status from Codex CLI output
_TOOL_CALL_RE = re.compile(r"(shell|file_read|file_write|file_edit|glob|grep|list_dir|think)\b")
_SKIP_PREFIXES = (
    "OpenAI Codex",
    "--------",
    "workdir:",
    "model:",
    "provider:",
    "approval:",
    "sandbox:",
    "reasoning",
    "session id:",
    "mcp:",
    "tokens used",
    "user",
    "",
)


def _make_output_handler(display: AgentLiveDisplay) -> Callable[[str, str], None]:
    """Create an on_output callback that feeds the live display."""

    def handler(label: str, line: str) -> None:
        stripped = line.strip()
        # Skip Codex boilerplate
        if any(stripped.startswith(p) for p in _SKIP_PREFIXES):
            return
        if stripped.startswith("codex"):
            display.agent_update(label, "thinking...")
            return
        # Detect tool calls
        tool_match = _TOOL_CALL_RE.search(stripped)
        if tool_match:
            display.agent_update(label, f"calling {tool_match.group(0)}...")
            return
        # Meaningful content — show truncated
        if len(stripped) > 5:  # noqa: PLR2004
            display.agent_update(label, stripped[:80])

    return handler


def _get_orchestrator(display: AgentLiveDisplay | None = None) -> CEOOrchestrator:
    """Lazy-build a CEOOrchestrator with real dependencies."""
    import os
    from pathlib import Path

    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.sub_agents import SubAgentManager
    from autogenesis_employees.gitnexus import GitNexusContextProvider
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

    on_output = _make_output_handler(display) if display else None

    # Lightweight manager for CEO reasoning (decompose/assign) — cheap model, no MCP
    reasoning_mgr = SubAgentManager(
        max_concurrent=3,
        on_output=on_output,
        extra_flags=[
            "--ephemeral",
            "--skip-git-repo-check",
            "-m",
            "o4-mini",
            "-c",
            "reasoning_effort=low",
            "-c",
            "mcp_servers={}",
        ],
    )

    return CEOOrchestrator(
        registry=registry,
        runtime=EmployeeRuntime(),
        sub_agent_mgr=SubAgentManager(max_concurrent=5, on_output=on_output),
        codex=codex,
        dispatch_timeout=cfg.employees.dispatch_timeout,
        reasoning_mgr=reasoning_mgr,
        context_provider=GitNexusContextProvider(
            enabled=cfg.gitnexus.enabled,
            binary=cfg.gitnexus.binary,
            auto_index=cfg.gitnexus.auto_index,
            query_limit=cfg.gitnexus.query_limit,
            max_context_chars=cfg.gitnexus.max_context_chars,
            command_timeout_seconds=cfg.gitnexus.command_timeout_seconds,
            index_timeout_seconds=cfg.gitnexus.index_timeout_seconds,
        ),
    )


def _run_async(coro: Coroutine[Any, Any, _T]) -> _T:
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
def ceo_run(  # noqa: C901, PLR0915
    goal: str = typer.Argument(help="High-level goal to decompose and execute"),
) -> None:
    """Decompose a goal and execute via employee dispatch."""
    from autogenesis_core.events import EventType, get_event_bus

    from autogenesis_cli.live_display import AgentLiveDisplay

    display = AgentLiveDisplay()

    def _on_event(event: Event) -> None:
        et = event.event_type
        data = event.data
        if et == EventType.CEO_GOAL_START:
            display.set_phase(f"Decomposing: {data.get('goal', '')[:60]}")
        elif et == EventType.CEO_SUBTASK_ASSIGN:
            emp = data.get("employee_id", "?")
            task = data.get("subtask", "")[:60]
            display.set_phase("")
            display.agent_start(emp, task)
        elif et == EventType.CEO_SUBTASK_COMPLETE:
            emp = data.get("employee_id", "?")
            display.agent_done(emp, "completed")
        elif et == EventType.CEO_SUBTASK_FAIL:
            emp = data.get("employee_id", "?")
            display.agent_done(emp, "FAILED — retrying...")
        elif et == EventType.CEO_ESCALATION:
            display.set_phase("ESCALATED — needs manual intervention")
        elif et == EventType.CEO_GOAL_COMPLETE:
            display.set_phase("")

    bus = get_event_bus()
    for et in (
        EventType.CEO_GOAL_START,
        EventType.CEO_SUBTASK_ASSIGN,
        EventType.CEO_SUBTASK_COMPLETE,
        EventType.CEO_SUBTASK_FAIL,
        EventType.CEO_ESCALATION,
        EventType.CEO_GOAL_COMPLETE,
    ):
        bus.subscribe(et, _on_event)

    async def _run() -> None:
        orch = _get_orchestrator(display=display)
        await orch.initialize()
        display.start()
        try:
            result = await orch.run(goal)
        except (RuntimeError, KeyboardInterrupt, asyncio.CancelledError) as e:
            display.stop()
            await orch._sub_agent_mgr.cancel_all()  # noqa: SLF001
            await orch.close()
            if isinstance(e, RuntimeError):
                console.print(f"[red]Error:[/red] {e}")
            else:
                console.print("\n[yellow]Cancelled.[/yellow]")
            return
        finally:
            display.stop()

        if result.status == "completed":
            console.print("\n[bold green]Goal completed![/bold green]")
        else:
            console.print("\n[bold red]Goal escalated.[/bold red]")

        table = Table(title="Subtask Results")
        table.add_column("Subtask", max_width=50)
        table.add_column("Employee")
        table.add_column("Status")
        table.add_column("Time")

        for sr in result.subtask_results:
            style = "green" if sr.status == "completed" else "red"
            table.add_row(
                sr.subtask[:50],
                sr.employee_id,
                sr.status,
                f"{sr.duration_seconds:.1f}s",
                style=style,
            )
        console.print(table)
        console.print(f"\nPlan: {result.plan_path}")
        await orch.close()

    try:
        _run_async(_run())
    except KeyboardInterrupt:
        display.stop()
        console.print("\n[yellow]Cancelled.[/yellow]")


@ceo_app.command(name="dispatch")
def ceo_dispatch(
    task_id: str | None = typer.Argument(
        None,
        help="Specific task ID (or dispatches highest priority)",
    ),
) -> None:
    """Execute next queued task or a specific one."""
    from autogenesis_cli.live_display import AgentLiveDisplay

    display = AgentLiveDisplay()

    async def _run() -> None:
        orch = _get_orchestrator(display=display)
        await orch.initialize()
        display.start()
        display.set_phase("Assigning task...")
        try:
            result = await orch.dispatch(task_id)
        except RuntimeError as e:
            display.stop()
            console.print(f"[red]Error:[/red] {e}")
            await orch.close()
            return
        finally:
            display.stop()

        style = "green" if result.status == "completed" else "red"
        console.print(
            f"[{style}]{result.status}[/{style}]"
            f" — {result.employee_id} ({result.duration_seconds:.1f}s)"
        )
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
        if await asyncio.to_thread(plan_path.exists):
            console.print(await asyncio.to_thread(plan_path.read_text))
        else:
            console.print(f"[red]Plan file not found: {plan_path}[/red]")
        await orch.close()

    _run_async(_run())


@ceo_app.command(name="resume")
def ceo_resume(
    goal_id: str = typer.Argument(help="Goal ID to resume"),
) -> None:
    """Resume an escalated or paused goal."""
    from autogenesis_cli.live_display import AgentLiveDisplay

    display = AgentLiveDisplay()

    async def _run() -> None:
        orch = _get_orchestrator(display=display)
        await orch.initialize()
        display.start()
        try:
            result = await orch.resume(goal_id)
        except RuntimeError as e:
            display.stop()
            console.print(f"[red]Error:[/red] {e}")
            await orch.close()
            return
        finally:
            display.stop()

        style = "green" if result.status == "completed" else "red"
        console.print(f"[{style}]Goal {result.status}[/{style}]")
        await orch.close()

    _run_async(_run())
