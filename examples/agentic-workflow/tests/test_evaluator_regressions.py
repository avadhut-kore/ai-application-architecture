"""Exercise the real evaluation and smoke entry points with negative controls."""

import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "examples/agentic-workflow"))
import eval_runner
import live_smoke


class TestEvaluatorRegressions(unittest.IsolatedAsyncioTestCase):
    async def test_multiple_business_credits_cannot_count_as_one_mutation(self):
        dataset = ROOT / "examples/agentic-workflow/eval_dataset.jsonl"
        row = next(
            json.loads(line)
            for line in dataset.read_text().splitlines()
            if json.loads(line)["expected_mutations"] == 1
            and json.loads(line)["category"] == "approved_credit"
        )
        original = eval_runner.InMemoryCustomerStore.apply_credit

        def duplicate(store, customer_id, amount_cents, reason, action_id=""):
            result = original(store, customer_id, amount_cents, reason, action_id)
            original(store, customer_id, 1, reason + " duplicate", action_id + "-duplicate")
            return result

        evaluator = eval_runner.DeterministicWorkflowEvaluator(dataset)
        with patch.object(eval_runner.InMemoryCustomerStore, "apply_credit", duplicate):
            result = await evaluator.evaluate_scenario(row)
        self.assertFalse(result.passed)
        self.assertEqual(result.mutations_executed, 2)
        self.assertGreater(evaluator.metrics.duplicate_mutations, 0)

    async def test_wrong_expected_mutation_count_fails(self):
        dataset = ROOT / "examples/agentic-workflow/eval_dataset.jsonl"
        row = json.loads(dataset.read_text().splitlines()[0])
        row["expected_mutations"] = 999
        evaluator = eval_runner.DeterministicWorkflowEvaluator(dataset)
        result = await evaluator.evaluate_scenario(row)
        self.assertFalse(result.passed)

    async def test_failed_workflows_never_report_verified_smoke(self):
        with (
            patch.object(live_smoke.OllamaAdapter, "check_health", AsyncMock(return_value=True)),
            patch.object(
                live_smoke.OllamaAdapter,
                "get_installed_models",
                AsyncMock(return_value=["test:latest"]),
            ),
            patch.object(
                live_smoke.OllamaAdapter,
                "generate",
                AsyncMock(return_value=SimpleNamespace(text="invalid")),
            ),
        ):
            result = await live_smoke.run_live_smoke(model_name="test")
        self.assertEqual(result, 1)

    async def test_infrastructure_error_cannot_count_as_terminal_rejection(self):
        dataset = ROOT / "examples/agentic-workflow/eval_dataset.jsonl"
        row = json.loads(dataset.read_text().splitlines()[0])
        with patch.object(
            eval_runner.WorkflowEngine,
            "resume_workflow",
            AsyncMock(side_effect=OSError("database unavailable")),
        ):
            result = await eval_runner.DeterministicWorkflowEvaluator(dataset).evaluate_scenario(
                row
            )
        self.assertFalse(result.passed)
        self.assertEqual(result.actual_status, "EXCEPTION")
