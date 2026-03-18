"""Cross-provider token counting."""

from __future__ import annotations

from typing import Any

import litellm


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in a text string for a given model."""
    result: int = litellm.token_counter(model=model, text=text)
    return result


def count_message_tokens(messages: list[dict[str, Any]], model: str = "gpt-4o") -> int:
    """Count tokens in a list of messages for a given model."""
    result: int = litellm.token_counter(model=model, messages=messages)
    return result


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4o",
) -> float:
    """Estimate cost in USD for given token counts and model."""
    try:
        return litellm.completion_cost(
            model=model,
            prompt="",
            completion="",
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
        )
    except Exception:  # noqa: BLE001
        return 0.0
