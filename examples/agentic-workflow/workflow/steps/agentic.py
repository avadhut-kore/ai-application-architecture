"""Agentic investigation step integrating frozen Phase 6 AgentExecutionEngine."""

from __future__ import annotations

import json
import re
from typing import Any, Mapping, Optional

from contracts.agent import AgentActor, SideEffectLevel
from contracts.workflow import StepExecutionStatus

from ..state import RemediationProposal, RemediationType, StepOutcome, WorkflowState

PROPOSAL_JSON_PATTERN = re.compile(r"\{.*\}", re.DOTALL)


class AgenticInvestigationStep:
    """Delegates bounded diagnosis to Phase 6 Agent with strictly read-only capabilities."""

    def __init__(
        self,
        agent_engine: Any,
        read_only_registry: Any,
    ) -> None:
        self.agent_engine = agent_engine
        self.registry = read_only_registry
        self._verify_read_only_registry()

    def _verify_read_only_registry(self) -> None:
        """Enforce critical safety invariant: Zero mutating tools in investigation registry."""
        for item in self.registry.list_capabilities():
            if isinstance(item, str):
                cap = self.registry.get(item)
                meta = cap.metadata if cap else None
            else:
                meta = item
            if meta and meta.side_effect_level == SideEffectLevel.STATE_MUTATING:
                raise ValueError(
                    f"Security Invariant Violation: Mutating capability '{meta.name}' detected "
                    "in AgenticInvestigationStep registry. Investigation must be strictly read-only."
                )

    def _parse_proposal_from_answer(self, raw_text: str) -> RemediationProposal:
        """Parse untrusted model text into a strongly typed RemediationProposal."""
        # Attempt to parse JSON proposal block
        match = PROPOSAL_JSON_PATTERN.search(raw_text)
        if match:
            try:
                data = json.loads(match.group(0))
                if isinstance(data, dict) and "proposal_type" in data:
                    prop_type_str = str(data["proposal_type"]).lower()
                    for t in RemediationType:
                        if t.value == prop_type_str:
                            return RemediationProposal(
                                proposal_type=t,
                                summary=str(data.get("summary", raw_text[:200])),
                                suggested_arguments=dict(data.get("suggested_arguments", {})),
                                requires_approval=bool(data.get("requires_approval", t == RemediationType.FEE_CREDIT)),
                            )
            except Exception:
                pass

        # Fallback text heuristic matching
        lower_text = raw_text.lower()
        if "frozen" in lower_text or "escalat" in lower_text or "security hold" in lower_text:
            return RemediationProposal(
                proposal_type=RemediationType.SECURITY_ESCALATION,
                summary=raw_text[:200],
                requires_approval=False,
            )
        elif "credit" in lower_text or "refund" in lower_text or "waive" in lower_text:
            # Extract amount if present
            amount_cents = 1500  # Default $15 concession heuristic
            amount_match = re.search(r"\$?(\d+(?:\.\d{2})?)", raw_text)
            if amount_match:
                val = float(amount_match.group(1))
                amount_cents = int(val * 100) if val < 100 else int(val)

            return RemediationProposal(
                proposal_type=RemediationType.FEE_CREDIT,
                summary=raw_text[:200],
                suggested_arguments={
                    "amount_cents": min(amount_cents, 5000),
                    "reason": "Customer billing dispute adjustment",
                },
                requires_approval=True,
            )
        elif "note" in lower_text:
            return RemediationProposal(
                proposal_type=RemediationType.CUSTOMER_NOTE,
                summary=raw_text[:200],
                suggested_arguments={"note": "Inquiry reviewed; operational note documented."},
                requires_approval=False,
            )

        return RemediationProposal(
            proposal_type=RemediationType.INFORMATIONAL,
            summary=raw_text,
            requires_approval=False,
        )

    async def execute(self, state: WorkflowState) -> StepOutcome:
        customer_id = state.domain_context.get("customer_id", "")
        inquiry = state.domain_context.get("issue_description", "Customer billing inquiry")

        goal = (
            f"Investigate customer inquiry for '{customer_id}': {inquiry}. "
            "Inspect customer status, account balance, and dispute policies. "
            "Determine the appropriate remediation proposal: INFORMATIONAL, CUSTOMER_NOTE, "
            "FEE_CREDIT, or SECURITY_ESCALATION."
        )

        actor = AgentActor(
            actor_id=state.initiator_actor.actor_id,
            role=state.initiator_actor.role,
            permissions=list(state.initiator_actor.permissions),
        )

        # Run bounded Phase 6 agent
        result = await self.agent_engine.run(goal, actor=actor)

        # Invariant check: Ensure NO mutating capabilities were executed
        execution_receipts = getattr(result, "execution_receipts", ()) or ()
        for receipt in execution_receipts:
            cap = self.registry.get(receipt.capability_name)
            if cap and cap.metadata.side_effect_level == SideEffectLevel.STATE_MUTATING:
                raise RuntimeError(
                    f"Fatal Security Breach: Mutating capability '{receipt.capability_name}' was executed "
                    "during read-only agentic investigation."
                )

        if getattr(result, "status", "") == "FAILED":
            return StepOutcome(
                status=StepExecutionStatus.FAILED,
                outcome_type="agent_failed",
                error_message=getattr(result, "final_answer", "Agent execution failed."),
                receipts=tuple(execution_receipts),
            )

        proposal = self._parse_proposal_from_answer(getattr(result, "final_answer", ""))

        return StepOutcome(
            status=StepExecutionStatus.SUCCEEDED,
            outcome_type=proposal.proposal_type.value,
            proposal=proposal,
            context_updates={
                "agent_run_id": getattr(result, "run_id", "run-unknown"),
                "remediation_proposal": proposal.to_dict(),
            },
            receipts=tuple(execution_receipts),
        )
