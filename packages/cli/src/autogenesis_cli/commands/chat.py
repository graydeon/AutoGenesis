"""Chat command — interactive REPL with session persistence."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console

from autogenesis_cli.display import ApprovalManager, print_text_delta, print_text_done

console = Console()
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def chat_command(
    full_auto: bool = typer.Option(False, "--full-auto", help="Bypass all approval prompts"),
    model: str = typer.Option("gpt-5.3-codex", "--model", help="Model to use"),
) -> None:
    """Interactive chat session with the agent."""
    asyncio.run(_chat_async(full_auto, model))


async def _chat_async(full_auto: bool, model: str) -> None:
    from autogenesis_core.client import CodexClient, CodexClientConfig
    from autogenesis_core.config import load_config
    from autogenesis_core.credentials import EnvCredentialProvider
    from autogenesis_core.loop import AgentLoop
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
    for tool_cls in [
        BashTool,
        FileReadTool,
        FileWriteTool,
        FileEditTool,
        GlobTool,
        GrepTool,
        ListDirTool,
        ThinkTool,
    ]:
        registry.register(tool_cls())

    instructions = (_PROMPTS_DIR / "default.txt").read_text()
    approval = ApprovalManager(full_auto=full_auto)

    console.print("[blue]AutoGenesis Chat[/blue] (type 'exit' or Ctrl+C to quit)\n")

    try:
        while True:
            try:
                user_input = console.input("[green]You>[/green] ").strip()
            except EOFError:
                break

            if not user_input or user_input.lower() in ("exit", "quit"):
                break

            tool_defs = registry.get_definitions_for_context()

            async def tool_executor(tc: object) -> str:
                tool = registry.get(tc.name)  # type: ignore[attr-defined]
                if not tool:
                    return f"Unknown tool: {tc.name}"  # type: ignore[attr-defined]
                if approval.should_prompt(tc.name) and not approval.prompt_user(  # type: ignore[attr-defined]
                    tc.name,
                    tc.arguments,  # type: ignore[attr-defined]
                ):
                    return "Tool execution denied by user"
                return await tool.execute(tc.arguments)  # type: ignore[attr-defined]

            loop = AgentLoop(
                client=client,
                tool_executor=tool_executor,
                tool_definitions=tool_defs,
                instructions=instructions,
                on_text_delta=print_text_delta,
            )

            result = await loop.run(user_input)
            print_text_done()
            console.print(f"[dim]({result.usage.total_tokens} tokens)[/dim]\n")

    except KeyboardInterrupt:
        console.print("\n[yellow]Session ended.[/yellow]")
    finally:
        await client.close()
