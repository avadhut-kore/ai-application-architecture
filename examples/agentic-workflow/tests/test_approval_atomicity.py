"""Atomic approval decisions, rollback and current host identity regressions."""

import sqlite3
from contextlib import closing
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [
    str(ROOT / "building-blocks/python"),
    str(ROOT / "examples/agentic-workflow"),
    str(ROOT / "examples/agent-execution"),
]
from contracts.agent import AgentActor
from contracts.workflow import ApprovalStatus, WorkflowStatus
from demo import get_components
from tests.test_recovery import ProposalEngine
from workflow.errors import ConcurrentResumeConflictError
from workflow.state import WorkflowActorSnapshot
from workflow.store import InMemoryWorkflowStore


class TestApprovalAtomicity(unittest.IsolatedAsyncioTestCase):
    async def test_rollback_preserves_pending_checkpoint_and_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = str(Path(tmp) / "db")
            engine, customers = get_components(db, agent_engine=ProposalEngine())
            before = await engine.start_workflow(
                "wf", WorkflowActorSnapshot("operator", "senior_agent"), {"customer_id": "cust-001"}
            )
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute(
                    "CREATE TRIGGER reject_decision BEFORE UPDATE ON workflow_approvals BEGIN SELECT RAISE(ABORT, 'injected failure'); END"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                await engine.resume_workflow("wf", "approved", "manager")
            after = engine.store.load_state("wf")
            self.assertEqual(after.to_dict(), before.with_updated_checksum().to_dict())
            approval = engine.store.load_approval(before.pending_approval_id)
            self.assertEqual(approval.status, ApprovalStatus.PENDING)
            self.assertEqual(customers.get_account("cust-001").balance_cents, 15000)
            with closing(sqlite3.connect(db)) as conn, conn:
                conn.execute("DROP TRIGGER reject_decision")
            final = await engine.resume_workflow("wf", "approved", "manager")
            self.assertEqual(final.status, WorkflowStatus.COMPLETED)

    async def test_stale_approval_and_checkpoint_fail_without_partial_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine, _ = get_components(str(Path(tmp) / "db"), agent_engine=ProposalEngine())
            state = await engine.start_workflow(
                "wf", WorkflowActorSnapshot("operator", "senior_agent"), {"customer_id": "cust-001"}
            )
            approval = engine.store.load_approval(state.pending_approval_id)
            updated = replace(
                state,
                status=WorkflowStatus.RUNNING,
                checkpoint_version=state.checkpoint_version + 1,
            )
            decided = replace(approval, status=ApprovalStatus.APPROVED)
            memory = InMemoryWorkflowStore()
            memory.save_state(state)
            memory.save_approval(approval)
            for store in [memory, engine.store]:
                store.commit_approval_transition(state, updated, decided)
                with self.assertRaises(ConcurrentResumeConflictError):
                    store.commit_approval_transition(state, updated, decided)
                self.assertEqual(
                    store.load_approval(approval.approval_id).status, ApprovalStatus.APPROVED
                )
                with self.assertRaises(ValueError):
                    store.commit_approval_transition(
                        state, replace(updated, workflow_id="other"), decided
                    )

    async def test_missing_and_revoked_current_actor_never_mutate(self):
        for actor in [
            None,
            AgentActor("other", "senior_agent"),
            AgentActor("operator", "junior_agent"),
        ]:
            with self.subTest(actor=actor), tempfile.TemporaryDirectory() as tmp:
                engine, customers = get_components(
                    str(Path(tmp) / "db"), agent_engine=ProposalEngine()
                )
                state = await engine.start_workflow(
                    "wf",
                    WorkflowActorSnapshot("operator", "senior_agent"),
                    {"customer_id": "cust-001"},
                )
                step = engine.definition.steps["mutation_execution"].handler.__self__
                step.actor_resolver = lambda _: actor
                state = await engine.resume_workflow("wf", "approved", "manager")
                self.assertEqual(state.status, WorkflowStatus.FAILED)
                self.assertEqual(customers.get_account("cust-001").balance_cents, 15000)
