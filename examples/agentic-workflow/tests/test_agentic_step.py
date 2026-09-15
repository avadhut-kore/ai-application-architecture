"""Hermetic unit tests for AgenticInvestigationStep and read-only registry safety."""

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

from agent.registry import CapabilityRegistry
from contracts.agent import (
    AgentActor,
    CapabilityMetadata,
    CapabilityPort,
    SideEffectLevel,
)
from contracts.workflow import StepExecutionStatus, WorkflowDefinitionRef, WorkflowStatus
from workflow.state import (
    RemediationProposal,
    RemediationType,
    WorkflowActorSnapshot,
    WorkflowState,
)
from workflow.steps.agentic import AgenticInvestigationStep


class DummyReadOnlyCapability(CapabilityPort):
    def __init__(self, name: str = "get_customer") -> None:
        self._metadata = CapabilityMetadata(
            name=name,
            description="Read-only query",
            input_schema={"type": "object"},
            side_effect_level=SideEffectLevel.READ_ONLY,
        )

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(self, arguments: Mapping[str, Any], context: Optional[Any] = None) -> Any:
        return {"customer_id": "cust-1", "name": "Alice"}


class DummyMutatingCapability(CapabilityPort):
    def __init__(self, name: str = "apply_fee_credit") -> None:
        self._metadata = CapabilityMetadata(
            name=name,
            description="Mutating credit action",
            input_schema={"type": "object"},
            side_effect_level=SideEffectLevel.STATE_MUTATING,
            requires_approval=True,
        )

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(self, arguments: Mapping[str, Any], context: Optional[Any] = None) -> Any:
        return {"credited": True}


class MockAgentEngine:
    def __init__(self, answer_text: str) -> None:
        self.answer_text = answer_text

    async def run(self, task: str, actor: AgentActor) -> Any:
        class MockResult:
            def __init__(self, answer: str) -> None:
                self.final_answer = answer
                self.total_steps = 1
                self.execution_receipts = []
                self.status = "COMPLETED"
                self.run_id = "run-mock-123"
                self.episodes = ()
        return MockResult(self.answer_text)


class TestAgenticInvestigationStep(unittest.IsolatedAsyncioTestCase):
    """Verify read-only invariant and structured proposal parsing."""

    def test_enforces_read_only_registry_invariant(self) -> None:
        """Investigation step MUST reject any registry containing STATE_MUTATING tools."""
        mutating_registry = CapabilityRegistry([DummyReadOnlyCapability(), DummyMutatingCapability()])
        with self.assertRaises(ValueError) as ctx:
            AgenticInvestigationStep(
                agent_engine=MockAgentEngine(""),
                read_only_registry=mutating_registry,
            )
        self.assertIn("Security Invariant Violation", str(ctx.exception))
        self.assertIn("Mutating capability 'apply_fee_credit' detected", str(ctx.exception))

    async def test_successful_proposal_parsing_fee_credit(self) -> None:
        """Parses structured JSON proposal block into typed RemediationProposal."""
        read_only_registry = CapabilityRegistry([DummyReadOnlyCapability()])
        model_output = (
            "Based on the transaction history, the customer was double-charged due to system timeout.\n"
            "```json\n"
            "{\n"
            '  "proposal_type": "fee_credit",\n'
            '  "summary": "Refund accidental overdraft fee",\n'
            '  "suggested_arguments": {"amount": 3500},\n'
            '  "confidence": 0.95,\n'
            '  "requires_human_approval": true\n'
            "}\n"
            "```\n"
            "Please review."
        )

        step = AgenticInvestigationStep(
            agent_engine=MockAgentEngine(model_output),
            read_only_registry=read_only_registry,
        )

        state = WorkflowState(
            workflow_id="wf-inv-001",
            definition=WorkflowDefinitionRef("customer_account_remediation", "1.0.0"),
            status=WorkflowStatus.RUNNING,
            current_step="agentic_investigation",
            initiator_actor=WorkflowActorSnapshot("user-1", "operator"),
            history=(),
            domain_context={"customer_id": "cust-123"},
        )

        outcome = await step.execute(state)

        self.assertEqual(outcome.status, StepExecutionStatus.SUCCEEDED)
        self.assertEqual(outcome.outcome_type, RemediationType.FEE_CREDIT.value)
        proposal_dict = outcome.context_updates.get("remediation_proposal")
        self.assertIsNotNone(proposal_dict)
        assert proposal_dict is not None
        self.assertEqual(proposal_dict["proposal_type"], "fee_credit")
        self.assertEqual(proposal_dict["suggested_arguments"]["amount"], 3500)

    async def test_unstructured_output_defaults_to_informational(self) -> None:
        """Unparseable or non-JSON model answer safely defaults to INFORMATIONAL proposal."""
        read_only_registry = CapabilityRegistry([DummyReadOnlyCapability()])
        model_output = "The customer account is in good standing. No financial discrepancy found."

        step = AgenticInvestigationStep(
            agent_engine=MockAgentEngine(model_output),
            read_only_registry=read_only_registry,
        )

        state = WorkflowState(
            workflow_id="wf-inv-002",
            definition=WorkflowDefinitionRef("customer_account_remediation", "1.0.0"),
            status=WorkflowStatus.RUNNING,
            current_step="agentic_investigation",
            initiator_actor=WorkflowActorSnapshot("user-1", "operator"),
            history=(),
            domain_context={"customer_id": "cust-123"},
        )

        outcome = await step.execute(state)

        self.assertEqual(outcome.status, StepExecutionStatus.SUCCEEDED)
        self.assertEqual(outcome.outcome_type, RemediationType.INFORMATIONAL.value)
        proposal_dict = outcome.context_updates.get("remediation_proposal")
        self.assertIsNotNone(proposal_dict)
        assert proposal_dict is not None
        self.assertEqual(proposal_dict["proposal_type"], "informational")


if __name__ == "__main__":
    unittest.main()
