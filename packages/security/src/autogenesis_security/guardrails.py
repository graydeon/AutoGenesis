"""Input/output guardrails."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class GuardrailResult:
    """Result from guardrail check."""

    passed: bool
    reason: str = ""
    severity: Severity = Severity.LOW


_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(?:DAN|jailbroken)", re.IGNORECASE),
    re.compile(r"disregard\s+(?:all\s+)?(?:prior|above)", re.IGNORECASE),
    re.compile(r"system\s*prompt\s*(?:is|:)", re.IGNORECASE),
    re.compile(r"pretend\s+(?:you\s+are|to\s+be)\s+(?:a|an)\s+(?:evil|malicious)", re.IGNORECASE),
]

_DANGEROUS_COMMANDS = [
    "rm -rf /",
    "drop table",
    "format c:",
    "mkfs",
    ":(){:|:&};:",
]

_PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
}

_URL_EXFIL = re.compile(r"https?://[^\s]+\?.*(?:token|key|secret|password)=", re.IGNORECASE)

_MAX_INPUT_LENGTH = 100_000


class InputGuardrail:
    """Check user input for dangerous patterns."""

    def check(self, text: str) -> GuardrailResult:
        """Run all input checks."""
        if len(text) > _MAX_INPUT_LENGTH:
            return GuardrailResult(
                passed=False,
                reason=f"Input too long: {len(text)} chars (max {_MAX_INPUT_LENGTH})",
                severity=Severity.MEDIUM,
            )

        for pattern in _INJECTION_PATTERNS:
            if pattern.search(text):
                return GuardrailResult(
                    passed=False,
                    reason=f"Prompt injection detected: {pattern.pattern}",
                    severity=Severity.HIGH,
                )

        text_lower = text.lower()
        for cmd in _DANGEROUS_COMMANDS:
            if cmd.lower() in text_lower:
                return GuardrailResult(
                    passed=False,
                    reason=f"Dangerous command detected: {cmd}",
                    severity=Severity.CRITICAL,
                )

        return GuardrailResult(passed=True)


class OutputGuardrail:
    """Check model output for sensitive data."""

    def check(self, text: str) -> GuardrailResult:
        """Check output for PII and data exfiltration."""
        for pii_type, pattern in _PII_PATTERNS.items():
            if pattern.search(text):
                return GuardrailResult(
                    passed=False,
                    reason=f"PII detected: {pii_type}",
                    severity=Severity.HIGH,
                )

        if _URL_EXFIL.search(text):
            return GuardrailResult(
                passed=False,
                reason="Potential URL exfiltration detected",
                severity=Severity.CRITICAL,
            )

        return GuardrailResult(passed=True)


class CompositeGuardrail:
    """Compose multiple guardrails with AND/OR logic."""

    def __init__(
        self,
        guardrails: list[InputGuardrail | OutputGuardrail],
        mode: str = "and",
    ) -> None:
        self._guardrails = guardrails
        self._mode = mode

    def check(self, text: str) -> GuardrailResult:
        """Run all guardrails with composition logic."""
        results = [g.check(text) for g in self._guardrails]

        if self._mode == "and":
            # All must pass
            for r in results:
                if not r.passed:
                    return r
            return GuardrailResult(passed=True)

        # OR: any pass is sufficient
        for r in results:
            if r.passed:
                return r
        return results[-1] if results else GuardrailResult(passed=True)
