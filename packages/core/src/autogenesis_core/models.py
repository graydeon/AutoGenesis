"""Pydantic data models for agent state, messages, tools."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class ContentBlock(BaseModel):
    """A content block within a message."""

    type: Literal["text", "image", "tool_use", "tool_result"]
    text: str | None = None
    tool_use_id: str | None = None
    tool_name: str | None = None
    input: dict[str, Any] | None = None


class ToolCall(BaseModel):
    """A tool invocation request from the model."""

    id: str = Field(default_factory=lambda: f"call_{uuid4().hex[:12]}")
    name: str
    arguments: dict[str, Any]


class Message(BaseModel):
    """A single message in the conversation."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None
    tool_call_id: str | None = None
    token_count: int | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ToolResult(BaseModel):
    """Result from executing a tool call."""

    tool_call_id: str
    output: str
    error: str | None = None
    token_count: int | None = None
    execution_time_ms: float | None = None


class TokenUsage(BaseModel):
    """Tracks token consumption across API calls."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    total_cost_usd: float = 0.0
    api_calls: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed (input + output)."""
        return self.input_tokens + self.output_tokens


class AgentState(BaseModel):
    """Complete agent state -- serializable, restorable."""

    session_id: str = Field(default_factory=lambda: uuid4().hex)
    messages: list[Message] = []
    active_tools: list[str] = []
    token_usage: TokenUsage = Field(default_factory=TokenUsage)
    model_config_name: str = "standard"
    metadata: dict[str, Any] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModelTier(StrEnum):
    """Model routing tiers."""

    FAST = "fast"
    STANDARD = "standard"
    PREMIUM = "premium"


class ToolDefinition(BaseModel):
    """Definition of a tool for model context."""

    name: str
    description: str
    parameters: dict[str, Any]
    tier_requirement: ModelTier = ModelTier.FAST
    token_cost_estimate: int = 0
    hidden: bool = False


class PromptVersion(BaseModel):
    """A versioned prompt template."""

    version: str
    content: str
    checksum: str
    parent_version: str | None = None
    metrics: dict[str, float] = {}
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = False
    is_constitutional: bool = False
