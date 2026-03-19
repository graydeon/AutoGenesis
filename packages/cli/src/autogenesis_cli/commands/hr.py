"""HR subcommand group — manage the employee roster."""

from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

hr_app = typer.Typer(name="hr", help="Manage agent employees.", no_args_is_help=True)


def _get_roster_dir() -> Path:
    """Get the global employee roster directory from config."""
    from autogenesis_core.config import load_config

    cfg = load_config()
    if cfg.employees.global_roster_path:
        return Path(cfg.employees.global_roster_path)
    xdg = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    return Path(xdg) / "autogenesis" / "employees"


@hr_app.command(name="list")
def hr_list() -> None:
    """List all employees."""
    from autogenesis_employees.registry import EmployeeRegistry

    reg = EmployeeRegistry(global_dir=_get_roster_dir())
    employees = reg.list_all()

    table = Table(title="Agent Employees")
    table.add_column("ID", style="dim")
    table.add_column("Title")
    table.add_column("Status")

    for emp in employees:
        style = "green" if emp.status == "active" else "dim"
        table.add_row(emp.id, emp.title, emp.status, style=style)

    console.print(table)


@hr_app.command(name="hire")
def hr_hire(
    title: str = typer.Argument(help="Job title for the new employee"),
    based_on: str = typer.Option("", "--based-on", help="Clone from existing employee"),
) -> None:
    """Hire a new employee."""
    from autogenesis_employees.hr import hire

    roster = _get_roster_dir()
    path = hire(title, based_on=based_on or None, template_dir=roster, target_dir=roster)
    console.print(f"[green]Hired {title}![/green] Config: {path}")


@hr_app.command(name="fire")
def hr_fire(employee_id: str = typer.Argument(help="Employee ID to archive")) -> None:
    """Archive an employee."""
    from autogenesis_employees.hr import fire

    fire(employee_id, config_dir=_get_roster_dir())
    console.print(f"[yellow]{employee_id} archived.[/yellow]")


@hr_app.command(name="train")
def hr_train(
    employee_id: str = typer.Argument(help="Employee ID to train"),
    directive: str = typer.Option(..., "--directive", help="Training directive to add"),
) -> None:
    """Add a training directive to an employee."""
    from autogenesis_employees.hr import train

    train(employee_id, directive, config_dir=_get_roster_dir())
    console.print(f"[green]Trained {employee_id}:[/green] {directive}")


@hr_app.command(name="show")
def hr_show(employee_id: str = typer.Argument(help="Employee ID to show")) -> None:
    """Show an employee's config."""
    from autogenesis_employees.registry import EmployeeRegistry

    reg = EmployeeRegistry(global_dir=_get_roster_dir())
    emp = reg.get(employee_id)
    if not emp:
        console.print(f"[red]Employee {employee_id} not found.[/red]")
        raise typer.Exit(code=1)
    import yaml

    console.print(yaml.dump(emp.model_dump(), default_flow_style=False))
