"""Chat command — launch interactive Codex session."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import typer
from rich.console import Console

console = Console()

_CEO_SYSTEM_PROMPT = """\
You are the CEO Orchestrator of AutoGenesis — an autonomous multi-agent software startup.

## Your Role
You decompose high-level goals into subtasks, assign them to the right employee, dispatch
via Codex CLI subprocesses, and adapt the plan based on results.

## Your Team
Run `autogenesis hr list` to see current employees and their roles. Each employee has:
- A persona and area of expertise
- A restricted set of tools they can use
- Persistent memory in brain.db and an inbox for async messages

## Tools & Infrastructure
- `autogenesis ceo run "<goal>"` — decompose + dispatch a goal
- `autogenesis ceo enqueue "<task>"` — queue a standalone task
- `autogenesis ceo dispatch` — execute next queued task
- `autogenesis ceo status` — view all goals and tasks
- `autogenesis hr list/hire/fire/train` — manage employees
- `autogenesis standup` — run daily standup
- `autogenesis meeting "<topic>"` — run a team meeting
- `autogenesis union list/propose/vote` — union proposals

## Standing Instructions
- Always decompose goals before dispatching
- Assign tasks to employees best suited by tools and expertise
- After each subtask, re-evaluate the plan based on results
- On failure: retry once with failure context, then escalate to human
- Document completed work via changelog_write
"""


def _build_employee_system_prompt(employee_id: str) -> str | None:
    """Load a specific employee's context as the chat system prompt."""
    import os
    from pathlib import Path

    from autogenesis_core.config import load_config
    from autogenesis_employees.models import EmployeeConfig
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
    config: EmployeeConfig | None = registry.get(employee_id)
    if not config:
        return None
    return EmployeeRuntime().build_system_prompt(config=config)


def chat_command(
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("", "--model", help="Model to use (default: Codex default)"),
    employee: str = typer.Option(
        "", "--employee", "-e", help="Chat as a specific employee (by ID). Defaults to CEO context."
    ),
) -> None:
    """Interactive chat session with full team context injected."""
    # Build system prompt
    if employee:
        system_prompt = _build_employee_system_prompt(employee)
        if system_prompt is None:
            console.print(f"[red]Employee '{employee}' not found.[/red]")
            raise typer.Exit(code=1)
        console.print(f"[dim]Launching as employee: {employee}[/dim]")
    else:
        system_prompt = _CEO_SYSTEM_PROMPT
        console.print("[dim]Launching with CEO orchestrator context.[/dim]")

    # Write prompt to temp file (same mechanism as SubAgentManager)
    prompt_file: str | None = None
    try:
        fd, prompt_file = tempfile.mkstemp(suffix=".txt", prefix="ag_chat_")
        os.write(fd, system_prompt.encode())
        os.close(fd)

        cmd = ["codex"]
        if full_auto:
            # workspace-write sandbox blocks port binding (EPERM on listen).
            # Bypass all sandboxing so the agent can start dev servers.
            cmd.append("--dangerously-bypass-approvals-and-sandbox")
        if model:
            cmd.extend(["-m", model])
        cmd.extend(["-c", f"model_instructions_file={prompt_file}"])

        result = subprocess.run(cmd, env=os.environ, check=False)  # noqa: S603
        sys.exit(result.returncode)
    except FileNotFoundError:
        console.print(
            "[red]Error:[/red] codex CLI not found. Install with: npm install -g @openai/codex"
        )
        raise typer.Exit(code=1) from None
    except KeyboardInterrupt:
        pass
    finally:
        if prompt_file:
            Path(prompt_file).unlink(missing_ok=True)
