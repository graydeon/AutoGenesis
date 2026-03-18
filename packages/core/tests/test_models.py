"""Tests for core Pydantic models."""

from __future__ import annotations

from datetime import datetime

import pytest
from autogenesis_core.models import (
    AgentState,
    ContentBlock,
    Message,
    ModelTier,
    PromptVersion,
    TokenUsage,
    ToolCall,
    ToolDefinition,
    ToolResult,
)


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert isinstance(msg.timestamp, datetime)

    def test_create_assistant_with_tool_calls(self):
        tc = ToolCall(name="bash", arguments={"command": "ls"})
        msg = Message(role="assistant", content="", tool_calls=[tc])
        assert len(msg.tool_calls) == 1
        assert msg.tool_calls[0].name == "bash"

    def test_json_roundtrip(self):
        msg = Message(role="system", content="You are helpful.")
        data = msg.model_dump_json()
        restored = Message.model_validate_json(data)
        assert restored.role == msg.role
        assert restored.content == msg.content

    def test_invalid_role_rejected(self):
        with pytest.raises(Exception):
            Message(role="invalid", content="test")

    def test_content_as_blocks(self):
        blocks = [ContentBlock(type="text", text="Hello")]
        msg = Message(role="user", content=blocks)
        assert isinstance(msg.content, list)
        assert msg.content[0].text == "Hello"


class TestToolCall:
    def test_auto_generated_id(self):
        tc = ToolCall(name="bash", arguments={"cmd": "ls"})
        assert tc.id.startswith("call_")
        assert len(tc.id) == 17

    def test_explicit_id(self):
        tc = ToolCall(id="custom_id", name="bash", arguments={})
        assert tc.id == "custom_id"


class TestToolResult:
    def test_success_result(self):
        tr = ToolResult(tool_call_id="call_abc", output="file.txt")
        assert tr.error is None
        assert tr.output == "file.txt"

    def test_error_result(self):
        tr = ToolResult(tool_call_id="call_abc", output="", error="Not found")
        assert tr.error == "Not found"


class TestTokenUsage:
    def test_total_tokens(self):
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

    def test_defaults_zero(self):
        usage = TokenUsage()
        assert usage.total_tokens == 0
        assert usage.total_cost_usd == 0.0
        assert usage.api_calls == 0


class TestAgentState:
    def test_create_default(self):
        state = AgentState()
        assert len(state.session_id) == 32
        assert state.messages == []
        assert state.token_usage.total_tokens == 0

    def test_json_roundtrip(self):
        state = AgentState()
        state.messages.append(Message(role="user", content="hi"))
        data = state.model_dump_json()
        restored = AgentState.model_validate_json(data)
        assert len(restored.messages) == 1
        assert restored.session_id == state.session_id


class TestModelTier:
    def test_enum_values(self):
        assert ModelTier.FAST == "fast"
        assert ModelTier.STANDARD == "standard"
        assert ModelTier.PREMIUM == "premium"


class TestToolDefinition:
    def test_create(self):
        td = ToolDefinition(
            name="bash",
            description="Execute shell commands",
            parameters={"type": "object", "properties": {"command": {"type": "string"}}},
        )
        assert td.name == "bash"
        assert td.tier_requirement == ModelTier.FAST
        assert td.token_cost_estimate == 0
        assert td.hidden is False


class TestPromptVersion:
    def test_checksum_deterministic(self):
        pv1 = PromptVersion(version="1.0.0", content="Hello", checksum="abc")
        pv2 = PromptVersion(version="1.0.0", content="Hello", checksum="abc")
        assert pv1.checksum == pv2.checksum

    def test_constitutional_flag(self):
        pv = PromptVersion(
            version="1.0.0",
            content="Never delete system files",
            checksum="xyz",
            is_constitutional=True,
        )
        assert pv.is_constitutional is True
        assert pv.is_active is False


class TestContentBlock:
    def test_text_block(self):
        cb = ContentBlock(type="text", text="Hello")
        assert cb.type == "text"
        assert cb.text == "Hello"

    def test_tool_use_block(self):
        cb = ContentBlock(
            type="tool_use",
            tool_use_id="call_123",
            tool_name="bash",
            input={"command": "ls"},
        )
        assert cb.type == "tool_use"
        assert cb.tool_name == "bash"
