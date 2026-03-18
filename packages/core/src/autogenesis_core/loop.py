"""Master agent execution loop."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

import structlog
from pydantic import BaseModel, Field

from autogenesis_core.context import ContextManager
from autogenesis_core.events import Event, EventType, get_event_bus
from autogenesis_core.models import AgentState, Message, TokenUsage, ToolResult
from autogenesis_core.router import TokenBudgetExceededError
from autogenesis_core.state import StatePersistence

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from pathlib import Path

    from autogenesis_core.config import ModelConfig, TokenConfig
    from autogenesis_core.models import ModelTier, ToolCall
    from autogenesis_core.router import ModelRouter

logger = structlog.get_logger()

_DEFAULT_MAX_ITERATIONS = 50


class AgentLoopResult(BaseModel):
    """Result from running the agent loop."""

    final_message: Message
    state: AgentState
    iterations: int
    total_token_usage: TokenUsage
    tool_calls_made: int = 0
    tool_results: list[ToolResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AgentLoop:
    """Single-threaded async agent loop following Claude Code pattern."""

    def __init__(  # noqa: PLR0913
        self,
        router: ModelRouter,
        tool_executor: Callable[[ToolCall], Coroutine[Any, Any, str]],
        system_prompt: str,
        model_config: ModelConfig,
        token_config: TokenConfig,
        state: AgentState | None = None,
        state_dir: Path | None = None,
        max_context_tokens: int = 100_000,
    ) -> None:
        self._router = router
        self._tool_executor = tool_executor
        self._system_prompt = system_prompt
        self._state = state or AgentState()
        self._persistence = StatePersistence(base_dir=state_dir) if state_dir else None
        self._context = ContextManager(
            max_tokens=max_context_tokens,
            event_bus=get_event_bus(),
        )
        self._model_config = model_config
        self._token_config = token_config

    def _save_state(self) -> None:
        """Persist state if persistence is configured."""
        if self._persistence:
            self._persistence.save(self._state)

    def _emit(self, event_type: EventType, data: dict[str, Any] | None = None) -> None:
        """Emit an event on the global bus."""
        get_event_bus().emit(Event(event_type=event_type, data=data or {}))

    async def run(
        self,
        user_message: str,
        tier: ModelTier | None = None,
        max_iterations: int = _DEFAULT_MAX_ITERATIONS,
    ) -> AgentLoopResult:
        """Run the agent loop until completion or limit.

        Args:
            user_message: The user's input message.
            tier: Model tier to use. Defaults to config's default_tier.
            max_iterations: Maximum loop iterations before stopping.

        Returns:
            AgentLoopResult with final message, state, and metadata.

        """
        # Append user message
        self._state.messages.append(Message(role="user", content=user_message))

        total_usage = TokenUsage()
        total_tool_calls = 0
        all_tool_results: list[ToolResult] = []
        warnings: list[str] = []
        iterations = 0
        last_message = Message(role="assistant", content="")

        self._emit(EventType.LOOP_EXECUTION_START, {"session_id": self._state.session_id})

        try:
            for iterations in range(1, max_iterations + 1):
                self._emit(
                    EventType.LOOP_EXECUTION_ITERATION,
                    {"iteration": iterations},
                )

                # Build context
                context = self._context.build_context(
                    system_prompt=self._system_prompt,
                    messages=self._state.messages,
                )

                # Convert messages to dicts for router
                messages_dicts = [{"role": m.role, "content": m.content} for m in context]

                # Call model
                self._emit(EventType.MODEL_CALL_START, {"tier": str(tier)})
                try:
                    result = await self._router.complete(
                        messages=messages_dicts,
                        tier=tier,
                    )
                except TokenBudgetExceededError as exc:
                    warnings.append(f"Token budget exceeded: {exc}")
                    break

                self._emit(
                    EventType.MODEL_CALL_END,
                    {"model": result.model_used, "tokens": result.token_usage.total_tokens},
                )

                # Accumulate usage
                total_usage.input_tokens += result.token_usage.input_tokens
                total_usage.output_tokens += result.token_usage.output_tokens
                total_usage.total_cost_usd += result.token_usage.total_cost_usd
                total_usage.api_calls += result.token_usage.api_calls

                # Store assistant message
                last_message = result.message
                self._state.messages.append(last_message)

                # Check for tool calls
                if not last_message.tool_calls:
                    break

                # Execute tools sequentially
                for tool_call in last_message.tool_calls:
                    self._emit(
                        EventType.TOOL_CALL_START,
                        {"tool": tool_call.name, "id": tool_call.id},
                    )

                    try:
                        output = await self._tool_executor(tool_call)
                    except Exception as exc:  # noqa: BLE001
                        output = f"Error: {exc}"

                    tool_result = ToolResult(
                        tool_call_id=tool_call.id,
                        output=str(output),
                    )
                    all_tool_results.append(tool_result)
                    total_tool_calls += 1

                    # Add tool result as message
                    self._state.messages.append(
                        Message(
                            role="tool",
                            content=tool_result.output,
                            tool_call_id=tool_call.id,
                        )
                    )

                    self._emit(
                        EventType.TOOL_CALL_END,
                        {"tool": tool_call.name, "id": tool_call.id},
                    )

                # Save state after each iteration
                self._save_state()

            else:
                # max_iterations exhausted
                warnings.append(f"Max_iterations ({max_iterations}) reached without completion")

        except asyncio.CancelledError:
            warnings.append("Cancelled by user")
        finally:
            self._save_state()
            self._emit(
                EventType.LOOP_EXECUTION_END,
                {"iterations": iterations, "tool_calls": total_tool_calls},
            )

        # Update state usage
        self._state.token_usage = total_usage

        return AgentLoopResult(
            final_message=last_message,
            state=self._state,
            iterations=iterations,
            total_token_usage=total_usage,
            tool_calls_made=total_tool_calls,
            tool_results=all_tool_results,
            warnings=warnings,
        )
