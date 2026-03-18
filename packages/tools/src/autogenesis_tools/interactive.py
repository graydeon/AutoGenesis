"""User interaction tool."""

from __future__ import annotations

from typing import Any

from autogenesis_tools.base import Tool


class AskUserTool(Tool):
    """Ask the user for input."""

    @property
    def name(self) -> str:
        return "ask_user"

    @property
    def description(self) -> str:
        return "Ask the user a question and wait for their response."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "Question to ask the user"},
                "mode": {
                    "type": "string",
                    "enum": ["free_text", "yes_no", "select"],
                    "description": "Input mode (default: free_text)",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Options for select mode",
                },
            },
            "required": ["question"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 150

    async def execute(self, arguments: dict[str, Any]) -> str:
        """Ask user for input via stdin."""
        question = arguments["question"]
        mode = arguments.get("mode", "free_text")

        if mode == "yes_no":
            response = input(f"{question} (yes/no): ")
            return response.strip().lower()

        if mode == "select":
            options = arguments.get("options", [])
            prompt_parts = [question]
            for i, opt in enumerate(options, 1):
                prompt_parts.append(f"  {i}. {opt}")
            prompt_parts.append("Selection: ")
            response = input("\n".join(prompt_parts))
            return response.strip()

        response = input(f"{question}: ")
        return response.strip()
