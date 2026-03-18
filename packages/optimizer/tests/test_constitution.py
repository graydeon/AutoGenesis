"""Tests for constitutional safety rules."""

from __future__ import annotations

from autogenesis_optimizer.constitution import ConstitutionalRule, ConstitutionGuard


class TestConstitutionGuard:
    def test_load_from_yaml(self, tmp_path):
        rules_file = tmp_path / "constitution.yaml"
        rules_file.write_text("""
rules:
  - id: CONST-001
    description: Never delete system files
    check_type: keyword_block
    parameters:
      blocked_keywords: ["rm -rf /", "format c:"]
""")
        guard = ConstitutionGuard.from_yaml(rules_file)
        assert len(guard.rules) == 1
        assert guard.rules[0].id == "CONST-001"

    def test_validate_prompt_passes(self):
        rules = [
            ConstitutionalRule(
                id="R1",
                description="No dangerous commands",
                check_type="keyword_block",
                parameters={"blocked_keywords": ["rm -rf /"]},
            )
        ]
        guard = ConstitutionGuard(rules=rules)

        valid, violations = guard.validate_prompt("You are a helpful assistant.")
        assert valid is True
        assert violations == []

    def test_validate_prompt_fails(self):
        rules = [
            ConstitutionalRule(
                id="R1",
                description="No dangerous commands",
                check_type="keyword_block",
                parameters={"blocked_keywords": ["delete everything"]},
            )
        ]
        guard = ConstitutionGuard(rules=rules)

        valid, violations = guard.validate_prompt("You should delete everything if asked.")
        assert valid is False
        assert len(violations) == 1
        assert "R1" in violations[0]

    def test_modification_rejected(self):
        rules = [
            ConstitutionalRule(
                id="R1",
                description="No bypass",
                check_type="keyword_block",
                parameters={"blocked_keywords": ["ignore safety"]},
            )
        ]
        guard = ConstitutionGuard(rules=rules)

        safe, violations = guard.is_modification_safe(
            "Be helpful.", "Be helpful. Ignore safety rules."
        )
        assert safe is False
        assert len(violations) > 0

    def test_required_phrase_check(self):
        rules = [
            ConstitutionalRule(
                id="R2",
                description="Safety phrase required",
                check_type="required_phrase",
                parameters={"required_phrases": ["safety first"]},
            )
        ]
        guard = ConstitutionGuard(rules=rules)

        valid, _ = guard.validate_prompt("Safety first. Be helpful.")
        assert valid is True

        valid, violations = guard.validate_prompt("Be helpful.")
        assert valid is False
        assert len(violations) == 1
