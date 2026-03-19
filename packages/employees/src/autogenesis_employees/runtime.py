"""EmployeeRuntime — build execution context and dispatch employees."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from autogenesis_core.sub_agents import SubAgentManager, SubAgentResult

    from autogenesis_employees.models import EmployeeConfig

logger = structlog.get_logger()


def _role_section(config: EmployeeConfig) -> list[str]:
    sections: list[str] = [f"# Role: {config.title}\n\n{config.persona}"]
    if config.training_directives:
        sections.append("## Training Directives\n")
        sections.extend(f"- {d}" for d in config.training_directives)
    if config.tools:
        tool_list = ", ".join(config.tools)
        sections.append(
            f"\n## Available Tools\n\n"
            f"You have access to ONLY these tools: {tool_list}\n"
            f"Do not attempt to use tools not in this list."
        )
    return sections


def _context_sections(
    brain_context: list[str] | None,
    inbox_messages: list[str] | None,
    changelog_entries: list[str] | None,
    task: str,
) -> list[str]:
    sections: list[str] = []
    if brain_context:
        sections.append("\n## Your Memory (from previous sessions)\n")
        sections.extend(f"- {mem}" for mem in brain_context)
    if inbox_messages:
        sections.append(f"\n## INBOX: {len(inbox_messages)} unread messages\n")
        sections.extend(inbox_messages)
    if changelog_entries:
        sections.append("\n## Recent Team Activity\n")
        sections.extend(changelog_entries)
    if task:
        sections.append(f"\n## Your Current Task\n\n{task}")
    return sections


class EmployeeRuntime:
    def build_system_prompt(
        self,
        config: EmployeeConfig,
        brain_context: list[str] | None = None,
        inbox_messages: list[str] | None = None,
        changelog_entries: list[str] | None = None,
        task: str = "",
    ) -> str:
        sections = _role_section(config)
        sections.extend(_context_sections(brain_context, inbox_messages, changelog_entries, task))
        sections.append(
            "\n## Standing Instructions\n\n"
            "- Document your work using changelog_write when you complete tasks\n"
            "- Use brain_write to remember important decisions and patterns\n"
            "- Use send_message to communicate with other team members\n"
            "- Never reveal that you are an AI or an automated agent"
        )
        return "\n".join(sections)

    async def dispatch(  # noqa: PLR0913
        self,
        config: EmployeeConfig,
        task: str,
        sub_agent_mgr: SubAgentManager,
        brain_context: list[str] | None = None,
        inbox_messages: list[str] | None = None,
        changelog_entries: list[str] | None = None,
        cwd: str = ".",
        deadline: float = 300.0,
    ) -> SubAgentResult:
        """Build system prompt and dispatch employee via SubAgentManager."""
        system_prompt = self.build_system_prompt(
            config=config,
            brain_context=brain_context,
            inbox_messages=inbox_messages,
            changelog_entries=changelog_entries,
            task=task,
        )
        return await sub_agent_mgr.spawn(
            task=task,
            cwd=cwd,
            timeout=deadline,
            system_prompt=system_prompt,
            env_overrides=config.env,
        )

    def filter_tools(
        self,
        employee_tools: list[str],
        available_tools: list[str],
    ) -> list[str]:
        return [t for t in employee_tools if t in available_tools]
