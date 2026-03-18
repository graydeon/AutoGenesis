"""Tests for context compression."""

from __future__ import annotations

from autogenesis_core.models import Message
from autogenesis_tokens.compression import ContextCompressor


def _make_conversation(tool_output_chars: int = 1000, turns: int = 20) -> list[Message]:
    """Create a conversation with long tool outputs."""
    msgs = []
    for i in range(turns):
        msgs.append(Message(role="user", content=f"Step {i}"))
        msgs.append(Message(role="assistant", content=f"Calling tool for step {i}"))
        msgs.append(Message(role="tool", content="x" * tool_output_chars, tool_call_id=f"call_{i}"))
    return msgs


class TestContextCompressor:
    def test_short_conversation_unchanged(self):
        compressor = ContextCompressor(recent_turns_to_keep=10)
        msgs = [
            Message(role="user", content="Hi"),
            Message(role="assistant", content="Hello!"),
        ]
        result = compressor.compress(msgs)
        assert len(result) == 2

    def test_truncates_old_tool_outputs(self):
        compressor = ContextCompressor(max_tool_output_chars=100, recent_turns_to_keep=6)
        msgs = _make_conversation(tool_output_chars=1000, turns=20)

        result = compressor.compress(msgs)

        # Check old tool outputs are truncated
        truncated_count = sum(
            1 for m in result if "truncated" in (m.content if isinstance(m.content, str) else "")
        )
        assert truncated_count > 0

    def test_recent_messages_preserved(self):
        compressor = ContextCompressor(max_tool_output_chars=100, recent_turns_to_keep=6)
        msgs = _make_conversation(tool_output_chars=1000, turns=20)

        result = compressor.compress(msgs)

        # Last 6 messages should be intact (not truncated)
        for msg in result[-6:]:
            if isinstance(msg.content, str):
                assert "truncated" not in msg.content

    def test_reduction_estimate(self):
        compressor = ContextCompressor(max_tool_output_chars=100, recent_turns_to_keep=6)
        msgs = _make_conversation(tool_output_chars=2000, turns=20)

        reduction = compressor.estimate_reduction(msgs)
        assert reduction > 0.3  # Should achieve > 30% reduction

    def test_empty_messages(self):
        compressor = ContextCompressor()
        assert compressor.estimate_reduction([]) == 0.0
