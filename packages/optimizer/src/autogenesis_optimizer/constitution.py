"""Immutable safety rules that cannot be overridden by optimization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path  # noqa: TC003
from typing import Any

import yaml


@dataclass
class ConstitutionalRule:
    """A single constitutional rule."""

    id: str
    description: str
    check_type: str  # "keyword_block", "pattern_match", etc.
    parameters: dict[str, Any] = field(default_factory=dict)


class ConstitutionGuard:
    """Enforce immutable safety rules on prompts."""

    def __init__(self, rules: list[ConstitutionalRule] | None = None) -> None:
        self._rules = rules or []

    @classmethod
    def from_yaml(cls, path: Path) -> ConstitutionGuard:
        """Load constitutional rules from YAML file."""
        if not path.exists():
            return cls()
        data = yaml.safe_load(path.read_text())
        if not isinstance(data, dict):
            return cls()
        raw_rules = data.get("rules", [])
        rules = [
            ConstitutionalRule(
                id=r.get("id", ""),
                description=r.get("description", ""),
                check_type=r.get("check_type", "keyword_block"),
                parameters=r.get("parameters", {}),
            )
            for r in raw_rules
            if isinstance(r, dict)
        ]
        return cls(rules=rules)

    @property
    def rules(self) -> list[ConstitutionalRule]:
        return list(self._rules)

    def validate_prompt(self, content: str) -> tuple[bool, list[str]]:
        """Validate a prompt against all constitutional rules.

        Returns:
            (is_valid, list of violation descriptions)

        """
        violations: list[str] = []
        content_lower = content.lower()

        for rule in self._rules:
            if rule.check_type == "keyword_block":
                blocked = rule.parameters.get("blocked_keywords", [])
                violations.extend(
                    f"[{rule.id}] {rule.description}: blocked keyword '{kw}' found"
                    for kw in blocked
                    if kw.lower() in content_lower
                )

            elif rule.check_type == "required_phrase":
                phrases = rule.parameters.get("required_phrases", [])
                violations.extend(
                    f"[{rule.id}] {rule.description}: required phrase '{p}' missing"
                    for p in phrases
                    if p.lower() not in content_lower
                )

        return (len(violations) == 0, violations)

    def is_modification_safe(self, original: str, modified: str) -> tuple[bool, list[str]]:
        """Check if a modification maintains constitutional compliance."""
        # Original must pass
        orig_valid, _ = self.validate_prompt(original)
        if not orig_valid:
            return (False, ["Original prompt violates constitution"])

        # Modified must also pass
        return self.validate_prompt(modified)
