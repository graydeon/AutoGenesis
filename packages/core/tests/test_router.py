"""Tests for 3-tier model routing via LiteLLM."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from autogenesis_core.config import ModelConfig, TierConfig, TokenConfig
from autogenesis_core.models import ModelTier
from autogenesis_core.router import (
    AllModelsUnavailable,
    CompletionResult,
    ModelRouter,
    TokenBudgetExceeded,
)


def _make_litellm_response(
    content: str = "Hello!",
    model: str = "claude-sonnet-4-20250514",
    input_tokens: int = 10,
    output_tokens: int = 5,
) -> MagicMock:
    """Create a mock LiteLLM ModelResponse."""
    resp = MagicMock()
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = content
    resp.choices[0].message.tool_calls = None
    resp.model = model
    resp.usage.prompt_tokens = input_tokens
    resp.usage.completion_tokens = output_tokens
    resp.usage.prompt_tokens_details = None
    resp._response_ms = 150.0
    return resp


def _make_tool_call_response(
    model: str = "claude-sonnet-4-20250514",
) -> MagicMock:
    """Create a mock LiteLLM response with tool calls."""
    resp = MagicMock()
    tc = MagicMock()
    tc.id = "call_abc123"
    tc.function.name = "bash"
    tc.function.arguments = '{"command": "ls"}'
    resp.choices = [MagicMock()]
    resp.choices[0].message.content = None
    resp.choices[0].message.tool_calls = [tc]
    resp.model = model
    resp.usage.prompt_tokens = 20
    resp.usage.completion_tokens = 15
    resp.usage.prompt_tokens_details = None
    resp._response_ms = 200.0
    return resp


def _make_cache_response(
    model: str = "claude-sonnet-4-20250514",
) -> MagicMock:
    """Create a mock response with cache hit info."""
    resp = _make_litellm_response(model=model)
    details = MagicMock()
    details.cached_tokens = 50
    resp.usage.prompt_tokens_details = details
    return resp


@pytest.fixture
def model_config() -> ModelConfig:
    return ModelConfig(
        default_tier="standard",
        tiers={
            "fast": TierConfig(primary="gpt-4o-mini", fallback=["claude-3-5-haiku-20241022"]),
            "standard": TierConfig(primary="claude-sonnet-4-20250514", fallback=["gpt-4o"]),
            "premium": TierConfig(primary="claude-opus-4-20250918", fallback=["o3"]),
        },
    )


@pytest.fixture
def token_config() -> TokenConfig:
    return TokenConfig(
        max_tokens_per_session=100_000,
        max_cost_per_session=5.0,
    )


@pytest.fixture
def router(model_config: ModelConfig, token_config: TokenConfig) -> ModelRouter:
    return ModelRouter(model_config=model_config, token_config=token_config)


class TestModelRouter:
    @patch("autogenesis_core.router.litellm")
    async def test_selects_correct_model_for_tier(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(return_value=_make_litellm_response())
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        call_kwargs = mock_litellm.acompletion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-20250514"
        assert isinstance(result, CompletionResult)

    @patch("autogenesis_core.router.litellm")
    async def test_selects_fast_tier(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(
            return_value=_make_litellm_response(model="gpt-4o-mini")
        )
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.FAST)

        call_kwargs = mock_litellm.acompletion.call_args
        assert call_kwargs.kwargs["model"] == "gpt-4o-mini"
        assert result.tier_used == ModelTier.FAST

    @patch("autogenesis_core.router.litellm")
    async def test_selects_premium_tier(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(
            return_value=_make_litellm_response(model="claude-opus-4-20250918")
        )
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.PREMIUM)

        call_kwargs = mock_litellm.acompletion.call_args
        assert call_kwargs.kwargs["model"] == "claude-opus-4-20250918"
        assert result.tier_used == ModelTier.PREMIUM

    @patch("autogenesis_core.router.litellm")
    async def test_fallback_chain_on_primary_failure(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(
            side_effect=[
                Exception("Primary model unavailable"),
                _make_litellm_response(model="gpt-4o"),
            ]
        )
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.model_used == "gpt-4o"
        assert mock_litellm.acompletion.call_count == 2

    @patch("autogenesis_core.router.litellm")
    async def test_token_usage_accumulated(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(
            return_value=_make_litellm_response(input_tokens=100, output_tokens=50)
        )
        messages = [{"role": "user", "content": "Hi"}]

        await router.complete(messages=messages, tier=ModelTier.STANDARD)
        await router.complete(messages=messages, tier=ModelTier.STANDARD)

        usage = router.get_usage()
        assert usage.input_tokens == 200
        assert usage.output_tokens == 100
        assert usage.total_tokens == 300
        assert usage.api_calls == 2

    @patch("autogenesis_core.router.litellm")
    async def test_budget_enforcement_raises(self, mock_litellm, model_config):
        tight_budget = TokenConfig(max_tokens_per_session=50, max_cost_per_session=0.001)
        rtr = ModelRouter(model_config=model_config, token_config=tight_budget)
        # Simulate prior usage that exhausted budget
        mock_litellm.acompletion = AsyncMock(
            return_value=_make_litellm_response(input_tokens=40, output_tokens=20)
        )
        await rtr.complete(messages=[{"role": "user", "content": "Hi"}], tier=ModelTier.FAST)

        with pytest.raises(TokenBudgetExceeded):
            await rtr.complete(messages=[{"role": "user", "content": "More"}], tier=ModelTier.FAST)

    @patch("autogenesis_core.router.litellm")
    async def test_retry_on_transient_429(self, mock_litellm, router):
        rate_limit_err = Exception("Rate limit exceeded")
        rate_limit_err.status_code = 429
        mock_litellm.acompletion = AsyncMock(side_effect=[rate_limit_err, _make_litellm_response()])
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.message.content == "Hello!"
        assert mock_litellm.acompletion.call_count == 2

    @patch("autogenesis_core.router.litellm")
    async def test_no_retry_on_4xx_auth(self, mock_litellm, router):
        auth_err = Exception("Invalid API key")
        auth_err.status_code = 401
        mock_litellm.acompletion = AsyncMock(side_effect=auth_err)
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(AllModelsUnavailable):
            await router.complete(messages=messages, tier=ModelTier.STANDARD)

    @patch("autogenesis_core.router.litellm")
    async def test_all_models_unavailable(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(side_effect=Exception("Down"))
        messages = [{"role": "user", "content": "Hi"}]

        with pytest.raises(AllModelsUnavailable) as exc_info:
            await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert len(exc_info.value.attempted_models) == 2
        assert "claude-sonnet-4-20250514" in exc_info.value.attempted_models
        assert "gpt-4o" in exc_info.value.attempted_models

    @patch("autogenesis_core.router.litellm")
    async def test_prompt_caching_for_anthropic(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(return_value=_make_cache_response())
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        call_kwargs = mock_litellm.acompletion.call_args.kwargs
        # Anthropic models should get extra_headers for caching
        assert "extra_headers" in call_kwargs
        assert result.cache_read_tokens == 50

    @patch("autogenesis_core.router.litellm")
    async def test_completion_result_fields(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(return_value=_make_litellm_response())
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.message.role == "assistant"
        assert result.message.content == "Hello!"
        assert result.model_used == "claude-sonnet-4-20250514"
        assert result.tier_used == ModelTier.STANDARD
        assert result.token_usage.input_tokens == 10
        assert result.token_usage.output_tokens == 5
        assert result.latency_ms >= 0

    @patch("autogenesis_core.router.litellm")
    async def test_tool_call_response_converted(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(return_value=_make_tool_call_response())
        messages = [{"role": "user", "content": "List files"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.message.tool_calls is not None
        assert len(result.message.tool_calls) == 1
        assert result.message.tool_calls[0].name == "bash"
        assert result.message.tool_calls[0].arguments == {"command": "ls"}

    @patch("autogenesis_core.router.litellm")
    async def test_cost_estimation(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(
            return_value=_make_litellm_response(input_tokens=1000, output_tokens=500)
        )
        mock_litellm.completion_cost = MagicMock(return_value=0.0045)
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.token_usage.total_cost_usd == pytest.approx(0.0045)
        usage = router.get_usage()
        assert usage.total_cost_usd == pytest.approx(0.0045)

    @patch("autogenesis_core.router.litellm")
    async def test_retry_on_5xx(self, mock_litellm, router):
        server_err = Exception("Internal server error")
        server_err.status_code = 500
        mock_litellm.acompletion = AsyncMock(side_effect=[server_err, _make_litellm_response()])
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages, tier=ModelTier.STANDARD)

        assert result.message.content == "Hello!"
        assert mock_litellm.acompletion.call_count == 2

    @patch("autogenesis_core.router.litellm")
    async def test_default_tier_used(self, mock_litellm, router):
        mock_litellm.acompletion = AsyncMock(return_value=_make_litellm_response())
        messages = [{"role": "user", "content": "Hi"}]

        result = await router.complete(messages=messages)

        call_kwargs = mock_litellm.acompletion.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-20250514"
        assert result.tier_used == ModelTier.STANDARD
