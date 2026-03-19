"""Tests for core data models."""

from __future__ import annotations

from autogenesis_core.models import (
    AgentState,
    Message,
    TokenUsage,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestMessage:
    def test_user_message(self):
        m = Message(role="user", content="hello")
        assert m.role == "user"
        assert m.content == "hello"

    def test_assistant_message_with_tool_calls(self):
        tc = ToolCall(name="bash", arguments={"command": "ls"})
        m = Message(role="assistant", content="", tool_calls=[tc])
        assert len(m.tool_calls) == 1

    def test_tool_call_id_generated(self):
        tc = ToolCall(name="bash", arguments={})
        assert tc.id.startswith("call_")
        assert len(tc.id) == 17  # "call_" + 12 hex chars


class TestToolResult:
    def test_success(self):
        tr = ToolResult(tool_call_id="call_abc", output="done")
        assert tr.output == "done"
        assert tr.is_error is False

    def test_error(self):
        tr = ToolResult(tool_call_id="call_abc", output="fail", is_error=True)
        assert tr.is_error is True


class TestTokenUsage:
    def test_defaults(self):
        t = TokenUsage()
        assert t.input_tokens == 0
        assert t.output_tokens == 0
        assert t.total_tokens == 0

    def test_total_computed(self):
        t = TokenUsage(input_tokens=100, output_tokens=50)
        assert t.total_tokens == 150


class TestAgentState:
    def test_empty_state(self):
        s = AgentState()
        assert s.messages == []
        assert s.metadata == {}

    def test_serialization_roundtrip(self):
        s = AgentState(session_id="test-123")
        data = s.model_dump()
        restored = AgentState.model_validate(data)
        assert restored.session_id == "test-123"


class TestToolDefinition:
    def test_basic(self):
        td = ToolDefinition(
            name="bash",
            description="Run shell commands",
            parameters={"type": "object", "properties": {}},
        )
        assert td.name == "bash"

    def test_no_tier_requirement(self):
        """ModelTier is removed; ToolDefinition has no tier_requirement field."""
        td = ToolDefinition(name="bash", description="test", parameters={})
        assert not hasattr(td, "tier_requirement")
