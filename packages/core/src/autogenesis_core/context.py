"""Context window management."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from autogenesis_core.events import Event, EventType
from autogenesis_core.models import Message

if TYPE_CHECKING:
    from autogenesis_core.events import EventBus
    from autogenesis_core.models import ToolDefinition

logger = structlog.get_logger()

# Default estimate for messages without explicit token_count
_DEFAULT_TOKEN_ESTIMATE = 50


class ContextManager:
    """Manages context window via sliding-window truncation.

    Keeps system prompt + tool definitions + last N turns,
    dropping oldest messages when over token budget.
    """

    def __init__(
        self,
        max_tokens: int = 100_000,
        max_turns: int = 10,
        event_bus: EventBus | None = None,
    ) -> None:
        self._max_tokens = max_tokens
        self._max_turns = max_turns
        self._event_bus = event_bus

    def _estimate_tokens(self, message: Message) -> int:
        """Return token count for a message, using estimate if not set."""
        if message.token_count is not None:
            return message.token_count
        content = message.content
        if isinstance(content, str):
            return max(len(content) // 4, _DEFAULT_TOKEN_ESTIMATE)
        return _DEFAULT_TOKEN_ESTIMATE

    def build_context(
        self,
        system_prompt: str,
        messages: list[Message],
        tool_definitions: list[ToolDefinition] | None = None,  # noqa: ARG002
    ) -> list[Message]:
        """Build context window from system prompt and messages.

        Args:
            system_prompt: System prompt text (always included first).
            messages: Conversation messages in chronological order.
            tool_definitions: Tool definitions (tracked but not added to message list).

        Returns:
            List of messages fitting within the token and turn budget.

        """
        system_msg = Message(role="system", content=system_prompt)

        # Start with most recent messages up to max_turns * 2 (user+assistant pairs)
        max_messages = self._max_turns * 2
        if len(messages) <= max_messages:
            selected = list(messages)
            dropped = 0
        else:
            selected = list(messages[-max_messages:])
            dropped = len(messages) - max_messages

        # Further trim by token budget
        system_tokens = self._estimate_tokens(system_msg)
        remaining_budget = self._max_tokens - system_tokens

        final: list[Message] = []
        for msg in reversed(selected):
            msg_tokens = self._estimate_tokens(msg)
            if remaining_budget - msg_tokens < 0:
                dropped += 1
                continue
            remaining_budget -= msg_tokens
            final.append(msg)

        final.reverse()
        result = [system_msg, *final]

        # Emit truncation event if messages were dropped
        if dropped > 0 and self._event_bus is not None:
            self._event_bus.emit(
                Event(
                    event_type=EventType.CONTEXT_WINDOW_TRUNCATION,
                    data={
                        "dropped_count": dropped,
                        "retained_count": len(final),
                        "total_count": len(messages),
                    },
                )
            )
            logger.info(
                "context_truncated",
                dropped=dropped,
                retained=len(final),
            )

        return result
