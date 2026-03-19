"""Sub-agent tool — delegates tasks to Codex CLI subprocesses."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from autogenesis_tools.base import Tool

if TYPE_CHECKING:
    from autogenesis_core.sub_agents import SubAgentManager


class SubAgentTool(Tool):
    """Delegate a task to a Codex CLI sub-agent."""

    def __init__(self, sub_agent_manager: SubAgentManager | None = None) -> None:
        self._manager = sub_agent_manager

    @property
    def name(self) -> str:
        return "sub_agent"

    @property
    def description(self) -> str:
        return (
            "Delegate a task to a Codex CLI sub-agent. The sub-agent runs in its own "
            "process with full autonomy. Use for independent subtasks that can run in parallel."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Task description for the sub-agent"},
                "cwd": {"type": "string", "description": "Working directory for the sub-agent"},
            },
            "required": ["task"],
        }

    @property
    def hidden(self) -> bool:
        return False

    @property
    def token_cost_estimate(self) -> int:
        return 200

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._manager is None:
            return "Error: SubAgentManager not configured"

        result = await self._manager.spawn(
            task=arguments["task"],
            cwd=arguments.get("cwd", "."),
        )

        if result.success:
            return f"Sub-agent completed successfully:\n{result.output}"
        if result.timed_out:
            return "Sub-agent timed out"
        return f"Sub-agent failed (exit code {result.exit_code}):\n{result.output}"
