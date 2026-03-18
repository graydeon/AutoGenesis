"""Rich console output formatting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

if TYPE_CHECKING:
    from autogenesis_core.models import TokenUsage

console = Console()


def print_markdown(text: str) -> None:
    """Render text as markdown."""
    console.print(Markdown(text))


def print_assistant(text: str) -> None:
    """Print assistant response with formatting."""
    console.print(Panel(Markdown(text), title="Assistant", border_style="blue"))


def print_token_usage(usage: TokenUsage) -> None:
    """Print token usage summary."""
    console.print(
        f"[dim]Tokens: {usage.input_tokens} in / {usage.output_tokens} out"
        f" | Cost: ${usage.total_cost_usd:.4f}[/dim]"
    )


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")
