"""Unit tests for Gate D AI Evaluation Runner."""

from __future__ import annotations

import asyncio
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import sys
REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
for p in (REPO_ROOT / "building-blocks" / "python", REPO_ROOT / "examples" / "structured-generation", Path(__file__).resolve().parent.parent):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.models import CompletionRequest, CompletionResponse, UsageMetrics
from contracts.ports import TextGenerationPort
from structured_generation.service import FeedbackExtractionService

from runner import (
    DeterministicEvalStub,
    EvalScenario,
    evaluate_service,
    load_dataset,
    print_report,
)


class FailingStubClient(TextGenerationPort):
    """Client that always returns malformed responses."""

    async def generate(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(
            text="invalid json content",
            model="test-model",
            usage=UsageMetrics(input_tokens=5, output_tokens=5, total_tokens=10),
            latency_ms=1.0,
        )

    async def check_health(self) -> bool:
        return True


class TestEvaluationRunner(unittest.TestCase):
    """Test suite verifying evaluation runner functionality and Gate D scoring."""

    def setUp(self) -> None:
        self.dataset_path = Path(__file__).resolve().parent.parent / "eval_dataset.jsonl"

    def test_load_dataset_success(self) -> None:
        """Verify that the authoritative eval_dataset.jsonl loads exactly 30 scenarios."""
        scenarios = load_dataset(self.dataset_path)
        self.assertEqual(len(scenarios), 30)
        self.assertEqual(scenarios[0].id, "eval-001")
        self.assertIn(scenarios[0].scenario_type, {"normal", "boundary", "ambiguous", "adversarial"})
        self.assertTrue(scenarios[0].expected_category)

    def test_load_dataset_file_not_found(self) -> None:
        """Verify FileNotFoundError when dataset file does not exist."""
        with self.assertRaises(FileNotFoundError):
            load_dataset(Path("/nonexistent/dataset.jsonl"))

    def test_load_dataset_malformed_json(self) -> None:
        """Verify ValueError on corrupted JSON line in dataset."""
        with tempfile.NamedTemporaryFile("w", delete=False) as tf:
            tf.write('{"id": "eval-001", "scenario_type": "normal"}\nnot a json line\n')
            temp_path = Path(tf.name)

        try:
            with self.assertRaises(ValueError):
                load_dataset(temp_path)
        finally:
            temp_path.unlink()

    def test_evaluate_service_fake_mode_validates_harness(self) -> None:
        """Verify that evaluation in fake mode validates harness mechanics."""
        scenarios = load_dataset(self.dataset_path)
        stub_client = DeterministicEvalStub(scenarios)
        service = FeedbackExtractionService(client=stub_client, model="test-model")

        summary, results = asyncio.run(evaluate_service(service, scenarios, mode="fake"))

        self.assertEqual(summary.total, 30)
        self.assertEqual(len(results), 30)
        self.assertEqual(summary.schema_adherence_rate, 100.0)
        self.assertEqual(summary.category_accuracy, 100.0)
        self.assertTrue(summary.gate_d_passed)
        self.assertIn("normal", summary.type_breakdown)
        self.assertIn("adversarial", summary.type_breakdown)

    def test_gate_d_schema_threshold_boundary_failure(self) -> None:
        """Verify that 96.67% schema adherence (29/30) fails the authoritative >=98.0% threshold."""
        scenarios = load_dataset(self.dataset_path)

        # Create a stub that returns invalid JSON for exactly one scenario (eval-001)
        class OneFailureStub(TextGenerationPort):
            def __init__(self, base_stub: DeterministicEvalStub) -> None:
                self.base = base_stub

            async def generate(self, request: CompletionRequest) -> CompletionResponse:
                if scenarios[0].input in request.prompt:
                    return CompletionResponse(
                        text="corrupted {json",
                        model="test-model",
                        usage=UsageMetrics(input_tokens=10, output_tokens=5),
                    )
                return await self.base.generate(request)

            async def check_health(self) -> bool:
                return True

        stub = OneFailureStub(DeterministicEvalStub(scenarios))
        service = FeedbackExtractionService(client=stub, model="test-model", max_corrective_retries=0)
        summary, results = asyncio.run(evaluate_service(service, scenarios, mode="live"))

        self.assertEqual(summary.total, 30)
        self.assertEqual(summary.schema_valid_count, 29)
        self.assertAlmostEqual(summary.schema_adherence_rate, 96.67, places=1)
        # 96.67% is < 98.0% mandatory threshold -> MUST FAIL Gate D
        self.assertFalse(summary.gate_d_passed)

    def test_gate_d_schema_threshold_boundary_success(self) -> None:
        """Verify that 100.0% schema adherence satisfies the authoritative >=98.0% threshold."""
        scenarios = load_dataset(self.dataset_path)
        stub = DeterministicEvalStub(scenarios)
        service = FeedbackExtractionService(client=stub, model="test-model")
        summary, results = asyncio.run(evaluate_service(service, scenarios, mode="live"))

        self.assertEqual(summary.total, 30)
        self.assertEqual(summary.schema_valid_count, 30)
        self.assertEqual(summary.schema_adherence_rate, 100.0)
        self.assertTrue(summary.gate_d_passed)

    def test_evaluate_service_failing_client_fails_gate_d(self) -> None:
        """Verify that evaluation with a broken client records failures and rejects Gate D."""
        scenarios = load_dataset(self.dataset_path)
        failing_client = FailingStubClient()
        service = FeedbackExtractionService(client=failing_client, model="test-model", max_corrective_retries=0)

        summary, results = asyncio.run(evaluate_service(service, scenarios, mode="fake"))

        self.assertEqual(summary.total, 30)
        self.assertEqual(summary.schema_valid_count, 0)
        self.assertEqual(summary.schema_adherence_rate, 0.0)
        self.assertFalse(summary.gate_d_passed)
        for r in results:
            self.assertFalse(r.is_valid_schema)
            self.assertTrue(len(r.errors) > 0)

    def test_print_report_execution_and_fake_mode_wording(self) -> None:
        """Verify that print_report executes cleanly and fake mode explicitly reports NOT VERIFIED for real Gate D."""
        scenarios = load_dataset(self.dataset_path)
        stub_client = DeterministicEvalStub(scenarios)
        service = FeedbackExtractionService(client=stub_client, model="test-model")

        summary, _ = asyncio.run(evaluate_service(service, scenarios, mode="fake"))
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            print_report(summary)
            output = mock_stdout.getvalue()
            self.assertIn("AI EVALUATION REPORT", output)
            self.assertIn("Total Scenarios Evaluated: 30", output)
            self.assertIn("EVALUATION HARNESS VALIDATION: [PASS]", output)
            self.assertIn("Gate D Real-Model Evaluation:  [NOT VERIFIED]", output)

    def test_live_mode_unavailable_returns_nonzero(self) -> None:
        """Verify that run_evaluation in live mode returns non-zero (1) when daemon is unreachable."""
        from runner import run_evaluation

        exit_code = asyncio.run(
            run_evaluation(
                dataset_path=self.dataset_path,
                mode="live",
                base_url="http://localhost:59999",
                model="llama3.2",
            )
        )
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
