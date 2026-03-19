"""Send message tool for inter-employee communication."""

from __future__ import annotations

import os
from typing import Any

from autogenesis_employees.models import InboxMessage

from autogenesis_tools.base import Tool


class SendMessageTool(Tool):
    def __init__(self, inbox_manager: Any = None) -> None:  # noqa: ANN401
        self._inbox = inbox_manager

    @property
    def name(self) -> str:
        return "send_message"

    @property
    def description(self) -> str:
        return (
            "Send an async message to another team member."
            " They will receive it on their next session."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "string", "description": "Recipient employee ID"},
                "subject": {"type": "string", "description": "Message subject"},
                "body": {"type": "string", "description": "Message body"},
            },
            "required": ["to", "subject", "body"],
        }

    @property
    def token_cost_estimate(self) -> int:
        return 100

    async def execute(self, arguments: dict[str, Any]) -> str:
        if self._inbox is None:
            return "Error: InboxManager not configured"
        msg = InboxMessage(
            from_employee=os.environ.get("ROLE", "unknown"),
            to_employee=arguments["to"],
            subject=arguments["subject"],
            body=arguments["body"],
        )
        await self._inbox.send(msg)
        return f"Message sent to {arguments['to']}: {arguments['subject']}"
