"""Hermetic tests for durable Human-in-the-Loop (HITL) resumption across process restarts."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.capabilities import (
    ApplyFeeCreditCapability,
    GetAccountStatusCapability,
    GetCustomerCapability,
    SearchPolicyCapability,
    UpdateCustomerNoteCapability,
)
from agent.domain import InMemoryCustomerStore
from agent.executor import ToolExecutor
from agent.policy import CustomerSupportAuthorizationPolicy
from agent.registry import CapabilityRegistry
from contracts.agent import AgentActor, ApprovalDecision, ApprovalPort, CapabilityMetadata
from contracts.workflow import ApprovalStatus, MutationStatus, WorkflowStatus
from workflow.engine import WorkflowEngine
from workflow.remediation_workflow import build_customer_remediation_workflow
from workflow.state import WorkflowActorSnapshot
from workflow.store import SQLiteWorkflowStore


class StubAgentEngine:
    """Deterministic agent stub simulating bounded Phase 6 agent proposal."""

    def __init__(self, proposal_type: str = "fee_credit", amount_cents: int = 2500) -> None:
        self.proposal_type = proposal_type
        self.amount_cents = amount_cents

    async def run(self, task: str, actor: AgentActor) -> Any:
        answer = (
            f"Diagnosed customer inquiry.\n"
            f'{{"proposal_type": "{self.proposal_type}", "summary": "Outage fee adjustment", '
            f'"suggested_arguments": {{"amount_cents": {self.amount_cents}, "reason": "Outage fee adjustment"}}, '
            f'"requires_human_approval": true}}'
        )

        class StubResult:
            def __init__(self, text: str) -> None:
                self.final_answer = text
                self.status = "COMPLETED"
                self.execution_receipts = []
                self.run_id = "agent-run-stub-1"
                self.step_count = 2

        return StubResult(answer)


class StubApprovalHandler(ApprovalPort):
    async def request_approval(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> ApprovalDecision:
        return ApprovalDecision(approved=True, approver="test_approver")


class TestHitlProcessRestart(unittest.IsolatedAsyncioTestCase):
    """Verify end-to-end workflow pause, process termination, reload from SQLite, and resume."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "workflow_restart_test.db")
        self.customer_store = InMemoryCustomerStore()
        self.auth_policy = CustomerSupportAuthorizationPolicy(store=self.customer_store)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _create_engine(self, db_path: str, proposal_type: str = "fee_credit", amount_cents: int = 2500) -> WorkflowEngine:
        sqlite_store = SQLiteWorkflowStore(db_path)
        read_only_caps = [
            GetCustomerCapability(self.customer_store),
            GetAccountStatusCapability(self.customer_store),
            SearchPolicyCapability(),
        ]
        read_only_registry = CapabilityRegistry(read_only_caps)
        credit_cap = ApplyFeeCreditCapability(self.customer_store)
        note_cap = UpdateCustomerNoteCapability(self.customer_store)

        executor = ToolExecutor()

        agent_stub = StubAgentEngine(proposal_type=proposal_type, amount_cents=amount_cents)

        workflow_def = build_customer_remediation_workflow(
            customer_store=self.customer_store,
            agent_engine=agent_stub,
            read_only_registry=read_only_registry,
            credit_capability=credit_cap,
            note_capability=note_cap,
            tool_executor=executor,
            workflow_store=sqlite_store,
            auth_policy=self.auth_policy,
        )

        return WorkflowEngine(definition=workflow_def, store=sqlite_store)

    async def test_hitl_approval_and_execution_across_independent_instances(self) -> None:
        """Process A runs until suspension; Process B reloads and executes approved mutation."""
        wf_id = "wf-restart-001"
        actor = WorkflowActorSnapshot(actor_id="operator_bob", role="senior_agent")

        # --- PROCESS A: Execution begins, diagnoses, suspends at HumanApprovalStep ---
        engine_a = self._create_engine(self.db_path, proposal_type="fee_credit", amount_cents=2500)
        state_a = await engine_a.start_workflow(
            workflow_id=wf_id,
            actor=actor,
            domain_context={"customer_id": "cust-001", "description": "Overdraft dispute"},
        )

        self.assertEqual(state_a.status, WorkflowStatus.AWAITING_APPROVAL)
        self.assertEqual(state_a.current_step, "human_approval")
        self.assertEqual(state_a.checkpoint_version, 5)  # initial=1, intake=2, context=3, agentic=4, human=5

        # Verify physical customer balance is UNTOUCHED
        acc_after_a = self.customer_store.get_account("cust-001")
        assert acc_after_a is not None
        self.assertEqual(acc_after_a.balance_cents, 15000)

        # Discard Process A engine completely
        del engine_a

        # --- PROCESS B: Independent process starts, reloads from SQLite, approves, resumes ---
        engine_b = self._create_engine(self.db_path)
        persisted_state = engine_b.store.load_state(wf_id)
        self.assertIsNotNone(persisted_state)
        assert persisted_state is not None
        self.assertEqual(persisted_state.status, WorkflowStatus.AWAITING_APPROVAL)

        # Resume with manager approval
        final_state = await engine_b.resume_workflow(
            workflow_id=wf_id,
            decision="approved",
            approver_id="manager_sarah",
            approver_role="manager",
            reason="Approved refund of dispute",
        )

        self.assertEqual(final_state.status, WorkflowStatus.COMPLETED)
        self.assertEqual(final_state.current_step, "terminal_completed")

        # Verify mutation occurred exactly once (+2500 cents = 17500 cents)
        acc_after_b = self.customer_store.get_account("cust-001")
        assert acc_after_b is not None
        self.assertEqual(acc_after_b.balance_cents, 17500)

        # Verify durable mutation ledger recorded EXECUTED
        action_id = final_state.domain_context.get("stable_action_id")
        self.assertIsNotNone(action_id)
        mutation_rec = engine_b.store.load_mutation(action_id)
        self.assertIsNotNone(mutation_rec)
        assert mutation_rec is not None
        self.assertEqual(mutation_rec.status, MutationStatus.EXECUTED)
        self.assertIsNotNone(mutation_rec.execution_receipt)

        # Verify approval record is CONSUMED
        approval_id = final_state.domain_context.get("pending_approval_id")
        approval_rec = engine_b.store.load_approval(approval_id)
        self.assertIsNotNone(approval_rec)
        assert approval_rec is not None
        self.assertEqual(approval_rec.status, ApprovalStatus.CONSUMED)

    async def test_hitl_rejection_across_restart_prevents_all_mutations(self) -> None:
        """Process A suspends; Process B rejects; zero physical mutations occur."""
        wf_id = "wf-restart-002"
        actor = WorkflowActorSnapshot(actor_id="operator_bob", role="senior_agent")

        engine_a = self._create_engine(self.db_path, proposal_type="fee_credit", amount_cents=2500)
        state_a = await engine_a.start_workflow(
            workflow_id=wf_id,
            actor=actor,
            domain_context={"customer_id": "cust-001", "description": "Overdraft dispute"},
        )
        self.assertEqual(state_a.status, WorkflowStatus.AWAITING_APPROVAL)
        del engine_a

        # Independent Process B rejects
        engine_b = self._create_engine(self.db_path)
        final_state = await engine_b.resume_workflow(
            workflow_id=wf_id,
            decision="rejected",
            approver_id="manager_sarah",
            reason="Exceeds customer goodwill quota",
        )

        self.assertEqual(final_state.status, WorkflowStatus.REJECTED)
        self.assertEqual(final_state.current_step, "terminal_rejected")

        # Verify customer balance UNCHANGED
        acc = self.customer_store.get_account("cust-001")
        assert acc is not None
        self.assertEqual(acc.balance_cents, 15000)

        # Verify zero mutations in ledger
        action_id = final_state.domain_context.get("stable_action_id")
        mutation_rec = engine_b.store.load_mutation(action_id)
        self.assertIsNone(mutation_rec)


if __name__ == "__main__":
    unittest.main()
