"""Hermetic unit and integration tests for Local Saga backward compensation."""

import sys
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
from contracts.agent import (
    AgentActor,
    CapabilityMetadata,
    CapabilityPort,
    SideEffectLevel,
)
from contracts.workflow import StepExecutionStatus, WorkflowStatus
from workflow.engine import WorkflowEngine
from workflow.errors import SagaCompensationError
from workflow.remediation_workflow import build_customer_remediation_workflow
from workflow.saga import SagaCompensationCoordinator
from workflow.state import WorkflowActorSnapshot
from workflow.store import InMemoryWorkflowStore


class FailingCapability(CapabilityPort):
    def __init__(self, name: str = "failing_credit") -> None:
        self._metadata = CapabilityMetadata(
            name=name,
            description="Capability designed to simulate permanent downstream failure.",
            input_schema={"type": "object"},
            side_effect_level=SideEffectLevel.STATE_MUTATING,
            requires_approval=True,
        )

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(self, arguments: Mapping[str, Any], context: Optional[Any] = None) -> Any:
        raise RuntimeError("Core banking gateway timeout: transaction aborted.")


class TestLocalSagaCompensation(unittest.IsolatedAsyncioTestCase):
    """Verify local linear saga compensation and manual intervention signaling."""

    def setUp(self) -> None:
        self.customer_store = InMemoryCustomerStore()
        self.auth_policy = CustomerSupportAuthorizationPolicy(store=self.customer_store)
        self.store = InMemoryWorkflowStore()

    async def test_coordinator_lifo_backward_compensation(self) -> None:
        """SagaCompensationCoordinator executes registered compensations in reverse order."""
        coordinator = SagaCompensationCoordinator(workflow_id="wf-saga-001")
        note_cap = UpdateCustomerNoteCapability(self.customer_store)

        coordinator.register(
            original_action_id="act-note-1",
            step_name="mutate_note",
            capability=note_cap,
            arguments={"customer_id": "cust-001", "note": "Compensate: Rollback concession note."},
            reason="Downstream credit failed",
        )

        records = await coordinator.compensate_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].status, "succeeded")
        self.assertIn("Compensate: Rollback", self.customer_store.get_account("cust-001").notes[-1])

    async def test_coordinator_handles_compensation_failure(self) -> None:
        """When compensation action itself fails, coordinator raises SagaCompensationError."""
        coordinator = SagaCompensationCoordinator(workflow_id="wf-saga-002")
        failing_cap = FailingCapability()

        coordinator.register(
            original_action_id="act-fail-1",
            step_name="failing_step",
            capability=failing_cap,
            arguments={},
            reason="Failure test",
        )

        with self.assertRaises(SagaCompensationError) as ctx:
            await coordinator.compensate_all()

        self.assertIn("Manual intervention required", str(ctx.exception))
        self.assertEqual(len(coordinator.executed_compensations), 1)
        self.assertEqual(coordinator.executed_compensations[0].status, "failed")

    async def test_workflow_compensate_mutation_on_downstream_failure(self) -> None:
        """Workflow transitions to compensate_mutation when credit fails after note was logged."""
        failing_credit = FailingCapability("apply_fee_credit")
        note_cap = UpdateCustomerNoteCapability(self.customer_store)
        read_only_caps = [
            GetCustomerCapability(self.customer_store),
            GetAccountStatusCapability(self.customer_store),
            SearchPolicyCapability(),
        ]
        executor = ToolExecutor()

        class StubAgentEngine:
            async def run(self, task: str, actor: AgentActor) -> Any:
                class Res:
                    final_answer = '{"proposal_type": "fee_credit", "summary": "Fee refund", "suggested_arguments": {"amount_cents": 1000, "reason": "test"}}'
                    status = "COMPLETED"
                    execution_receipts = []
                    run_id = "stub-1"
                return Res()

        workflow_def = build_customer_remediation_workflow(
            customer_store=self.customer_store,
            agent_engine=StubAgentEngine(),
            read_only_registry=CapabilityRegistry(read_only_caps),
            credit_capability=failing_credit,
            note_capability=note_cap,
            tool_executor=executor,
            workflow_store=self.store,
            auth_policy=self.auth_policy,
        )

        engine = WorkflowEngine(definition=workflow_def, store=self.store)
        wf_id = "wf-saga-flow-001"
        actor = WorkflowActorSnapshot("operator_bob", "senior_agent")

        # Start workflow with pre-existing note indicator in domain context
        state = await engine.start_workflow(
            workflow_id=wf_id,
            actor=actor,
            domain_context={"customer_id": "cust-001", "has_prior_note": True},
        )
        self.assertEqual(state.status, WorkflowStatus.AWAITING_APPROVAL)

        # Resume with approval; credit execution will fail, triggering compensation
        final_state = await engine.resume_workflow(
            workflow_id=wf_id,
            decision="approved",
            approver_id="manager_jane",
        )

        # Reached terminal_failed after compensate_mutation
        self.assertEqual(final_state.status, WorkflowStatus.FAILED)
        self.assertTrue(final_state.domain_context.get("compensation_applied"))
        self.assertIn("COMPENSATION", self.customer_store.get_account("cust-001").notes[-1])

        # Assert compensation was recorded in the durable mutation ledger
        comp_mutations = [
            m for m in self.store.mutations.values()
            if m.step_name == "compensate_mutation"
        ]
        self.assertEqual(len(comp_mutations), 1)
        self.assertEqual(comp_mutations[0].status, "executed")

    async def test_workflow_compensation_failure_signals_manual_intervention(self) -> None:
        """When compensation capability itself fails, ledger records FAILED and manual intervention is flagged."""
        failing_credit = FailingCapability("apply_fee_credit")
        failing_note = FailingCapability("update_customer_note")
        read_only_caps = [
            GetCustomerCapability(self.customer_store),
            GetAccountStatusCapability(self.customer_store),
            SearchPolicyCapability(),
        ]
        executor = ToolExecutor()

        class StubAgentEngine:
            async def run(self, task: str, actor: AgentActor) -> Any:
                class Res:
                    final_answer = '{"proposal_type": "fee_credit", "summary": "Fee refund", "suggested_arguments": {"amount_cents": 1000, "reason": "test"}}'
                    status = "COMPLETED"
                    execution_receipts = []
                    run_id = "stub-2"
                return Res()

        workflow_def = build_customer_remediation_workflow(
            customer_store=self.customer_store,
            agent_engine=StubAgentEngine(),
            read_only_registry=CapabilityRegistry(read_only_caps),
            credit_capability=failing_credit,
            note_capability=failing_note,
            tool_executor=executor,
            workflow_store=self.store,
            auth_policy=self.auth_policy,
        )

        engine = WorkflowEngine(definition=workflow_def, store=self.store)
        wf_id = "wf-saga-fail-002"
        actor = WorkflowActorSnapshot("operator_bob", "senior_agent")

        await engine.start_workflow(
            workflow_id=wf_id,
            actor=actor,
            domain_context={"customer_id": "cust-001", "has_prior_note": True},
        )

        final_state = await engine.resume_workflow(
            workflow_id=wf_id,
            decision="approved",
            approver_id="manager_jane",
        )

        self.assertEqual(final_state.status, WorkflowStatus.FAILED)
        self.assertFalse(final_state.domain_context.get("compensation_applied", False))
        self.assertTrue(final_state.domain_context.get("manual_intervention_required"))

        comp_mutations = [
            m for m in self.store.mutations.values()
            if m.step_name == "compensate_mutation"
        ]
        self.assertEqual(len(comp_mutations), 1)
        self.assertEqual(comp_mutations[0].status, "failed")


if __name__ == "__main__":
    unittest.main()
