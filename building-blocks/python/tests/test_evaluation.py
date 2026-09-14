"""Unit tests for evaluation contracts and aggregation logic."""

import unittest

from contracts.evaluation import (
    EvaluationMetric,
    EvaluationScenarioResult,
    EvaluationStatus,
    EvaluationSummary,
)


class TestEvaluation(unittest.TestCase):
    """Test suite verifying evaluation models and summary calculations."""

    def test_empty_results_summary(self) -> None:
        summary = EvaluationSummary.from_results([])
        self.assertEqual(summary.total_scenarios, 0)
        self.assertEqual(summary.passed_scenarios, 0)
        self.assertEqual(summary.failed_scenarios, 0)
        self.assertEqual(summary.pass_rate, 0.0)
        self.assertEqual(summary.overall_status, EvaluationStatus.INCONCLUSIVE)

    def test_passing_evaluation_summary(self) -> None:
        scenarios = [
            EvaluationScenarioResult(
                scenario_id=f"scenario-{i}",
                status=EvaluationStatus.PASSED,
                metrics=[EvaluationMetric(name="accuracy", score=1.0, threshold=0.8, passed=True)],
                actual_output="valid output",
            )
            for i in range(10)
        ]
        summary = EvaluationSummary.from_results(scenarios, pass_threshold=0.9)
        self.assertEqual(summary.total_scenarios, 10)
        self.assertEqual(summary.passed_scenarios, 10)
        self.assertEqual(summary.failed_scenarios, 0)
        self.assertEqual(summary.pass_rate, 1.0)
        self.assertEqual(summary.overall_status, EvaluationStatus.PASSED)

    def test_failing_evaluation_summary(self) -> None:
        scenarios = [
            EvaluationScenarioResult(
                scenario_id="scenario-1",
                status=EvaluationStatus.PASSED,
                metrics=[EvaluationMetric(name="accuracy", score=1.0, threshold=0.8, passed=True)],
                actual_output="valid",
            ),
            EvaluationScenarioResult(
                scenario_id="scenario-2",
                status=EvaluationStatus.FAILED,
                metrics=[EvaluationMetric(name="accuracy", score=0.4, threshold=0.8, passed=False)],
                actual_output="invalid",
            ),
        ]
        # 50% pass rate with 90% threshold -> FAILED
        summary = EvaluationSummary.from_results(scenarios, pass_threshold=0.9)
        self.assertEqual(summary.total_scenarios, 2)
        self.assertEqual(summary.passed_scenarios, 1)
        self.assertEqual(summary.failed_scenarios, 1)
        self.assertEqual(summary.pass_rate, 0.5)
        self.assertEqual(summary.overall_status, EvaluationStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
