"""Shell execution tool."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from autogenesis_security.sandbox import CommandPolicy, SubprocessSandbox

from autogenesis_tools.base import Tool

if TYPE_CHECKING:
    from pathlib import Path

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_DEFAULT_TIMEOUT = 30.0
_MAX_OUTPUT_CHARS = 2000
_DEFAULT_ALLOWED_COMMANDS = frozenset(
    {
        "cat",
        "echo",
        "find",
        "git",
        "grep",
        "head",
        "ls",
        "mypy",
        "pwd",
        "pytest",
        "python",
        "python3",
        "rg",
        "ruff",
        "sed",
        "sleep",
        "tail",
        "uv",
        "wc",
    }
)


class BashTool(Tool):
    """Execute shell commands with timeout and output truncation."""

    def __init__(
        self,
        *,
        workspace_root: str | Path | None = None,
        allowed_commands: frozenset[str] | None = _DEFAULT_ALLOWED_COMMANDS,
    ) -> None:
        self._sandbox = SubprocessSandbox(
            workspace_root=workspace_root,
            command_policy=CommandPolicy(allowed_commands=allowed_commands),
        )

    @property
    def name(self) -> str:
        return "bash"

    @property
    def description(self) -> str:
        return "Execute a shell command and return its output."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "number", "description": "Timeout in seconds (default 30)"},
            },
            "required": ["command"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 150

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Execute a shell command."""
        command = arguments["command"]
        timeout = float(arguments.get("timeout", _DEFAULT_TIMEOUT))

        output, return_code = await self._sandbox.execute(command, timeout=timeout)
        output = _ANSI_ESCAPE.sub("", output)

        if len(output) > _MAX_OUTPUT_CHARS:
            output = output[:_MAX_OUTPUT_CHARS] + f"\n... (truncated, {len(output)} chars total)"

        if return_code != 0:
            if "timed out" in output.lower():
                return f"Error: Command timed out after {timeout}s"
            if output.startswith("Security policy denied command:"):
                return f"Error: {output}"
            return f"Exit code {return_code}\n{output}"
        return output
