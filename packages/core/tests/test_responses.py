"""Tests for Responses API data types and conversation translation."""

from __future__ import annotations

import json

from autogenesis_core.models import Message, ToolCall
from autogenesis_core.responses import (
    APIError,
    ResponseEventType,
    messages_to_response_input,
    parse_sse_event,
)


class TestResponseEventType:
    def test_text_delta(self):
        assert ResponseEventType.OUTPUT_TEXT_DELTA == "response.output_text.delta"

    def test_function_call_done(self):
        assert ResponseEventType.FUNCTION_CALL_ARGS_DONE == "response.function_call_arguments.done"

    def test_completed(self):
        assert ResponseEventType.COMPLETED == "response.completed"


class TestParseSSEEvent:
    def test_text_delta(self):
        raw = {
            "type": "response.output_text.delta",
            "delta": "Hello",
            "sequence_number": 5,
        }
        event = parse_sse_event("response.output_text.delta", json.dumps(raw))
        assert event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA
        assert event.data["delta"] == "Hello"

    def test_function_call_done(self):
        raw = {
            "type": "response.function_call_arguments.done",
            "name": "bash",
            "arguments": '{"command": "ls"}',
            "call_id": "call_abc123",
        }
        event = parse_sse_event("response.function_call_arguments.done", json.dumps(raw))
        assert event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE
        assert event.data["name"] == "bash"

    def test_unknown_event_type(self):
        raw = {"type": "some.unknown.event"}
        event = parse_sse_event("some.unknown.event", json.dumps(raw))
        assert event.event_type == ResponseEventType.UNKNOWN


class TestMessagesToResponseInput:
    def test_user_message(self):
        messages = [Message(role="user", content="hello")]
        items = messages_to_response_input(messages)
        assert items == [{"role": "user", "content": [{"type": "input_text", "text": "hello"}]}]

    def test_assistant_with_tool_call(self):
        tc = ToolCall(id="call_abc", name="bash", arguments={"command": "ls"})
        messages = [
            Message(role="assistant", content="", tool_calls=[tc]),
        ]
        items = messages_to_response_input(messages)
        assert items[0]["type"] == "function_call"
        assert items[0]["name"] == "bash"
        assert items[0]["call_id"] == "call_abc"

    def test_tool_result(self):
        messages = [
            Message(role="tool", content="output here", tool_call_id="call_abc"),
        ]
        items = messages_to_response_input(messages)
        assert items[0]["type"] == "function_call_output"
        assert items[0]["call_id"] == "call_abc"
        assert items[0]["output"] == "output here"


class TestAPIError:
    def test_from_response(self):
        err = APIError(status_code=429, error_type="rate_limit_error", message="Too many requests")
        assert err.status_code == 429
        assert err.retry_after is None
