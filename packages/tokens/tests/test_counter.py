"""Tests for token counter."""

from __future__ import annotations

from autogenesis_tokens.counter import count_message_tokens, count_tokens, estimate_cost


class TestTokenCounter:
    def test_count_tokens_string(self):
        count = count_tokens("Hello, world!")
        assert count > 0

    def test_count_tokens_empty(self):
        count = count_tokens("")
        assert count == 0

    def test_count_message_tokens(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        count = count_message_tokens(messages)
        assert count > 0

    def test_estimate_cost(self):
        cost = estimate_cost(input_tokens=1000, output_tokens=500, model="gpt-4o")
        assert isinstance(cost, float)
        assert cost >= 0
