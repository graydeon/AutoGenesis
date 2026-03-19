"""Core data models for AutoGenesis."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class ToolCall(BaseModel):
    """A tool invocation requested by the model."""

    id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:12]}")
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """A conversation message."""

    role: str  # "user", "assistant", "tool"
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None  # for role="tool" messages


class ToolResult(BaseModel):
    """Result from executing a tool."""

    tool_call_id: str
    output: str
    is_error: bool = False


class TokenUsage(BaseModel):
    """Token usage for a single API call."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    @model_validator(mode="after")
    def compute_total(self) -> TokenUsage:
        self.total_tokens = self.input_tokens + self.output_tokens
        return self

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
        )


class ToolDefinition(BaseModel):
    """Schema for a tool exposed to the model."""

    name: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    token_cost_estimate: int = 0


class AgentState(BaseModel):
    """Serializable state for an agent session."""

    session_id: str = Field(default_factory=lambda: uuid4().hex[:16])
    messages: list[Message] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
