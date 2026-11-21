"""Negative controls for durable mutation identities and uncertain outcomes."""

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import AsyncMock

ROOT = Path(__file__).resolve().parents[3]
for path in (
    ROOT / "building-blocks/python",
    ROOT / "examples/agent-execution",
    ROOT / "examples/agentic-workflow",
):
    sys.path.insert(0, str(path))
from contracts.workflow import MutationStatus, StepExecutionStatus
from demo import get_components
from tests.test_recovery import ProposalEngine
from workflow.approval import canonicalize_arguments
from workflow.ledger import DurableMutationRecord, generate_stable_action_id
from workflow.state import WorkflowActorSnapshot


class TestMutationBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_prior_failure_ambiguity_and_identity_conflict_never_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, _ = get_components(str(Path(directory) / "db"), agent_engine=ProposalEngine())
            state = await engine.start_workflow(
                "credit",
                WorkflowActorSnapshot("operator", "senior_agent"),
                {"customer_id": "cust-001"},
            )
            handler = engine.definition.steps["mutation_execution"].handler
            action_id = state.domain_context["stable_action_id"]
            args = canonicalize_arguments(state.domain_context["target_arguments"])
            for status, outcome in (
                (MutationStatus.FAILED, "mutation_failed"),
                (MutationStatus.AMBIGUOUS, "ambiguous_execution"),
            ):
                record = DurableMutationRecord(
                    action_id,
                    state.workflow_id,
                    "mutation_execution",
                    "apply_fee_credit",
                    args,
                    status,
                )
                engine.store.save_mutation(record)
                result = await handler(state)
                self.assertEqual(result.outcome_type, outcome)
            engine.store.save_mutation(replace(record, canonical_args="{}"))
            self.assertEqual((await handler(state)).outcome_type, "action_identity_mismatch")

    async def test_missing_approval_and_reconciler_failure_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, _ = get_components(str(Path(directory) / "db"), agent_engine=ProposalEngine())
            state = await engine.start_workflow(
                "credit",
                WorkflowActorSnapshot("operator", "senior_agent"),
                {"customer_id": "cust-001"},
            )
            step = engine.definition.steps["mutation_execution"].handler.__self__
            state = replace(
                state,
                domain_context={
                    "customer_id": "cust-001",
                    "remediation_proposal": {
                        "suggested_arguments": {"amount_cents": 100, "reason": "Other"}
                    },
                },
            )
            self.assertEqual(
                (await step.execute(state)).outcome_type, "approval_verification_failed"
            )
            args = {"amount_cents": 100, "reason": "Other", "customer_id": "cust-001"}
            canonical = canonicalize_arguments(args)
            action_id = generate_stable_action_id(
                state.workflow_id, "mutation_execution", "apply_fee_credit", canonical
            )
            engine.store.save_mutation(
                DurableMutationRecord(
                    action_id,
                    state.workflow_id,
                    "mutation_execution",
                    "apply_fee_credit",
                    canonical,
                    MutationStatus.EXECUTION_STARTED,
                )
            )
            step.reconciler = AsyncMock(side_effect=RuntimeError("unavailable"))
            result = await step.execute(state)
            self.assertEqual(result.status, StepExecutionStatus.FAILED)
            self.assertEqual(engine.store.load_mutation(action_id).status, MutationStatus.AMBIGUOUS)

    async def test_compensation_prior_failure_ambiguity_and_missing_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            engine, _ = get_components(str(Path(directory) / "db"), agent_engine=ProposalEngine())
            state = await engine.start_workflow(
                "credit",
                WorkflowActorSnapshot("operator", "senior_agent"),
                {"customer_id": "cust-001"},
            )
            handler = engine.definition.steps["compensate_mutation"].handler
            args = {
                "customer_id": "cust-001",
                "note": "COMPENSATION: Fee credit disbursement failed for workflow credit. Concession note voided.",
            }
            canonical = canonicalize_arguments(args)
            action_id = generate_stable_action_id(
                "credit", "compensate_mutation", "update_customer_note", canonical
            )
            for status in (
                MutationStatus.FAILED,
                MutationStatus.AMBIGUOUS,
                MutationStatus.EXECUTED,
            ):
                engine.store.save_mutation(
                    DurableMutationRecord(
                        action_id,
                        "credit",
                        "compensate_mutation",
                        "update_customer_note",
                        canonical,
                        status,
                    )
                )
                result = await handler(state)
                self.assertEqual(
                    result.outcome_type,
                    "compensation_completed"
                    if status == MutationStatus.EXECUTED
                    else "ambiguous_compensation"
                    if status == MutationStatus.AMBIGUOUS
                    else "compensation_failed",
                )
