"""Unit tests for SQLiteWorkflowStore persistence, concurrency, and integrity."""

from __future__ import annotations

import contextlib
import gc
import os
import sqlite3
import sys
import tempfile
import time
import unittest
import warnings
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import ExecutionReceipt
from contracts.workflow import (
    ApprovalStatus,
    MutationStatus,
    WorkflowDefinitionRef,
    WorkflowStatus,
)

from workflow.approval import DurableApprovalRecord
from workflow.audit import WorkflowAuditEvent
from workflow.errors import CorruptedCheckpointError
from workflow.ledger import DurableMutationRecord
from workflow.state import WorkflowActorSnapshot, WorkflowState
from workflow.store import SQLiteWorkflowStore


class TestSQLiteWorkflowStore(unittest.TestCase):
    """Verify SQLite persistence, WAL journaling, optimistic CAS, and checksum enforcement."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_workflow.db")
        self.store = SQLiteWorkflowStore(self.db_path)

        self.actor = WorkflowActorSnapshot(actor_id="test_actor", role="operator")
        self.definition_ref = WorkflowDefinitionRef(definition_id="test_def", version="1.0.0")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_wal_mode_enabled(self) -> None:
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            cursor = conn.execute("PRAGMA journal_mode;")
            mode = cursor.fetchone()[0]
        self.assertEqual(mode.lower(), "wal")

    def test_save_and_load_workflow_state(self) -> None:
        state = WorkflowState(
            workflow_id="wf-100",
            definition=self.definition_ref,
            status=WorkflowStatus.RUNNING,
            current_step="step_1",
            initiator_actor=self.actor,
            domain_context={"key": "value", "count": 10},
        )
        self.store.save_state(state)

        loaded = self.store.load_state("wf-100")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.workflow_id, "wf-100")
        self.assertEqual(loaded.status, WorkflowStatus.RUNNING)
        self.assertEqual(loaded.current_step, "step_1")
        self.assertEqual(loaded.domain_context["count"], 10)
        self.assertEqual(loaded.compute_checksum(), loaded.checksum)

    def test_checksum_corruption_detection(self) -> None:
        state = WorkflowState(
            workflow_id="wf-corrupt",
            definition=self.definition_ref,
            status=WorkflowStatus.RUNNING,
            current_step="step_1",
            initiator_actor=self.actor,
        )
        self.store.save_state(state)

        # Directly tamper with SQLite state_json without updating checksum
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn, conn:
            conn.execute(
                "UPDATE workflow_checkpoints SET state_json = '{\"workflow_id\": \"wf-corrupt\", \"tampered\": true}' "
                "WHERE workflow_id = 'wf-corrupt';"
            )

        with self.assertRaises(Exception):
            self.store.load_state("wf-corrupt")

    def test_compare_and_swap_resume(self) -> None:
        state = WorkflowState(
            workflow_id="wf-cas",
            definition=self.definition_ref,
            status=WorkflowStatus.AWAITING_APPROVAL,
            current_step="human_approval",
            initiator_actor=self.actor,
            checkpoint_version=3,
        )
        self.store.save_state(state)

        # 1. Matching version and status -> True
        success = self.store.compare_and_swap_resume("wf-cas", expected_version=3, new_version=4)
        self.assertTrue(success)

        resumed = self.store.load_state("wf-cas")
        assert resumed is not None
        self.assertEqual(resumed.checkpoint_version, 4)
        self.assertEqual(resumed.status, WorkflowStatus.RUNNING)

        # 2. Competing CAS with old expected_version=3 -> False
        fail_old = self.store.compare_and_swap_resume("wf-cas", expected_version=3, new_version=5)
        self.assertFalse(fail_old)

        # 3. Competing CAS when status is already RUNNING -> False
        fail_status = self.store.compare_and_swap_resume("wf-cas", expected_version=4, new_version=5)
        self.assertFalse(fail_status)

    def test_approval_record_persistence(self) -> None:
        rec = DurableApprovalRecord(
            approval_id="app-1",
            workflow_id="wf-1",
            workflow_definition_id="def-1",
            workflow_definition_version="1.0",
            action_id="act-1",
            capability_name="apply_fee_credit",
            canonical_arguments_json='{"amount": 2000}',
            actor_id="alice",
            actor_role="support",
            status=ApprovalStatus.PENDING,
        )
        self.store.save_approval(rec)

        loaded_by_id = self.store.load_approval("app-1")
        self.assertIsNotNone(loaded_by_id)
        assert loaded_by_id is not None
        self.assertEqual(loaded_by_id.approval_id, "app-1")
        self.assertEqual(loaded_by_id.status, ApprovalStatus.PENDING)

        loaded_by_action = self.store.load_approval_by_action_id("act-1")
        self.assertIsNotNone(loaded_by_action)
        assert loaded_by_action is not None
        self.assertEqual(loaded_by_action.approval_id, "app-1")

    def test_atomic_commit_mutation_and_approval(self) -> None:
        receipt = ExecutionReceipt(
            action_id="act-mut-1",
            capability_name="apply_fee_credit",
            status="succeeded",
            result_summary="Fee credited",
        )
        mutation = DurableMutationRecord(
            action_id="act-mut-1",
            workflow_id="wf-atomic",
            step_name="mutation_step",
            capability_name="apply_fee_credit",
            canonical_args='{"amount": 1500}',
            status=MutationStatus.EXECUTED,
            execution_receipt=receipt,
        )
        approval = DurableApprovalRecord(
            approval_id="app-atomic",
            workflow_id="wf-atomic",
            workflow_definition_id="def-1",
            workflow_definition_version="1.0",
            action_id="act-mut-1",
            capability_name="apply_fee_credit",
            canonical_arguments_json='{"amount": 1500}',
            actor_id="alice",
            actor_role="support",
            status=ApprovalStatus.CONSUMED,
            consumed_at=1000.0,
            execution_receipt_id="act-mut-1",
        )

        self.store.atomic_commit_mutation_and_approval(mutation, approval)

        loaded_mut = self.store.load_mutation("act-mut-1")
        loaded_app = self.store.load_approval("app-atomic")

        self.assertIsNotNone(loaded_mut)
        self.assertIsNotNone(loaded_app)
        assert loaded_mut is not None and loaded_app is not None

        self.assertEqual(loaded_mut.status, MutationStatus.EXECUTED)
        self.assertEqual(loaded_app.status, ApprovalStatus.CONSUMED)
        self.assertEqual(loaded_app.execution_receipt_id, "act-mut-1")

    def test_audit_log_append_and_retrieve(self) -> None:
        evt1 = WorkflowAuditEvent(
            event_id="evt-1",
            workflow_id="wf-audit",
            event_type="workflow_started",
            step_name="step_a",
            details={"foo": "bar"},
        )
        evt2 = WorkflowAuditEvent(
            event_id="evt-2",
            workflow_id="wf-audit",
            event_type="step_completed",
            step_name="step_a",
        )
        self.store.append_audit_event(evt1)
        self.store.append_audit_event(evt2)

        events = self.store.load_audit_events("wf-audit")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "workflow_started")
        self.assertEqual(events[1].event_type, "step_completed")

    def test_connections_close_deterministically_and_tempdir_cleans_without_gc(self) -> None:
        """All SQLiteWorkflowStore methods close connections deterministically without needing gc.collect()."""
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                tmp_dir = tempfile.TemporaryDirectory()
                try:
                    db_file = os.path.join(tmp_dir.name, "lifecycle.db")
                    before_conns = sum(1 for obj in gc.get_objects() if isinstance(obj, sqlite3.Connection))

                    store = SQLiteWorkflowStore(db_file)
                    state = WorkflowState(
                        workflow_id="wf-lifecycle",
                        definition=self.definition_ref,
                        status=WorkflowStatus.AWAITING_APPROVAL,
                        current_step="human_approval",
                        initiator_actor=self.actor,
                        checkpoint_version=1,
                    )
                    store.save_state(state)
                    self.assertIsNotNone(store.load_state("wf-lifecycle"))
                    self.assertTrue(store.compare_and_swap_resume("wf-lifecycle", 1, 2))

                    approval = DurableApprovalRecord(
                        approval_id="app-lc",
                        workflow_id="wf-lifecycle",
                        workflow_definition_id="test_def",
                        workflow_definition_version="1.0.0",
                        action_id="act-lc",
                        capability_name="apply_fee_credit",
                        canonical_arguments_json='{"amount": 100}',
                        actor_id="test_actor",
                        actor_role="operator",
                        status=ApprovalStatus.PENDING,
                    )
                    store.save_approval(approval)
                    self.assertIsNotNone(store.load_approval("app-lc"))
                    self.assertIsNotNone(store.load_approval_by_action_id("act-lc"))

                    mutation = DurableMutationRecord(
                        action_id="act-lc",
                        workflow_id="wf-lifecycle",
                        step_name="mutation_step",
                        capability_name="apply_fee_credit",
                        canonical_args='{"amount": 100}',
                        status=MutationStatus.EXECUTED,
                    )
                    store.save_mutation(mutation)
                    self.assertIsNotNone(store.load_mutation("act-lc"))
                    consumed = DurableApprovalRecord(
                        approval_id="app-lc",
                        workflow_id="wf-lifecycle",
                        workflow_definition_id="test_def",
                        workflow_definition_version="1.0.0",
                        action_id="act-lc",
                        capability_name="apply_fee_credit",
                        canonical_arguments_json='{"amount": 100}',
                        actor_id="test_actor",
                        actor_role="operator",
                        status=ApprovalStatus.CONSUMED,
                        consumed_at=time.time(),
                    )
                    store.atomic_commit_mutation_and_approval(mutation, consumed)
                    store.append_audit_event(
                        WorkflowAuditEvent(
                            event_id="evt-lc",
                            workflow_id="wf-lifecycle",
                            event_type="lifecycle_checked",
                        )
                    )
                    self.assertEqual(len(store.load_audit_events("wf-lifecycle")), 1)

                    after_conns = sum(1 for obj in gc.get_objects() if isinstance(obj, sqlite3.Connection))
                    self.assertEqual(after_conns, before_conns)
                finally:
                    # Must succeed immediately with cyclic GC disabled
                    tmp_dir.cleanup()

                db_warnings = [w for w in caught if "unclosed database" in str(w.message)]
                self.assertEqual(db_warnings, [])
        finally:
            if gc_was_enabled:
                gc.enable()

    def test_connection_rolls_back_and_closes_on_exception(self) -> None:
        """Exceptions inside _connection() roll back transactions and still close the connection."""
        captured_conn: sqlite3.Connection | None = None
        with self.assertRaises(RuntimeError), self.store._connection() as conn:
            captured_conn = conn
            conn.execute(
                """
                INSERT INTO workflow_audit_log (
                    event_id, workflow_id, event_type, step_name, details_json, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                ("evt-rollback", "wf-rollback", "should_rollback", None, "{}", time.time()),
            )
            raise RuntimeError("Simulated mid-transaction failure")

        # Transaction was rolled back
        self.assertEqual(self.store.load_audit_events("wf-rollback"), [])
        # Connection was deterministically closed
        assert captured_conn is not None
        with self.assertRaises(sqlite3.ProgrammingError):
            captured_conn.execute("SELECT 1;")

    def test_atomic_commit_rolls_back_and_closes_on_sql_error(self) -> None:
        """Failure on second write in atomic_commit_mutation_and_approval rolls back first write and closes."""
        gc_was_enabled = gc.isenabled()
        gc.disable()
        try:
            tmp_dir = tempfile.TemporaryDirectory()
            try:
                store = SQLiteWorkflowStore(os.path.join(tmp_dir.name, "atomic_rollback.db"))
                mutation = DurableMutationRecord(
                    action_id="act-rb-1",
                    workflow_id="wf-rb-1",
                    step_name="mutation_step",
                    capability_name="apply_fee_credit",
                    canonical_args='{"amount": 500}',
                    status=MutationStatus.EXECUTED,
                )
                # actor_id=None violates NOT NULL on workflow_approvals after mutation insert succeeds
                invalid_approval = DurableApprovalRecord(
                    approval_id="app-rb-1",
                    workflow_id="wf-rb-1",
                    workflow_definition_id="def-1",
                    workflow_definition_version="1.0",
                    action_id="act-rb-1",
                    capability_name="apply_fee_credit",
                    canonical_arguments_json='{"amount": 500}',
                    actor_id=None,  # type: ignore[arg-type]
                    actor_role="support",
                    status=ApprovalStatus.CONSUMED,
                )
                with self.assertRaises(sqlite3.IntegrityError):
                    store.atomic_commit_mutation_and_approval(mutation, invalid_approval)

                # First insert must have been rolled back atomically
                self.assertIsNone(store.load_mutation("act-rb-1"))
            finally:
                tmp_dir.cleanup()
        finally:
            if gc_was_enabled:
                gc.enable()


if __name__ == "__main__":
    unittest.main()
