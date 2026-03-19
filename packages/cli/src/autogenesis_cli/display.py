"""Rich-based display layer for AutoGenesis CLI.

Handles streaming text output, tool call display with approval prompts,
and error/warning formatting. Headless-compatible (no TUI framework).
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel

console = Console()

# Tools that are auto-approved by default (read-only operations)
_AUTO_APPROVED_TOOLS: set[str] = {"file_read", "glob", "grep", "list_dir", "think"}

# Maximum characters to display for tool output before truncating
_MAX_OUTPUT_DISPLAY_CHARS: int = 2000


class ApprovalManager:
    """Manages tool execution approval state for a session."""

    def __init__(self, full_auto: bool = False) -> None:
        self._full_auto = full_auto
        self._session_approved: set[str] = set()

    def should_prompt(self, tool_name: str) -> bool:
        if self._full_auto:
            return False
        if tool_name in _AUTO_APPROVED_TOOLS:
            return False
        return tool_name not in self._session_approved

    def prompt_user(self, tool_name: str, arguments: dict[str, Any]) -> bool:
        args_preview = _format_args_preview(tool_name, arguments)
        console.print(f"\n[yellow][Allow][/yellow] {tool_name}: {args_preview}")
        response = console.input("[y/n/always] ").strip().lower()
        if response == "always":
            self._session_approved.add(tool_name)
            return True
        return response in ("y", "yes")


def print_text_delta(delta: str) -> None:
    """Print a streaming text delta (no newline)."""
    console.print(delta, end="", highlight=False)


def print_text_done() -> None:
    """Print a newline after streaming text is complete."""
    console.print()


def print_tool_call(tool_name: str, arguments: dict[str, Any]) -> None:
    """Display a tool call being executed."""
    args_preview = _format_args_preview(tool_name, arguments)
    console.print(f"\n[dim]> {tool_name}:[/dim] {args_preview}")


def print_tool_result(tool_name: str, output: str, is_error: bool = False) -> None:
    """Display a tool execution result."""
    style = "red" if is_error else "green"
    truncated = (
        output[:_MAX_OUTPUT_DISPLAY_CHARS] + "..."
        if len(output) > _MAX_OUTPUT_DISPLAY_CHARS
        else output
    )
    console.print(Panel(truncated, title=f"{tool_name} result", border_style=style, expand=False))


def print_error(message: str) -> None:
    """Display an error message."""
    console.print(f"[red]Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Display a warning message."""
    console.print(f"[yellow]Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[blue]{message}[/blue]")


def _format_args_preview(tool_name: str, arguments: dict[str, Any]) -> str:
    """Format tool arguments for display."""
    if tool_name == "bash":
        return str(arguments.get("command", ""))
    if tool_name in ("file_read", "file_write", "file_edit"):
        return str(arguments.get("path", ""))
    if tool_name == "sub_agent":
        return str(arguments.get("task", ""))[:100]
    return str(arguments)[:200]
