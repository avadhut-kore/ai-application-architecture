"""Regression evidence for real process death, durable outcomes and approval policy."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[3]
for path in (
    ROOT / "building-blocks/python",
    ROOT / "examples/agent-execution",
    ROOT / "examples/agentic-workflow",
):
    sys.path.insert(0, str(path))

from agent.persistence import SQLiteCustomerStore
from contracts.workflow import ApprovalStatus, WorkflowStatus
from demo import get_components
from workflow.state import WorkflowActorSnapshot


class ProposalEngine:
    def __init__(self, kind="fee_credit"):
        self.kind = kind
        self.goals = []

    async def run(self, goal, actor):
        self.goals.append(goal)
        arguments = (
            {"amount_cents": 2500, "reason": "Verified fee"}
            if self.kind == "fee_credit"
            else {"note": "Verified note"}
        )
        return SimpleNamespace(
            status="COMPLETED",
            execution_receipts=[],
            final_answer=json.dumps(
                {
                    "proposal_type": self.kind,
                    "summary": "Verified proposal",
                    "suggested_arguments": arguments,
                }
            ),
        )


class TestDurableRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_model_cannot_change_the_workflow_customer_scope(self):
        class CrossCustomerProposal:
            async def run(self, goal, actor):
                return SimpleNamespace(
                    status="COMPLETED",
                    execution_receipts=[],
                    final_answer=json.dumps(
                        {
                            "proposal_type": "fee_credit",
                            "summary": "Wrong customer",
                            "suggested_arguments": {
                                "customer_id": "cust-004",
                                "amount_cents": 1000,
                                "reason": "Mismatch",
                            },
                        }
                    ),
                )

        engine, customers = get_components(self.db, agent_engine=CrossCustomerProposal())
        state = await engine.start_workflow("scope", self.actor, {"customer_id": "cust-001"})
        self.assertEqual(state.status, WorkflowStatus.FAILED)
        self.assertIsNone(state.pending_approval_id)
        self.assertEqual(customers.get_account("cust-004").credits_applied_cents, 0)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "workflow.db")
        self.actor = WorkflowActorSnapshot("operator", "senior_agent")

    def tearDown(self):
        self.temp.cleanup()

    async def test_note_requires_approval_and_inquiry_is_delivered(self):
        proposal = ProposalEngine("customer_note")
        engine, customers = get_components(self.db, agent_engine=proposal)
        state = await engine.start_workflow(
            "note", self.actor, {"customer_id": "cust-001", "inquiry": "UNIQUE QUESTION"}
        )
        self.assertEqual(state.status, WorkflowStatus.AWAITING_APPROVAL)
        self.assertEqual(len(customers.get_account("cust-001").notes), 1)
        self.assertIn("UNIQUE QUESTION", proposal.goals[0])
        state = await engine.resume_workflow("note", "approved", "manager")
        self.assertEqual(state.status, WorkflowStatus.COMPLETED)
        self.assertEqual(len(SQLiteCustomerStore(self.db).get_account("cust-001").notes), 2)
        self.assertEqual(
            engine.store.load_approval(state.pending_approval_id).status, ApprovalStatus.CONSUMED
        )

    async def test_claim_without_decision_returns_to_approval(self):
        engine, customers = get_components(self.db, agent_engine=ProposalEngine())
        state = await engine.start_workflow("credit", self.actor, {"customer_id": "cust-001"})
        engine.store.compare_and_swap_resume(
            "credit", state.checkpoint_version, state.checkpoint_version + 1
        )
        fresh, _ = get_components(self.db, agent_engine=ProposalEngine())
        recovered = await fresh.recover_workflow("credit")
        self.assertEqual(recovered.status, WorkflowStatus.AWAITING_APPROVAL)
        self.assertEqual(customers.get_account("cust-001").balance_cents, 15000)

    async def test_invalid_approver_or_decision_does_not_claim(self):
        engine, _ = get_components(self.db, agent_engine=ProposalEngine())
        await engine.start_workflow("credit", self.actor, {"customer_id": "cust-001"})
        for decision, role in [("typo", "manager"), ("approved", "junior_agent")]:
            with self.assertRaises(ValueError):
                await engine.resume_workflow("credit", decision, "actor", approver_role=role)
        self.assertEqual(engine.store.load_state("credit").status, WorkflowStatus.AWAITING_APPROVAL)

    def test_real_os_death_after_claim_effect_and_receipt(self):
        fixture = Path(__file__).parent / "cli_fixture.py"
        for boundary in ("claim", "effect", "receipt"):
            db = str(Path(self.temp.name) / f"{boundary}.db")
            base = [sys.executable, str(fixture), "--db", db]
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            started = subprocess.run(
                base + ["start", "--workflow-id", "wf"], capture_output=True, env=env, timeout=30
            )
            self.assertEqual(started.returncode, 0, started.stderr)
            crash_env = dict(env, WORKFLOW_TEST_CRASH=boundary)
            crashed = subprocess.run(
                base + ["approve", "--workflow-id", "wf"],
                capture_output=True,
                env=crash_env,
                timeout=30,
            )
            self.assertEqual(crashed.returncode, 71, crashed.stderr)
            recovered = subprocess.run(
                base + ["recover", "--workflow-id", "wf"], capture_output=True, env=env, timeout=30
            )
            self.assertEqual(recovered.returncode, 0, recovered.stderr)
            if boundary == "claim":
                approved = subprocess.run(
                    base + ["approve", "--workflow-id", "wf"],
                    capture_output=True,
                    env=env,
                    timeout=30,
                )
                self.assertEqual(approved.returncode, 0, approved.stderr)
            account = SQLiteCustomerStore(db).get_account("cust-001")
            self.assertEqual(account.balance_cents, 17500)
            self.assertEqual(
                len([x for x in account.activity_log if x.startswith("Credit applied")]), 1
            )

    def test_durable_action_identity_rejects_collisions(self):
        store = SQLiteCustomerStore(self.db)
        store.apply_credit("cust-001", 100, "Fee", "id")
        store.apply_credit("cust-001", 100, "Fee", "id")
        self.assertEqual(store.get_account("cust-001").balance_cents, 15100)
        with self.assertRaises(ValueError):
            store.apply_credit("cust-002", 100, "Fee", "id")
        store.apply_credit("cust-001", 100, "Fee", "different-id")
        self.assertEqual(store.get_account("cust-001").balance_cents, 15200)
        self.assertEqual(store.action_status("missing"), "not_executed")
        store.set_customer_status("cust-001", "frozen")
        self.assertEqual(SQLiteCustomerStore(self.db).get_customer("cust-001").status, "frozen")


if __name__ == "__main__":
    unittest.main()
