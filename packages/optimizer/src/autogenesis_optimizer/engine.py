"""Prompt optimization orchestrator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from autogenesis_optimizer.constitution import ConstitutionGuard
    from autogenesis_optimizer.evaluator import EvaluationResult, GoldenTest, PromptEvaluator
    from autogenesis_optimizer.versioning import PromptVersionManager


@dataclass
class OptimizationResult:
    """Result from an optimization run."""

    improved: bool
    original_score: float
    best_score: float
    best_candidate: str
    candidates_tested: int
    violations: list[str] = field(default_factory=list)


class PromptOptimizer:
    """Critique-revise prompt optimization with constitutional safety.

    v0.1.0: Generates candidates via simple text transformations.
    Future: LLM-based critique-revise.
    """

    def __init__(
        self,
        version_manager: PromptVersionManager,
        evaluator: PromptEvaluator,
        constitution: ConstitutionGuard | None = None,
        max_candidates: int = 3,
    ) -> None:
        self._versions = version_manager
        self._evaluator = evaluator
        self._constitution = constitution
        self._max_candidates = max_candidates

    def _generate_candidates(self, content: str) -> list[str]:
        """Generate candidate prompt variations.

        v0.1.0: Simple transformations. Future: LLM-based critique-revise.
        """
        candidates = []

        # Candidate 1: Add clarity instruction
        candidates.append(f"{content}\n\nBe clear and concise in your responses.")

        # Candidate 2: Add step-by-step instruction
        candidates.append(f"{content}\n\nThink step by step before responding.")

        # Candidate 3: Add safety reminder
        candidates.append(f"{content}\n\nAlways verify before taking destructive actions.")

        return candidates[: self._max_candidates]

    def optimize(
        self,
        prompt_name: str,  # noqa: ARG002
        current_content: str,
        tests: list[GoldenTest],
    ) -> OptimizationResult:
        """Run optimization: generate candidates, evaluate, promote best."""
        # Evaluate baseline
        baseline = self._evaluator.run_golden_tests(current_content, tests)

        candidates = self._generate_candidates(current_content)
        best_candidate = current_content
        best_score = baseline.overall_score
        best_eval: EvaluationResult = baseline
        all_violations: list[str] = []

        for candidate in candidates:
            # Constitutional check
            if self._constitution:
                is_safe, violations = self._constitution.validate_prompt(candidate)
                if not is_safe:
                    all_violations.extend(violations)
                    continue

            # Evaluate candidate
            result = self._evaluator.run_golden_tests(candidate, tests)

            if result.overall_score > best_score:
                best_score = result.overall_score
                best_candidate = candidate
                best_eval = result  # noqa: F841

        improved = best_score > baseline.overall_score

        return OptimizationResult(
            improved=improved,
            original_score=baseline.overall_score,
            best_score=best_score,
            best_candidate=best_candidate,
            candidates_tested=len(candidates),
            violations=all_violations,
        )
