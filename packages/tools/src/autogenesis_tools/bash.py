"""Shell execution tool."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from autogenesis_tools.base import Tool

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")
_DEFAULT_TIMEOUT = 30.0
_MAX_OUTPUT_CHARS = 2000


class BashTool(Tool):
    """Execute shell commands with timeout and output truncation."""

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

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except TimeoutError:
            if proc is not None:
                proc.kill()
            return f"Error: Command timed out after {timeout}s"

        output = stdout.decode(errors="replace") if stdout else ""
        output = _ANSI_ESCAPE.sub("", output)

        if len(output) > _MAX_OUTPUT_CHARS:
            output = output[:_MAX_OUTPUT_CHARS] + f"\n... (truncated, {len(output)} chars total)"

        if proc.returncode != 0:
            return f"Exit code {proc.returncode}\n{output}"
        return output
