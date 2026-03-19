"""Abstract tool interface."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import structlog
from autogenesis_core.events import Event, EventType, get_event_bus
from autogenesis_core.models import ToolDefinition

if TYPE_CHECKING:
    from autogenesis_core.models import ToolCall

logger = structlog.get_logger()


class Tool(ABC):
    """Abstract base for all tools."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""

    @property
    @abstractmethod
    def parameters(self) -> dict[str, Any]:
        """JSON Schema for tool arguments."""

    @property
    def hidden(self) -> bool:
        """Whether this tool is hidden from normal context."""
        return False

    @property
    def token_cost_estimate(self) -> int:
        """Estimated tokens for tool definition in context."""
        return 0

    def to_definition(self) -> ToolDefinition:
        """Convert to ToolDefinition for model context."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
            token_cost_estimate=self.token_cost_estimate,
        )

    def to_responses_api_format(self) -> dict[str, Any]:
        """Convert tool to Responses API function format."""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }

    async def __call__(self, tool_call: ToolCall) -> str:
        """Execute tool with event emission and error handling."""
        bus = get_event_bus()
        bus.emit(
            Event(
                event_type=EventType.TOOL_CALL_START,
                data={"tool": self.name, "id": tool_call.id},
            )
        )

        start = time.monotonic()
        try:
            result = await self.execute(tool_call.arguments)
        except Exception as exc:  # noqa: BLE001
            result = f"Error: {exc}"
            logger.warning("tool_error", tool=self.name, error=str(exc))
        finally:
            elapsed_ms = (time.monotonic() - start) * 1000
            bus.emit(
                Event(
                    event_type=EventType.TOOL_CALL_END,
                    data={
                        "tool": self.name,
                        "id": tool_call.id,
                        "elapsed_ms": round(elapsed_ms, 1),
                    },
                )
            )

        return str(result)

    @abstractmethod
    async def execute(self, arguments: dict[str, Any]) -> str:
        """Execute the tool. Implementations must return a string."""
