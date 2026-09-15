"""Unit tests for workflow state, actor snapshots, and remediation proposals."""

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

from contracts.workflow import (
    StepExecutionStatus,
    WorkflowDefinitionRef,
    WorkflowStatus,
)

from workflow.state import (
    RemediationProposal,
    RemediationType,
    StepExecutionRecord,
    WorkflowActorSnapshot,
    WorkflowState,
)


class TestWorkflowState(unittest.TestCase):
    """Verify serialization, integrity, and immutability of WorkflowState and sub-models."""

    def setUp(self) -> None:
        self.actor = WorkflowActorSnapshot(
            actor_id="agent_alice",
            role="support_tier_1",
            permissions=("read_customer", "request_concession"),
        )
        self.definition_ref = WorkflowDefinitionRef(
            definition_id="account_remediation",
            version="1.0.0",
        )

    def test_actor_snapshot_validation(self) -> None:
        with self.assertRaises(ValueError):
            WorkflowActorSnapshot(actor_id="", role="support")
        with self.assertRaises(ValueError):
            WorkflowActorSnapshot(actor_id="alice", role=" ")

        snap = WorkflowActorSnapshot(actor_id="bob", role="admin")
        d = snap.to_dict()
        self.assertEqual(d["actor_id"], "bob")
        restored = WorkflowActorSnapshot.from_dict(d)
        self.assertEqual(restored.actor_id, "bob")
        self.assertEqual(restored.role, "admin")

    def test_remediation_proposal_roundtrip(self) -> None:
        prop = RemediationProposal(
            proposal_type=RemediationType.FEE_CREDIT,
            summary="Approve $20 waiver",
            suggested_arguments={"amount_cents": 2000, "customer_id": "cust-1"},
            requires_approval=True,
        )
        d = prop.to_dict()
        restored = RemediationProposal.from_dict(d)
        self.assertEqual(restored.proposal_type, RemediationType.FEE_CREDIT)
        self.assertEqual(restored.suggested_arguments["amount_cents"], 2000)
        self.assertTrue(restored.requires_approval)

    def test_step_execution_record_roundtrip(self) -> None:
        rec = StepExecutionRecord(
            step_name="intake",
            attempt=1,
            status=StepExecutionStatus.SUCCEEDED,
            started_at=1000.0,
            completed_at=1001.5,
            outcome_type="valid_input",
            execution_receipt_ids=("rec-1", "rec-2"),
        )
        d = rec.to_dict()
        restored = StepExecutionRecord.from_dict(d)
        self.assertEqual(restored.step_name, "intake")
        self.assertEqual(restored.status, StepExecutionStatus.SUCCEEDED)
        self.assertEqual(restored.execution_receipt_ids, ("rec-1", "rec-2"))

    def test_workflow_state_checksum_and_serialization(self) -> None:
        state = WorkflowState(
            workflow_id="wf-test-01",
            definition=self.definition_ref,
            status=WorkflowStatus.RUNNING,
            current_step="intake_validation",
            initiator_actor=self.actor,
            checkpoint_version=1,
            domain_context={"customer_id": "cust-101"},
        )
        state_with_cksum = state.with_updated_checksum()
        self.assertTrue(len(state_with_cksum.checksum) == 64)  # SHA-256 hex string

        # Verify round-trip serialization
        serialized = state_with_cksum.to_dict()
        restored = WorkflowState.from_dict(serialized)

        self.assertEqual(restored.workflow_id, "wf-test-01")
        self.assertEqual(restored.status, WorkflowStatus.RUNNING)
        self.assertEqual(restored.current_step, "intake_validation")
        self.assertEqual(restored.initiator_actor.actor_id, "agent_alice")
        self.assertEqual(restored.checkpoint_version, 1)
        self.assertEqual(restored.checksum, state_with_cksum.checksum)
        self.assertEqual(restored.compute_checksum(), state_with_cksum.checksum)


if __name__ == "__main__":
    unittest.main()
