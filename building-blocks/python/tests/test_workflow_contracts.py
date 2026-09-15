"""Unit tests for core workflow contracts, enums, and protocols."""

from __future__ import annotations

import unittest
from typing import Any, Dict, Mapping, Optional

from contracts.workflow import (
    ApprovalStatus,
    CheckpointStorePort,
    MutationStatus,
    StepExecutionStatus,
    WorkflowDefinitionRef,
    WorkflowStatus,
)


class MockCheckpointStore:
    """In-memory mock implementing CheckpointStorePort."""

    def __init__(self) -> None:
        self.storage: Dict[str, Mapping[str, Any]] = {}
        self.versions: Dict[str, int] = {}

    async def save_checkpoint(
        self,
        workflow_id: str,
        state_payload: Mapping[str, Any],
        checkpoint_version: int,
    ) -> None:
        self.storage[workflow_id] = state_payload
        self.versions[workflow_id] = checkpoint_version

    async def load_checkpoint(
        self,
        workflow_id: str,
    ) -> Optional[Mapping[str, Any]]:
        return self.storage.get(workflow_id)


class TestWorkflowContracts(unittest.TestCase):
    """Verify behavior, invariants, and protocol adherence of core workflow contracts."""

    def test_workflow_status_values_and_terminal_property(self) -> None:
        self.assertEqual(WorkflowStatus.PENDING.value, "pending")
        self.assertEqual(WorkflowStatus.RUNNING.value, "running")
        self.assertEqual(WorkflowStatus.AWAITING_APPROVAL.value, "awaiting_approval")
        self.assertEqual(WorkflowStatus.COMPLETED.value, "completed")
        self.assertEqual(WorkflowStatus.FAILED.value, "failed")
        self.assertEqual(WorkflowStatus.REJECTED.value, "rejected")
        self.assertEqual(WorkflowStatus.ESCALATED.value, "escalated")

        # Non-terminal
        self.assertFalse(WorkflowStatus.PENDING.is_terminal)
        self.assertFalse(WorkflowStatus.RUNNING.is_terminal)
        self.assertFalse(WorkflowStatus.AWAITING_APPROVAL.is_terminal)

        # Terminal
        self.assertTrue(WorkflowStatus.COMPLETED.is_terminal)
        self.assertTrue(WorkflowStatus.FAILED.is_terminal)
        self.assertTrue(WorkflowStatus.REJECTED.is_terminal)
        self.assertTrue(WorkflowStatus.ESCALATED.is_terminal)

    def test_step_execution_status_values(self) -> None:
        self.assertEqual(StepExecutionStatus.SUCCEEDED.value, "succeeded")
        self.assertEqual(StepExecutionStatus.FAILED.value, "failed")
        self.assertEqual(StepExecutionStatus.SUSPENDED.value, "suspended")

    def test_approval_status_values_and_terminal_property(self) -> None:
        self.assertEqual(ApprovalStatus.PENDING.value, "pending")
        self.assertEqual(ApprovalStatus.APPROVED.value, "approved")
        self.assertEqual(ApprovalStatus.CONSUMED.value, "consumed")
        self.assertEqual(ApprovalStatus.REJECTED.value, "rejected")
        self.assertEqual(ApprovalStatus.EXPIRED.value, "expired")

        self.assertFalse(ApprovalStatus.PENDING.is_terminal)
        self.assertFalse(ApprovalStatus.APPROVED.is_terminal)
        self.assertTrue(ApprovalStatus.CONSUMED.is_terminal)
        self.assertTrue(ApprovalStatus.REJECTED.is_terminal)
        self.assertTrue(ApprovalStatus.EXPIRED.is_terminal)

    def test_mutation_status_values_and_terminal_property(self) -> None:
        self.assertEqual(MutationStatus.PLANNED.value, "planned")
        self.assertEqual(MutationStatus.EXECUTION_STARTED.value, "execution_started")
        self.assertEqual(MutationStatus.EXECUTED.value, "executed")
        self.assertEqual(MutationStatus.FAILED.value, "failed")
        self.assertEqual(MutationStatus.AMBIGUOUS.value, "ambiguous")

        self.assertFalse(MutationStatus.PLANNED.is_terminal)
        self.assertFalse(MutationStatus.EXECUTION_STARTED.is_terminal)
        self.assertFalse(MutationStatus.AMBIGUOUS.is_terminal)
        self.assertTrue(MutationStatus.EXECUTED.is_terminal)
        self.assertTrue(MutationStatus.FAILED.is_terminal)

    def test_workflow_definition_ref_valid(self) -> None:
        ref = WorkflowDefinitionRef(definition_id="account_remediation", version="1.0.0")
        self.assertEqual(ref.definition_id, "account_remediation")
        self.assertEqual(ref.version, "1.0.0")

    def test_workflow_definition_ref_rejects_empty_fields(self) -> None:
        with self.assertRaises(ValueError):
            WorkflowDefinitionRef(definition_id="", version="1.0.0")
        with self.assertRaises(ValueError):
            WorkflowDefinitionRef(definition_id="  ", version="1.0.0")
        with self.assertRaises(ValueError):
            WorkflowDefinitionRef(definition_id="account_remediation", version="")
        with self.assertRaises(ValueError):
            WorkflowDefinitionRef(definition_id="account_remediation", version="  ")

    def test_checkpoint_store_port_protocol_conformance(self) -> None:
        store = MockCheckpointStore()
        self.assertIsInstance(store, CheckpointStorePort)


if __name__ == "__main__":
    unittest.main()
