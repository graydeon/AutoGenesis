"""Prompt evaluation via LLM-as-judge."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvaluationResult:
    """Result from evaluating a prompt version."""

    scores: dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    test_results: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class GoldenTest:
    """A golden test case for prompt evaluation."""

    input_text: str
    expected_contains: list[str] = field(default_factory=list)
    expected_not_contains: list[str] = field(default_factory=list)


class PromptEvaluator:
    """Evaluate prompt quality using test suites and metrics."""

    def __init__(
        self,
        metrics: list[str] | None = None,
    ) -> None:
        self._metrics = metrics or [
            "task_completion",
            "token_efficiency",
            "safety_compliance",
            "coherence",
        ]

    def run_golden_tests(
        self,
        prompt_content: str,
        tests: list[GoldenTest],
    ) -> EvaluationResult:
        """Run golden test suite against a prompt.

        Note: In v0.1.0 this does local validation only (no LLM calls).
        LLM-as-judge scoring will be added in a future version.
        """
        results = []
        passed = 0
        for test in tests:
            # Check if prompt + test input would produce expected output patterns
            combined = f"{prompt_content}\n{test.input_text}".lower()
            test_passed = True

            for phrase in test.expected_contains:
                if phrase.lower() not in combined:
                    test_passed = False

            for phrase in test.expected_not_contains:
                if phrase.lower() in combined:
                    test_passed = False

            results.append(
                {
                    "input": test.input_text,
                    "passed": test_passed,
                }
            )
            if test_passed:
                passed += 1

        total = len(tests) if tests else 1
        score = passed / total

        return EvaluationResult(
            scores=dict.fromkeys(self._metrics, score),
            overall_score=score,
            test_results=results,
        )

    def compare_versions(
        self,
        baseline: EvaluationResult,
        candidate: EvaluationResult,
    ) -> dict[str, float]:
        """Compare two evaluation results. Positive = improvement."""
        diffs = {}
        for metric in self._metrics:
            base = baseline.scores.get(metric, 0.0)
            cand = candidate.scores.get(metric, 0.0)
            diffs[metric] = cand - base
        diffs["overall"] = candidate.overall_score - baseline.overall_score
        return diffs

    def detect_regression(
        self,
        baseline: EvaluationResult,
        candidate: EvaluationResult,
        threshold: float = -0.1,
    ) -> bool:
        """Return True if candidate is a regression from baseline."""
        return (candidate.overall_score - baseline.overall_score) < threshold
