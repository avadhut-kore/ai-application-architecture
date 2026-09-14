"""Contracts for AI evaluation pipelines and benchmarks."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence


class EvaluationStatus(str, Enum):
    """Execution status of an evaluation scenario or suite."""

    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class EvaluationMetric:
    """Individual metric scored during evaluation."""

    name: str
    score: float
    threshold: float
    passed: bool
    details: Optional[Mapping[str, Any]] = field(default=None)


@dataclass(frozen=True)
class EvaluationScenarioResult:
    """Result of evaluating a single scenario from an evaluation dataset."""

    scenario_id: str
    status: EvaluationStatus
    metrics: Sequence[EvaluationMetric]
    actual_output: str
    expected_output: Optional[str] = None
    metadata: Optional[Mapping[str, Any]] = field(default=None)


@dataclass(frozen=True)
class EvaluationSummary:
    """Aggregated results across an evaluation suite execution."""

    total_scenarios: int
    passed_scenarios: int
    failed_scenarios: int
    pass_rate: float
    results: Sequence[EvaluationScenarioResult]
    overall_status: EvaluationStatus

    @classmethod
    def from_results(
        cls, results: Sequence[EvaluationScenarioResult], pass_threshold: float = 0.90
    ) -> EvaluationSummary:
        """Calculate summary statistics from a sequence of scenario results."""
        total = len(results)
        if total == 0:
            return cls(
                total_scenarios=0,
                passed_scenarios=0,
                failed_scenarios=0,
                pass_rate=0.0,
                results=(),
                overall_status=EvaluationStatus.INCONCLUSIVE,
            )

        passed = sum(1 for r in results if r.status == EvaluationStatus.PASSED)
        failed = sum(1 for r in results if r.status == EvaluationStatus.FAILED)
        rate = passed / total
        status = EvaluationStatus.PASSED if rate >= pass_threshold else EvaluationStatus.FAILED

        return cls(
            total_scenarios=total,
            passed_scenarios=passed,
            failed_scenarios=failed,
            pass_rate=round(rate, 4),
            results=tuple(results),
            overall_status=status,
        )
