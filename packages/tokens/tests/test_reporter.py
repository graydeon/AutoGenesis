"""Tests for token usage reporter."""

from __future__ import annotations

import json

from autogenesis_core.models import TokenUsage
from autogenesis_tokens.reporter import TokenReporter


class TestTokenReporter:
    def test_per_session_summary(self):
        reporter = TokenReporter()
        reporter.record(TokenUsage(input_tokens=100, output_tokens=50))
        reporter.record(TokenUsage(input_tokens=200, output_tokens=100))

        summary = reporter.summary()
        assert summary["total_input_tokens"] == 300
        assert summary["total_output_tokens"] == 150
        assert summary["total_tokens"] == 450
        assert summary["api_calls"] == 2

    def test_per_tool_breakdown(self):
        reporter = TokenReporter()
        reporter.record(TokenUsage(input_tokens=50, output_tokens=25), model="gpt-4o", tool="bash")
        reporter.record(TokenUsage(input_tokens=50, output_tokens=25), model="gpt-4o", tool="bash")
        reporter.record(
            TokenUsage(input_tokens=100, output_tokens=50), model="gpt-4o", tool="file_read"
        )

        breakdown = reporter.tool_breakdown()
        assert breakdown["bash"]["calls"] == 2
        assert breakdown["bash"]["tokens"] == 150
        assert breakdown["file_read"]["calls"] == 1

    def test_json_export(self):
        reporter = TokenReporter()
        reporter.record(TokenUsage(input_tokens=100, output_tokens=50))

        output = reporter.to_json()
        data = json.loads(output)
        assert "summary" in data
        assert "tool_breakdown" in data
        assert "entries" in data

    def test_empty_reporter(self):
        reporter = TokenReporter()
        summary = reporter.summary()
        assert summary["total_tokens"] == 0
        assert summary["api_calls"] == 0
