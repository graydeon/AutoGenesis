"""Agent loop — core execution engine.

Iterates: send messages to CodexClient → parse response → execute tool calls → repeat.
Streams text deltas to an optional display callback.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

from autogenesis_core.events import Event, EventType, get_event_bus
from autogenesis_core.models import Message, TokenUsage, ToolCall, ToolDefinition
from autogenesis_core.responses import ResponseEventType

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from autogenesis_core.client import CodexClient

logger = structlog.get_logger()


class AgentLoopResult(BaseModel):
    """Result from a complete agent loop run."""

    output: str = ""
    usage: TokenUsage = Field(default_factory=TokenUsage)
    iterations: int = 0
    tool_calls_made: int = 0


class AgentLoop:
    """Async agent loop that drives the CodexClient."""

    def __init__(  # noqa: PLR0913
        self,
        client: CodexClient,
        tool_executor: Callable[[ToolCall], Awaitable[str]] | None = None,
        tool_definitions: list[ToolDefinition] | None = None,
        instructions: str = "",
        max_iterations: int = 50,
        on_text_delta: Callable[[str], None] | None = None,
    ) -> None:
        self._client = client
        self._tool_executor = tool_executor
        self._tool_definitions = tool_definitions or []
        self._instructions = instructions
        self._max_iterations = max_iterations
        self._on_text_delta = on_text_delta

    async def _process_stream(
        self,
        messages: list[Message],
    ) -> tuple[list[str], list[ToolCall], TokenUsage]:
        """Stream one response from the client, returning text parts, tool calls, and usage."""
        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        usage = TokenUsage()

        async for event in self._client.create_response(
            messages=messages,
            instructions=self._instructions,
            tools=self._tool_definitions if self._tool_definitions else None,
        ):
            if event.event_type == ResponseEventType.OUTPUT_TEXT_DELTA:
                delta = event.data.get("delta", "")
                text_parts.append(delta)
                if self._on_text_delta:
                    self._on_text_delta(delta)

            elif event.event_type == ResponseEventType.FUNCTION_CALL_ARGS_DONE:
                call_id = event.data.get("call_id", "")
                name = event.data.get("name", "")
                args_str = event.data.get("arguments", "{}")
                try:
                    args: dict[str, Any] = json.loads(args_str)
                except json.JSONDecodeError:
                    args = {"raw": args_str}
                tool_calls.append(ToolCall(id=call_id, name=name, arguments=args))

            elif event.event_type == ResponseEventType.COMPLETED:
                response = event.data.get("response", {})
                raw_usage = response.get("usage", {})
                usage = TokenUsage(
                    input_tokens=raw_usage.get("input_tokens", 0),
                    output_tokens=raw_usage.get("output_tokens", 0),
                    total_tokens=raw_usage.get("total_tokens", 0),
                )

        return text_parts, tool_calls, usage

    async def _execute_tool(self, tc: ToolCall) -> str:
        """Execute a single tool call, returning its output string."""
        if self._tool_executor:
            try:
                return await self._tool_executor(tc)
            except Exception as exc:  # noqa: BLE001
                return f"Error: {exc}"
        return f"Error: No tool executor configured for {tc.name}"

    async def run(self, prompt: str) -> AgentLoopResult:
        """Execute the agent loop for a given prompt."""
        bus = get_event_bus()
        messages: list[Message] = [Message(role="user", content=prompt)]
        total_usage = TokenUsage()
        total_tool_calls = 0

        bus.emit(Event(event_type=EventType.LOOP_EXECUTION_START, data={"prompt": prompt}))

        for iteration in range(1, self._max_iterations + 1):
            bus.emit(Event(event_type=EventType.MODEL_CALL_START, data={"iteration": iteration}))
            text_parts, tool_calls, step_usage = await self._process_stream(messages)
            total_usage = total_usage + step_usage
            bus.emit(Event(event_type=EventType.MODEL_CALL_END, data={"iteration": iteration}))

            if not tool_calls:
                output = "".join(text_parts)
                bus.emit(
                    Event(event_type=EventType.LOOP_EXECUTION_END, data={"output": output[:200]})
                )
                return AgentLoopResult(
                    output=output,
                    usage=total_usage,
                    iterations=iteration,
                    tool_calls_made=total_tool_calls,
                )

            content = "".join(text_parts)
            messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))

            for tc in tool_calls:
                total_tool_calls += 1
                bus.emit(Event(event_type=EventType.TOOL_CALL_START, data={"tool": tc.name}))
                result = await self._execute_tool(tc)
                messages.append(Message(role="tool", content=result, tool_call_id=tc.id))
                bus.emit(Event(event_type=EventType.TOOL_CALL_END, data={"tool": tc.name}))

        bus.emit(Event(event_type=EventType.LOOP_EXECUTION_END, data={"reason": "max_iterations"}))
        return AgentLoopResult(
            output="Max iterations reached",
            usage=total_usage,
            iterations=self._max_iterations,
            tool_calls_made=total_tool_calls,
        )
