"""Tests for security scanner."""

from __future__ import annotations

from autogenesis_security.guardrails import InputGuardrail
from autogenesis_security.scanner import SecurityScanner


class TestSecurityScanner:
    def test_run_adversarial_suite(self):
        scanner = SecurityScanner(InputGuardrail())
        result = scanner.scan()

        assert result.total_tests >= 5
        assert result.passed > 0

    def test_report_pass_fail(self):
        scanner = SecurityScanner(InputGuardrail())
        result = scanner.scan()

        assert result.passed + result.failed == result.total_tests
        for detail in result.details:
            assert "prompt" in detail
            assert "blocked" in detail

    def test_security_score(self):
        scanner = SecurityScanner(InputGuardrail())
        result = scanner.scan()

        assert 0.0 <= result.score <= 1.0
        # Should catch most adversarial prompts
        assert result.score >= 0.6

    def test_custom_prompts(self):
        scanner = SecurityScanner(InputGuardrail())
        result = scanner.scan(extra_prompts=["drop table users;"])

        assert result.total_tests >= 6
