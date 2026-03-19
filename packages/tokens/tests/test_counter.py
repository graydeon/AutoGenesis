"""Tests for token counter."""

from __future__ import annotations

import pytest
from autogenesis_tokens.counter import count_message_tokens, count_tokens, estimate_cost


class TestTokenCounter:
    def test_count_tokens_raises_not_implemented(self):
        with pytest.raises(NotImplementedError, match="deferred to post-MVP"):
            count_tokens("Hello, world!")

    def test_count_message_tokens_raises_not_implemented(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        with pytest.raises(NotImplementedError, match="deferred to post-MVP"):
            count_message_tokens(messages)

    def test_estimate_cost_raises_not_implemented(self):
        with pytest.raises(NotImplementedError, match="deferred to post-MVP"):
            estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o")
