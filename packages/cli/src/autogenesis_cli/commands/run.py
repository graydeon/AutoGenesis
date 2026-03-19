"""Run command — single-shot task execution."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console

from autogenesis_cli.display import ApprovalManager, print_error

console = Console()

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def run_command(
    prompt: str = typer.Argument("", help="Task to execute"),
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("gpt-5.3-codex", "--model", help="Model to use"),
    quiet: bool = typer.Option(False, "--quiet", help="Minimal output"),
) -> None:
    """Execute a single task and exit."""
    if not prompt:
        if not sys.stdin.isatty():
            prompt = sys.stdin.read().strip()
        if not prompt:
            print_error("No prompt provided. Usage: autogenesis run 'your task'")
            raise typer.Exit(code=1)

    asyncio.run(_run_async(prompt, full_auto, model, quiet))


async def _run_async(prompt: str, full_auto: bool, model: str, quiet: bool) -> None:
    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.loop import AgentLoop
    from autogenesis_core.models import ToolCall
    from autogenesis_tools.base import Tool
    from autogenesis_tools.bash import BashTool
    from autogenesis_tools.filesystem import (
        FileEditTool,
        FileReadTool,
        FileWriteTool,
        GlobTool,
        GrepTool,
        ListDirTool,
    )
    from autogenesis_tools.registry import ToolRegistry
    from autogenesis_tools.think import ThinkTool

    load_config()
    provider = EnvCredentialProvider()
    client_config = CodexClientConfig(model=model)
    client = CodexClient(credential_provider=provider, config=client_config)

    registry = ToolRegistry()
    tool_classes: list[type[Tool]] = [
        BashTool,
        FileReadTool,
        FileWriteTool,
        FileEditTool,
        GlobTool,
        GrepTool,
        ListDirTool,
        ThinkTool,
    ]
    for tool_cls in tool_classes:
        registry.register(tool_cls())

    instructions = (_PROMPTS_DIR / "default.txt").read_text()
    approval = ApprovalManager(full_auto=full_auto)

    tool_defs = registry.get_definitions_for_context()

    async def tool_executor(tc: ToolCall) -> str:
        tool = registry.get(tc.name)
        if not tool:
            return f"Unknown tool: {tc.name}"
        if approval.should_prompt(tc.name) and not approval.prompt_user(
            tc.name,
            tc.arguments,
        ):
            return "Tool execution denied by user"
        return await tool.execute(tc.arguments)

    loop = AgentLoop(
        client=client,
        tool_executor=tool_executor,
        tool_definitions=tool_defs,
        instructions=instructions,
    )

    try:
        result = await loop.run(prompt)
        if not quiet:
            console.print(f"\n[dim]Tokens: {result.usage.total_tokens}[/dim]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled.[/yellow]")
    finally:
        await client.close()
