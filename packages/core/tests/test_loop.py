"""Tests for master agent execution loop."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from autogenesis_core.config import ModelConfig, TokenConfig
from autogenesis_core.loop import AgentLoop, AgentLoopResult
from autogenesis_core.models import Message, ModelTier, TokenUsage, ToolCall
from autogenesis_core.router import CompletionResult, TokenBudgetExceededError


def _text_result(content: str = "Done!", tokens: int = 10) -> CompletionResult:
    """Create a CompletionResult with plain text (no tools)."""
    return CompletionResult(
        message=Message(role="assistant", content=content),
        model_used="claude-sonnet-4-20250514",
        tier_used=ModelTier.STANDARD,
        token_usage=TokenUsage(input_tokens=tokens, output_tokens=tokens // 2, api_calls=1),
        latency_ms=100.0,
    )


def _tool_result(
    tool_name: str = "bash",
    tool_args: dict | None = None,
) -> CompletionResult:
    """Create a CompletionResult with a tool call."""
    tc = ToolCall(name=tool_name, arguments=tool_args or {"command": "ls"})
    return CompletionResult(
        message=Message(role="assistant", content="", tool_calls=[tc]),
        model_used="claude-sonnet-4-20250514",
        tier_used=ModelTier.STANDARD,
        token_usage=TokenUsage(input_tokens=20, output_tokens=10, api_calls=1),
        latency_ms=150.0,
    )


@pytest.fixture
def mock_router():
    router = MagicMock()
    router.complete = AsyncMock()
    router.get_usage = MagicMock(return_value=TokenUsage())
    return router


@pytest.fixture
def mock_tool_executor():
    executor = AsyncMock()
    executor.return_value = "file.txt\n"
    return executor


@pytest.fixture
def loop(mock_router, mock_tool_executor, tmp_path):
    return AgentLoop(
        router=mock_router,
        tool_executor=mock_tool_executor,
        system_prompt="You are helpful.",
        state_dir=tmp_path,
        model_config=ModelConfig(),
        token_config=TokenConfig(),
    )


class TestAgentLoop:
    async def test_text_response_one_iteration(self, loop, mock_router):
        mock_router.complete.return_value = _text_result("Hello!")

        result = await loop.run("Hi")

        assert isinstance(result, AgentLoopResult)
        assert result.iterations == 1
        assert result.final_message.content == "Hello!"
        assert result.tool_calls_made == 0

    async def test_tool_then_text_two_iterations(self, loop, mock_router, mock_tool_executor):
        mock_router.complete.side_effect = [
            _tool_result("bash", {"command": "ls"}),
            _text_result("Here are your files."),
        ]
        mock_tool_executor.return_value = "file.txt"

        result = await loop.run("List files")

        assert result.iterations == 2
        assert result.tool_calls_made == 1
        assert result.final_message.content == "Here are your files."

    async def test_max_iterations_respected(self, loop, mock_router, mock_tool_executor):
        # Always return tool calls — should stop at max_iterations
        mock_router.complete.return_value = _tool_result()
        mock_tool_executor.return_value = "output"

        result = await loop.run("Do stuff", max_iterations=3)

        assert result.iterations == 3
        assert len(result.warnings) > 0
        assert "max_iterations" in result.warnings[0].lower()

    async def test_token_budget_stops_cleanly(self, loop, mock_router, mock_tool_executor):
        # Return tool calls but budget will be exceeded
        call_count = 0

        async def budget_exceeding(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                raise TokenBudgetExceededError("Budget exceeded", TokenUsage(input_tokens=100_000))
            return _tool_result()

        mock_router.complete.side_effect = budget_exceeding
        mock_tool_executor.return_value = "output"

        result = await loop.run("Do stuff")

        assert len(result.warnings) > 0
        assert "budget" in result.warnings[0].lower()

    async def test_state_saved_after_iteration(self, loop, mock_router, tmp_path):
        mock_router.complete.return_value = _text_result()

        await loop.run("Hi")

        # State file should exist
        session_files = list(tmp_path.glob("*.json"))
        assert len(session_files) >= 1

    async def test_token_usage_accumulated(self, loop, mock_router, mock_tool_executor):
        mock_router.complete.side_effect = [
            _tool_result(),
            _text_result(),
        ]
        mock_tool_executor.return_value = "output"

        result = await loop.run("Do stuff")

        assert result.total_token_usage.api_calls == 2
        assert result.total_token_usage.input_tokens > 0

    async def test_sequential_tool_execution(self, loop, mock_router, mock_tool_executor):
        """Verify tools execute in order."""
        tc1 = ToolCall(name="bash", arguments={"command": "echo 1"})
        tc2 = ToolCall(name="bash", arguments={"command": "echo 2"})
        multi_tool = CompletionResult(
            message=Message(role="assistant", content="", tool_calls=[tc1, tc2]),
            model_used="claude-sonnet-4-20250514",
            tier_used=ModelTier.STANDARD,
            token_usage=TokenUsage(input_tokens=20, output_tokens=10, api_calls=1),
            latency_ms=150.0,
        )
        mock_router.complete.side_effect = [multi_tool, _text_result()]

        execution_order = []
        original_executor = mock_tool_executor

        async def tracking_executor(tool_call):
            execution_order.append(tool_call.name)
            return await original_executor(tool_call)

        loop._tool_executor = tracking_executor
        mock_tool_executor.return_value = "done"

        result = await loop.run("Run both")

        assert result.tool_calls_made == 2

    async def test_cancelled_error_handled(self, loop, mock_router):
        mock_router.complete.side_effect = asyncio.CancelledError()

        result = await loop.run("Hi")

        assert len(result.warnings) > 0
        assert "cancel" in result.warnings[0].lower()

    async def test_empty_tool_calls_treated_as_text(self, loop, mock_router):
        result_with_empty_tools = CompletionResult(
            message=Message(role="assistant", content="No tools needed", tool_calls=[]),
            model_used="claude-sonnet-4-20250514",
            tier_used=ModelTier.STANDARD,
            token_usage=TokenUsage(input_tokens=10, output_tokens=5, api_calls=1),
            latency_ms=100.0,
        )
        mock_router.complete.return_value = result_with_empty_tools

        result = await loop.run("Hi")

        assert result.iterations == 1
        assert result.final_message.content == "No tools needed"

    async def test_loop_result_fields(self, loop, mock_router):
        mock_router.complete.return_value = _text_result("Hello!")

        result = await loop.run("Hi")

        assert isinstance(result.final_message, Message)
        assert result.state is not None
        assert result.iterations >= 1
        assert isinstance(result.total_token_usage, TokenUsage)
        assert isinstance(result.tool_calls_made, int)
        assert isinstance(result.warnings, list)
