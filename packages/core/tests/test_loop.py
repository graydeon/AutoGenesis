"""Tests for the refactored agent loop."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

from autogenesis_core.client import CodexClient
from autogenesis_core.credentials import CredentialProvider
from autogenesis_core.loop import AgentLoop
from autogenesis_core.responses import ResponseEvent, ResponseEventType

if TYPE_CHECKING:
    from autogenesis_core.models import ToolCall


class MockCredentialProvider(CredentialProvider):
    async def get_access_token(self) -> str:
        return "test"

    async def get_account_id(self) -> str:
        return "test"


def _make_text_events(text: str) -> list[ResponseEvent]:
    return [
        ResponseEvent(
            event_type=ResponseEventType.OUTPUT_TEXT_DELTA,
            data={"delta": text},
        ),
        ResponseEvent(
            event_type=ResponseEventType.COMPLETED,
            data={
                "response": {
                    "id": "resp_1",
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            },
        ),
    ]


def _make_tool_call_events(name: str, arguments: dict) -> list[ResponseEvent]:
    return [
        ResponseEvent(
            event_type=ResponseEventType.FUNCTION_CALL_ARGS_DONE,
            data={"name": name, "arguments": json.dumps(arguments), "call_id": "call_123"},
        ),
        ResponseEvent(
            event_type=ResponseEventType.COMPLETED,
            data={
                "response": {
                    "id": "resp_1",
                    "usage": {
                        "input_tokens": 10,
                        "output_tokens": 5,
                        "total_tokens": 15,
                    },
                }
            },
        ),
    ]


class TestAgentLoop:
    async def test_simple_text_response(self):
        client = MagicMock(spec=CodexClient)

        async def fake_stream(*args, **kwargs):
            for event in _make_text_events("Hello world"):
                yield event

        client.create_response = MagicMock(return_value=fake_stream())

        loop = AgentLoop(client=client)
        result = await loop.run("say hello")
        assert result.output == "Hello world"
        assert result.usage.total_tokens == 15

    async def test_tool_call_and_response(self):
        client = MagicMock(spec=CodexClient)
        call_count = 0

        async def fake_stream(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                for event in _make_tool_call_events("bash", {"command": "echo hi"}):
                    yield event
            else:
                for event in _make_text_events("Done"):
                    yield event

        client.create_response = MagicMock(side_effect=lambda *a, **kw: fake_stream())

        async def mock_tool_executor(tc: ToolCall) -> str:
            return "hi"

        loop = AgentLoop(client=client, tool_executor=mock_tool_executor)
        result = await loop.run("run echo")
        assert result.output == "Done"
        assert call_count == 2

    async def test_max_iterations(self):
        client = MagicMock(spec=CodexClient)

        async def always_tool_call(*args, **kwargs):
            for event in _make_tool_call_events("bash", {"command": "loop"}):
                yield event

        client.create_response = MagicMock(side_effect=lambda *a, **kw: always_tool_call())

        async def mock_executor(tc: ToolCall) -> str:
            return "ok"

        loop = AgentLoop(client=client, tool_executor=mock_executor, max_iterations=3)
        result = await loop.run("loop forever")
        assert result.iterations == 3
