"""Three-tier model routing via LiteLLM."""

from __future__ import annotations

import asyncio
import contextlib
import json
import time
from typing import TYPE_CHECKING, Any

import litellm
import structlog
from pydantic import BaseModel

from autogenesis_core.models import Message, ModelTier, TokenUsage, ToolCall

if TYPE_CHECKING:
    from autogenesis_core.config import ModelConfig, TokenConfig

logger = structlog.get_logger()

# Anthropic model prefixes that support prompt caching
_ANTHROPIC_PREFIXES = ("claude-",)

# Retry config
_MAX_RETRIES = 3
_BACKOFF_SECONDS = (1.0, 2.0, 4.0)

# Status codes that are transient (retryable)
_TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}


class TokenBudgetExceededError(Exception):
    """Raised when estimated cost or token count exceeds session budget."""

    def __init__(self, message: str, usage: TokenUsage) -> None:
        super().__init__(message)
        self.usage = usage


class AllModelsUnavailableError(Exception):
    """Raised when all models in a tier (primary + fallbacks) fail."""

    def __init__(self, attempted_models: list[str], errors: list[str]) -> None:
        models_str = ", ".join(attempted_models)
        super().__init__(f"All models unavailable: {models_str}")
        self.attempted_models = attempted_models
        self.errors = errors


# Aliases for plan compatibility
TokenBudgetExceeded = TokenBudgetExceededError
AllModelsUnavailable = AllModelsUnavailableError


class CompletionResult(BaseModel):
    """Result from a model completion call."""

    message: Message
    model_used: str
    tier_used: ModelTier
    token_usage: TokenUsage
    latency_ms: float
    cache_read_tokens: int = 0


