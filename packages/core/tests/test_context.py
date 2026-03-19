"""Tests for context window management."""

from __future__ import annotations

from autogenesis_core.context import ContextManager
from autogenesis_core.events import EventBus, EventType
from autogenesis_core.models import Message, ToolDefinition


def _make_messages(count: int) -> list[Message]:
    """Create alternating user/assistant messages."""
    msgs = []
    for i in range(count):
        role = "user" if i % 2 == 0 else "assistant"
        msgs.append(Message(role=role, content=f"Message {i}"))
    return msgs


class TestContextManager:
    def test_few_messages_returns_all(self):
        cm = ContextManager(max_tokens=10_000)
        system = "You are helpful."
        messages = _make_messages(4)

        result = cm.build_context(system_prompt=system, messages=messages)

        # System prompt + 4 messages
        assert len(result) == 5
        assert result[0].role == "system"
        assert result[0].content == system

    def test_many_messages_truncated_to_window(self):
        cm = ContextManager(max_tokens=10_000, max_turns=10)
        system = "You are helpful."
        messages = _make_messages(60)

        result = cm.build_context(system_prompt=system, messages=messages)

        # System prompt + last 10 turns (20 messages)
        assert result[0].role == "system"
        # Should have truncated — fewer than 60 + 1
        assert len(result) < 61
        # Last message should be preserved
        assert result[-1].content == messages[-1].content

    def test_system_prompt_never_dropped(self):
        cm = ContextManager(max_tokens=500, max_turns=5)
        system = "You are helpful."
        messages = _make_messages(50)

        result = cm.build_context(system_prompt=system, messages=messages)

        assert result[0].role == "system"
        assert result[0].content == system

    def test_tool_definitions_included(self):
        cm = ContextManager(max_tokens=10_000)
        system = "You are helpful."
        messages = _make_messages(4)
        tools = [
            ToolDefinition(
                name="bash",
                description="Execute commands",
                parameters={"type": "object"},
            )
        ]

        result = cm.build_context(system_prompt=system, messages=messages, tool_definitions=tools)

        # System prompt + 4 messages (tools passed separately, not in message list)
        assert len(result) == 5

    def test_token_budget_respected(self):
        cm = ContextManager(max_tokens=100)
        system = "System"
        messages = _make_messages(50)

        result = cm.build_context(system_prompt=system, messages=messages)

        # Should have fewer messages to stay under budget
        # Each short message estimates to _DEFAULT_TOKEN_ESTIMATE (50), so result should be small
        assert len(result) < len(messages) + 1

    def test_truncation_emits_event(self):
        bus = EventBus()
        events_received = []
        bus.subscribe(EventType.CONTEXT_WINDOW_TRUNCATION, events_received.append)

        cm = ContextManager(max_tokens=100, max_turns=5, event_bus=bus)
        system = "System"
        messages = _make_messages(50)

        cm.build_context(system_prompt=system, messages=messages)

        assert len(events_received) == 1
        assert events_received[0].data["dropped_count"] > 0
