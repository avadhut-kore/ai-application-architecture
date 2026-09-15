"""Human-in-the-Loop (HITL) step suspending workflow execution until human authorization."""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional

from contracts.workflow import ApprovalStatus, StepExecutionStatus

from ..approval import DurableApprovalRecord, canonicalize_arguments
from ..ledger import generate_stable_action_id
from ..state import RemediationProposal, StepOutcome, WorkflowState


class HumanApprovalStep:
    """Creates a durable approval record and suspends workflow execution to disk."""

    def __init__(self, store: Any, expiry_seconds: Optional[float] = 86400.0) -> None:
        self.store = store
        self.expiry_seconds = expiry_seconds

    async def execute(self, state: WorkflowState) -> StepOutcome:
        proposal_dict = state.domain_context.get("remediation_proposal", {})
        proposal = RemediationProposal.from_dict(proposal_dict)

        capability_name = state.domain_context.get("target_capability", "apply_fee_credit")
        target_args = dict(proposal.suggested_arguments)
        target_args["customer_id"] = state.domain_context.get("customer_id")

        canonical_args = canonicalize_arguments(target_args)

        # Generate stable action_id bound to workflow_id and canonical arguments
        action_id = generate_stable_action_id(
            workflow_id=state.workflow_id,
            step_name="mutation_execution",
            capability_name=capability_name,
            canonical_args=canonical_args,
        )

        approval_id = f"app-{uuid.uuid4().hex[:12]}"
        expires_at = time.time() + self.expiry_seconds if self.expiry_seconds else None

        approval_record = DurableApprovalRecord(
            approval_id=approval_id,
            workflow_id=state.workflow_id,
            workflow_definition_id=state.definition.definition_id,
            workflow_definition_version=state.definition.version,
            action_id=action_id,
            capability_name=capability_name,
            canonical_arguments_json=canonical_args,
            actor_id=state.initiator_actor.actor_id,
            actor_role=state.initiator_actor.role,
            status=ApprovalStatus.PENDING,
            reason=f"Remediation requires human approval: {proposal.summary}",
            requested_at=time.time(),
            expires_at=expires_at,
        )

        # Persist durable approval in SQLite
        self.store.save_approval(approval_record)

        return StepOutcome(
            status=StepExecutionStatus.SUSPENDED,
            outcome_type="awaiting_approval",
            context_updates={
                "pending_approval_id": approval_id,
                "stable_action_id": action_id,
                "target_capability": capability_name,
                "target_arguments": target_args,
            },
        )