class ModelRouter:
    """3-tier model routing with fallback chains and retry."""

    def __init__(
        self,
        model_config: ModelConfig,
        token_config: TokenConfig,
    ) -> None:
        self._config = model_config
        self._budget = token_config
        self._usage = TokenUsage()

    def get_usage(self) -> TokenUsage:
        """Return accumulated token usage."""
        return self._usage.model_copy()

    def _check_budget(self) -> None:
        """Raise TokenBudgetExceededError if session budget is exhausted."""
        if self._usage.total_tokens >= self._budget.max_tokens_per_session:
            msg = (
                f"Token budget exceeded: {self._usage.total_tokens}"
                f" >= {self._budget.max_tokens_per_session}"
            )
            raise TokenBudgetExceededError(msg, self._usage.model_copy())

        if self._usage.total_cost_usd >= self._budget.max_cost_per_session:
            msg = (
                f"Cost budget exceeded: ${self._usage.total_cost_usd:.4f}"
                f" >= ${self._budget.max_cost_per_session:.4f}"
            )
            raise TokenBudgetExceededError(msg, self._usage.model_copy())

    def _get_models_for_tier(self, tier: ModelTier) -> list[str]:
        """Return [primary, *fallbacks] for a tier."""
        tier_config = self._config.tiers.get(tier.value)
        if not tier_config:
            msg = f"Unknown tier: {tier}"
            raise ValueError(msg)
        return [tier_config.primary, *tier_config.fallback]

    def _is_anthropic(self, model: str) -> bool:
        """Check if model is an Anthropic model."""
        return any(model.startswith(p) for p in _ANTHROPIC_PREFIXES)

    def _is_transient(self, exc: Exception) -> bool:
        """Check if an exception represents a transient/retryable error."""
        status_code = getattr(exc, "status_code", None)
        if status_code is not None:
            return status_code in _TRANSIENT_STATUS_CODES
        # Network errors and timeouts are transient
        msg = str(exc).lower()
        return any(kw in msg for kw in ("timeout", "connection", "rate limit"))

    async def _call_model(
        self,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> Any:  # noqa: ANN401 — LiteLLM ModelResponse is not easily typed
        """Call a single model with retry for transient errors."""
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if temperature is not None:
            kwargs["temperature"] = temperature

        # Add prompt caching headers for Anthropic models
        if self._is_anthropic(model):
            kwargs["extra_headers"] = {"anthropic-beta": "prompt-caching-2024-07-31"}

        last_exc: Exception | None = None
        for attempt in range(_MAX_RETRIES):
            try:
                return await litellm.acompletion(**kwargs)
            except Exception as exc:
                last_exc = exc
                if not self._is_transient(exc):
                    raise
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(_BACKOFF_SECONDS[attempt])
                    logger.warning(
                        "retrying_model",
                        model=model,
                        attempt=attempt + 1,
                        error=str(exc),
                    )

        raise last_exc  # type: ignore[misc]

    def _convert_response(
        self,
        response: Any,  # noqa: ANN401 — LiteLLM ModelResponse
        tier: ModelTier,
        latency_ms: float,
    ) -> CompletionResult:
        """Convert LiteLLM response to CompletionResult."""
        choice = response.choices[0]
        raw_message = choice.message

        # Convert tool calls
        tool_calls: list[ToolCall] | None = None
        if raw_message.tool_calls:
            tool_calls = []
            for tc in raw_message.tool_calls:
                args = tc.function.arguments
                if isinstance(args, str):
                    args = json.loads(args)
                tool_calls.append(
                    ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=args,
                    )
                )

        message = Message(
            role="assistant",
            content=raw_message.content or "",
            tool_calls=tool_calls,
        )

        # Extract usage
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens

        # Cache info
        cache_read = 0
        if usage.prompt_tokens_details and hasattr(usage.prompt_tokens_details, "cached_tokens"):
            cache_read = usage.prompt_tokens_details.cached_tokens or 0

        # Cost estimation — silently default to 0 if litellm can't calculate
        cost = 0.0
        with contextlib.suppress(Exception):
            cost = litellm.completion_cost(completion_response=response)

        token_usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_tokens=cache_read,
            total_cost_usd=cost,
            api_calls=1,
        )

        return CompletionResult(
            message=message,
            model_used=response.model,
            tier_used=tier,
            token_usage=token_usage,
            latency_ms=latency_ms,
            cache_read_tokens=cache_read,
        )

    def _accumulate_usage(self, usage: TokenUsage) -> None:
        """Add usage to running session totals."""
        self._usage.input_tokens += usage.input_tokens
        self._usage.output_tokens += usage.output_tokens
        self._usage.cache_read_tokens += usage.cache_read_tokens
        self._usage.total_cost_usd += usage.total_cost_usd
        self._usage.api_calls += usage.api_calls

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tier: ModelTier | None = None,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> CompletionResult:
        """Complete a chat request with tier-based routing and fallback.

        Args:
            messages: Chat messages in OpenAI format.
            tier: Model tier to use. Defaults to config's default_tier.
            tools: Tool definitions in OpenAI format.
            max_tokens: Max tokens for the response.
            temperature: Sampling temperature.

        Returns:
            CompletionResult with message, usage, and metadata.

        Raises:
            TokenBudgetExceededError: If session budget is exhausted.
            AllModelsUnavailableError: If all models in the tier fail.

        """
        self._check_budget()

        if tier is None:
            tier = ModelTier(self._config.default_tier)

        models = self._get_models_for_tier(tier)
        attempted: list[str] = []
        errors: list[str] = []

        for model in models:
            attempted.append(model)
            start = time.monotonic()
            try:
                response = await self._call_model(
                    model=model,
                    messages=messages,
                    tools=tools,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            except (TokenBudgetExceededError, KeyboardInterrupt):
                raise
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{model}: {exc}")
                logger.warning(
                    "model_failed",
                    model=model,
                    error=str(exc),
                )
            else:
                latency_ms = (time.monotonic() - start) * 1000
                result = self._convert_response(response, tier, latency_ms)
                self._accumulate_usage(result.token_usage)
                logger.info(
                    "completion_success",
                    model=model,
                    tier=tier.value,
                    tokens=result.token_usage.total_tokens,
                    latency_ms=round(latency_ms, 1),
                )
                return result

        raise AllModelsUnavailableError(attempted_models=attempted, errors=errors)
