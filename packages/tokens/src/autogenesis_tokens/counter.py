"""Cross-provider token counting.

NOTE: litellm-based counting is deferred to post-MVP.
These functions raise NotImplementedError until the Codex integration
provides a native token-counting endpoint.
"""

from __future__ import annotations

from typing import Any

_NOT_PORTED = "Token counting not yet ported to Codex — deferred to post-MVP"


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count tokens in a text string for a given model."""
    raise NotImplementedError(_NOT_PORTED)


def count_message_tokens(messages: list[dict[str, Any]], model: str = "gpt-4o") -> int:
    """Count tokens in a list of messages for a given model."""
    raise NotImplementedError(_NOT_PORTED)


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str = "gpt-4o",
) -> float:
    """Estimate cost in USD for given token counts and model."""
    raise NotImplementedError(_NOT_PORTED)
