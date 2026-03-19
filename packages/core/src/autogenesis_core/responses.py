"""Responses API data types and conversation format translation."""

from __future__ import annotations

import json
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from autogenesis_core.models import Message


class ResponseEventType(StrEnum):
    """SSE event types from the OpenAI Responses API."""

    RESPONSE_CREATED = "response.created"
    IN_PROGRESS = "response.in_progress"
    OUTPUT_ITEM_ADDED = "response.output_item.added"
    CONTENT_PART_ADDED = "response.content_part.added"
    OUTPUT_TEXT_DELTA = "response.output_text.delta"
    OUTPUT_TEXT_DONE = "response.output_text.done"
    CONTENT_PART_DONE = "response.content_part.done"
    FUNCTION_CALL_ARGS_DELTA = "response.function_call_arguments.delta"
    FUNCTION_CALL_ARGS_DONE = "response.function_call_arguments.done"
    OUTPUT_ITEM_DONE = "response.output_item.done"
    COMPLETED = "response.completed"
    FAILED = "response.failed"
    RATE_LIMITED = "response.rate_limited"
    UNKNOWN = "unknown"


class ResponseEvent(BaseModel):
    """A parsed SSE event from the Responses API."""

    event_type: ResponseEventType
    data: dict[str, Any] = Field(default_factory=dict)


class APIError(BaseModel):
    """Structured error from the Responses API."""

    status_code: int
    error_type: str
    message: str
    retry_after: float | None = None


class AuthenticationError(Exception):
    """401 from the API — credentials invalid or expired."""


class RateLimitError(Exception):
    """429 from the API — rate limited."""

    def __init__(self, message: str, retry_after: float | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class ServerError(Exception):
    """5xx from the API — server-side failure."""


def parse_sse_event(event_type: str, data: str) -> ResponseEvent:
    """Parse a raw SSE event into a ResponseEvent."""
    try:
        parsed_type = ResponseEventType(event_type)
    except ValueError:
        parsed_type = ResponseEventType.UNKNOWN

    try:
        parsed_data = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        parsed_data = {"raw": data}

    return ResponseEvent(event_type=parsed_type, data=parsed_data)


def messages_to_response_input(messages: list[Message]) -> list[dict[str, Any]]:
    """Translate internal Message list to Responses API input items."""
    items: list[dict[str, Any]] = []

    for msg in messages:
        if msg.role == "user":
            items.append(
                {
                    "role": "user",
                    "content": [{"type": "input_text", "text": msg.content}],
                }
            )
        elif msg.role == "assistant":
            if msg.tool_calls:
                items.extend(
                    {
                        "type": "function_call",
                        "name": tc.name,
                        "arguments": json.dumps(tc.arguments),
                        "call_id": tc.id,
                    }
                    for tc in msg.tool_calls
                )
            elif msg.content:
                items.append(
                    {
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": msg.content}],
                    }
                )
        elif msg.role == "tool":
            items.append(
                {
                    "type": "function_call_output",
                    "call_id": msg.tool_call_id or "",
                    "output": msg.content,
                }
            )

    return items
