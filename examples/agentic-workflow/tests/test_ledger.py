"""Hermetic unit tests for durable mutation ledger, stable action ID, and replay suppression."""

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import ExecutionReceipt
from contracts.workflow import MutationStatus
from workflow.approval import canonicalize_arguments
from workflow.ledger import DurableMutationRecord, generate_stable_action_id


class TestDurableMutationLedger(unittest.TestCase):
    """Verify stable action ID generation, ledger serialization, and idempotency semantics."""

    def test_generate_stable_action_id_determinism(self) -> None:
        """Same workflow, step, capability, and canonical arguments yield identical action_id."""
        wf_id = "wf-1001"
        step = "mutation_execution"
        cap = "apply_fee_credit"
        args = canonicalize_arguments({"amount": 2500, "customer_id": "cust-42"})

        id_1 = generate_stable_action_id(wf_id, step, cap, args)
        id_2 = generate_stable_action_id(wf_id, step, cap, args)

        self.assertEqual(id_1, id_2)
        self.assertTrue(id_1.startswith(f"act-{wf_id}-{step}-"))

    def test_generate_stable_action_id_argument_sensitivity(self) -> None:
        """Changed arguments yield a different action_id."""
        wf_id = "wf-1001"
        step = "mutation_execution"
        cap = "apply_fee_credit"
        args_1 = canonicalize_arguments({"amount": 2500, "customer_id": "cust-42"})
        args_2 = canonicalize_arguments({"amount": 5000, "customer_id": "cust-42"})

        id_1 = generate_stable_action_id(wf_id, step, cap, args_1)
        id_2 = generate_stable_action_id(wf_id, step, cap, args_2)

        self.assertNotEqual(id_1, id_2)

    def test_generate_stable_action_id_workflow_isolation(self) -> None:
        """Different workflow instances yield distinct action IDs for identical arguments."""
        step = "mutation_execution"
        cap = "apply_fee_credit"
        args = canonicalize_arguments({"amount": 2500, "customer_id": "cust-42"})

        id_wf1 = generate_stable_action_id("wf-001", step, cap, args)
        id_wf2 = generate_stable_action_id("wf-002", step, cap, args)

        self.assertNotEqual(id_wf1, id_wf2)

    def test_durable_mutation_record_serialization_roundtrip(self) -> None:
        """Verify full round-trip serialization of DurableMutationRecord with ExecutionReceipt."""
        receipt = ExecutionReceipt(
            action_id="act-wf-1001-mutation_execution-abcdef1234567890",
            capability_name="apply_fee_credit",
            status="succeeded",
            executed_at=1700000000.0,
            result_summary="Credited $25.00 to account cust-42",
        )
        record = DurableMutationRecord(
            action_id=receipt.action_id,
            workflow_id="wf-1001",
            step_name="mutation_execution",
            capability_name="apply_fee_credit",
            canonical_args='{"amount":2500,"customer_id":"cust-42"}',
            status=MutationStatus.EXECUTED,
            execution_receipt=receipt,
            created_at=1700000000.0,
            updated_at=1700000005.0,
        )

        d = record.to_dict()
        restored = DurableMutationRecord.from_dict(d)

        self.assertEqual(restored.action_id, record.action_id)
        self.assertEqual(restored.workflow_id, record.workflow_id)
        self.assertEqual(restored.status, MutationStatus.EXECUTED)
        self.assertIsNotNone(restored.execution_receipt)
        assert restored.execution_receipt is not None
        self.assertEqual(restored.execution_receipt.status, "succeeded")
        self.assertEqual(restored.execution_receipt.result_summary, receipt.result_summary)


if __name__ == "__main__":
    unittest.main()
