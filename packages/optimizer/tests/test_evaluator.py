"""Tests for prompt evaluator."""

from __future__ import annotations

from autogenesis_optimizer.evaluator import GoldenTest, PromptEvaluator


class TestPromptEvaluator:
    def test_golden_tests_all_pass(self):
        evaluator = PromptEvaluator()
        tests = [
            GoldenTest(
                input_text="Hello",
                expected_contains=["hello"],
            ),
        ]
        result = evaluator.run_golden_tests("Say hello to the user.", tests)
        assert result.overall_score == 1.0

    def test_golden_tests_failure(self):
        evaluator = PromptEvaluator()
        tests = [
            GoldenTest(
                input_text="Hello",
                expected_contains=["xyznonexistent"],
            ),
        ]
        result = evaluator.run_golden_tests("Be helpful.", tests)
        assert result.overall_score == 0.0

    def test_compare_versions(self):
        evaluator = PromptEvaluator(metrics=["quality"])
        baseline = evaluator.run_golden_tests("V1", [GoldenTest(input_text="v1")])
        candidate = evaluator.run_golden_tests(
            "V2 v1",
            [GoldenTest(input_text="v1", expected_contains=["v1"])],
        )

        diffs = evaluator.compare_versions(baseline, candidate)
        assert "quality" in diffs
        assert "overall" in diffs

    def test_regression_detection(self):
        evaluator = PromptEvaluator(metrics=["quality"])
        good = evaluator.run_golden_tests(
            "complete v1", [GoldenTest(input_text="v1", expected_contains=["v1"])]
        )
        bad = evaluator.run_golden_tests(
            "empty", [GoldenTest(input_text="v1", expected_contains=["nonexistent"])]
        )

        assert evaluator.detect_regression(good, bad) is True
        assert evaluator.detect_regression(bad, good) is False
