"""Pre-verified state mutation execution step with durable ledger recording."""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional

from contracts.agent import (
    AgentActor,
    CapabilityPort,
    ExecutionReceipt,
    SideEffectLevel,
)
from contracts.workflow import (
    ApprovalStatus,
    MutationStatus,
    StepExecutionStatus,
)

from ..approval import (
    DurableApprovalRecord,
    WorkflowApprovalVerifier,
    canonicalize_arguments,
)
from ..ledger import DurableMutationRecord, generate_stable_action_id
from ..state import StepOutcome, WorkflowState


class MutationExecutionStep:
    """Executes state-mutating capability following strict authorization and approval verification."""

    def __init__(
        self,
        capability: CapabilityPort,
        tool_executor: Any,
        store: Any,
        policy: Any,
        requires_approval: bool = True,
    ) -> None:
        self.capability = capability
        self.tool_executor = tool_executor
        self.store = store
        self.policy = policy
        self.requires_approval = requires_approval

    async def execute(self, state: WorkflowState) -> StepOutcome:
        target_args = dict(state.domain_context.get("target_arguments", {}))
        if not target_args and "remediation_proposal" in state.domain_context:
            prop_dict = state.domain_context.get("remediation_proposal", {})
            suggested = prop_dict.get("suggested_arguments", {})
            target_args = dict(suggested)
            if "customer_id" not in target_args and "customer_id" in state.domain_context:
                target_args["customer_id"] = state.domain_context["customer_id"]

        canonical_args = canonicalize_arguments(target_args)

        action_id = state.domain_context.get("stable_action_id") or generate_stable_action_id(
            workflow_id=state.workflow_id,
            step_name="mutation_execution",
            capability_name=self.capability.metadata.name,
            canonical_args=canonical_args,
        )

        actor = AgentActor(
            actor_id=state.initiator_actor.actor_id,
            role=state.initiator_actor.role,
            permissions=list(state.initiator_actor.permissions),
        )

        # 1. Idempotency Check: Inspect Durable Mutation Ledger
        existing_mutation = self.store.load_mutation(action_id)
        if existing_mutation and existing_mutation.status == MutationStatus.EXECUTED:
            receipt = existing_mutation.execution_receipt or ExecutionReceipt(
                action_id=action_id,
                capability_name=self.capability.metadata.name,
                status="succeeded",
                result_summary="Replayed from durable mutation ledger (duplicate suppressed).",
            )
            return StepOutcome(
                status=StepExecutionStatus.SUCCEEDED,
                outcome_type="mutation_succeeded",
                context_updates={"mutation_executed": True, "duplicate_suppressed": True},
                receipts=(receipt,),
            )

        # 2. TOCTOU Authorization Revalidation
        auth_decision = self.policy.authorize(actor, self.capability.metadata, target_args)
        if not auth_decision.allowed:
            return StepOutcome(
                status=StepExecutionStatus.FAILED,
                outcome_type="authorization_denied",
                error_message=f"Authorization revoked on resume: {auth_decision.reason}",
            )

        # 3. Pre-Execution Approval Verification (7-point binding check)
        is_mutating = (self.capability.metadata.side_effect_level == SideEffectLevel.STATE_MUTATING)
        requires_approval = self.requires_approval and (self.capability.metadata.requires_approval or is_mutating)
        approval_record: Optional[DurableApprovalRecord] = None

        if requires_approval:
            approval_record = self.store.load_approval_by_action_id(action_id)
            if not approval_record:
                approval_id = state.domain_context.get("pending_approval_id")
                if approval_id:
                    approval_record = self.store.load_approval(approval_id)

            if not approval_record:
                return StepOutcome(
                    status=StepExecutionStatus.FAILED,
                    outcome_type="approval_verification_failed",
                    error_message=f"No durable approval record found for action '{action_id}'.",
                )

            try:
                WorkflowApprovalVerifier.verify(
                    record=approval_record,
                    expected_workflow_id=state.workflow_id,
                    expected_action_id=action_id,
                    capability=self.capability.metadata,
                    arguments=target_args,
                    actor=actor,
                )
            except Exception as exc:
                return StepOutcome(
                    status=StepExecutionStatus.FAILED,
                    outcome_type="approval_verification_failed",
                    error_message=f"Approval verification rejected: {str(exc)}",
                )

        # 4. Record Intent in Durable Mutation Ledger: EXECUTION_STARTED
        in_flight_mutation = DurableMutationRecord(
            action_id=action_id,
            workflow_id=state.workflow_id,
            step_name="mutation_execution",
            capability_name=self.capability.metadata.name,
            canonical_args=canonical_args,
            status=MutationStatus.EXECUTION_STARTED,
            created_at=time.time(),
            updated_at=time.time(),
        )
        self.store.save_mutation(in_flight_mutation)

        # 5. Execute Physical Capability via Phase 6 ToolExecutor
        args_with_id = dict(target_args)
        args_with_id["action_id"] = action_id
        receipt, raw_output = await self.tool_executor.execute_tool(
            self.capability,
            args_with_id,
            action_id=action_id,
        )

        now = time.time()
        # 6. Atomic Commit: Ledger EXECUTED + Approval CONSUMED
        if receipt.status == "succeeded":
            executed_mutation = DurableMutationRecord(
                action_id=action_id,
                workflow_id=state.workflow_id,
                step_name="mutation_execution",
                capability_name=self.capability.metadata.name,
                canonical_args=canonical_args,
                status=MutationStatus.EXECUTED,
                execution_receipt=receipt,
                created_at=in_flight_mutation.created_at,
                updated_at=now,
            )

            if approval_record:
                consumed_approval = DurableApprovalRecord(
                    approval_id=approval_record.approval_id,
                    workflow_id=approval_record.workflow_id,
                    workflow_definition_id=approval_record.workflow_definition_id,
                    workflow_definition_version=approval_record.workflow_definition_version,
                    action_id=approval_record.action_id,
                    capability_name=approval_record.capability_name,
                    canonical_arguments_json=approval_record.canonical_arguments_json,
                    actor_id=approval_record.actor_id,
                    actor_role=approval_record.actor_role,
                    status=ApprovalStatus.CONSUMED,
                    approver_id=approval_record.approver_id,
                    approver_role=approval_record.approver_role,
                    reason=approval_record.reason,
                    requested_at=approval_record.requested_at,
                    decided_at=approval_record.decided_at,
                    consumed_at=now,
                    execution_receipt_id=receipt.action_id,
                    expires_at=approval_record.expires_at,
                )
                self.store.atomic_commit_mutation_and_approval(executed_mutation, consumed_approval)
            else:
                self.store.save_mutation(executed_mutation)

            return StepOutcome(
                status=StepExecutionStatus.SUCCEEDED,
                outcome_type="mutation_succeeded",
                context_updates={
                    "mutation_executed": True,
                    "execution_receipt_id": receipt.action_id,
                    "mutation_output": raw_output,
                },
                receipts=(receipt,),
            )
        else:
            failed_mutation = DurableMutationRecord(
                action_id=action_id,
                workflow_id=state.workflow_id,
                step_name="mutation_execution",
                capability_name=self.capability.metadata.name,
                canonical_args=canonical_args,
                status=MutationStatus.FAILED,
                execution_receipt=receipt,
                created_at=in_flight_mutation.created_at,
                updated_at=now,
            )
            self.store.save_mutation(failed_mutation)

            return StepOutcome(
                status=StepExecutionStatus.FAILED,
                outcome_type="mutation_failed",
                error_message=receipt.error_message or "Physical capability execution failed.",
                receipts=(receipt,),
            )
