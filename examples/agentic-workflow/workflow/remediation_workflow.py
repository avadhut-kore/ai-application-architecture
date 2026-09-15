"""Reference Customer Account Remediation workflow definition builder."""

from __future__ import annotations

from typing import Any, Mapping

from contracts.workflow import StepExecutionStatus, WorkflowStatus

from .definition import StepDefinition, TransitionRule, WorkflowDefinition
from .state import RemediationType, StepOutcome, WorkflowState
from .steps import (
    AgenticInvestigationStep,
    ContextGatheringStep,
    FinalizationStep,
    HumanApprovalStep,
    IntakeValidationStep,
    MutationExecutionStep,
)


def build_customer_remediation_workflow(
    customer_store: Any,
    agent_engine: Any,
    read_only_registry: Any,
    credit_capability: Any,
    note_capability: Any,
    tool_executor: Any,
    workflow_store: Any,
    auth_policy: Any,
    definition_version: str = "1.0.0",
    max_transitions: int = 15,
) -> WorkflowDefinition:
    """Construct the canonical Customer Account Remediation workflow graph."""

    # 1. Instantiate step handlers
    intake_step = IntakeValidationStep(customer_store=customer_store)
    context_step = ContextGatheringStep(customer_store=customer_store)
    agentic_step = AgenticInvestigationStep(
        agent_engine=agent_engine,
        read_only_registry=read_only_registry,
    )
    human_step = HumanApprovalStep(store=workflow_store)
    mutation_credit_step = MutationExecutionStep(
        capability=credit_capability,
        tool_executor=tool_executor,
        store=workflow_store,
        policy=auth_policy,
    )
    mutation_note_step = MutationExecutionStep(
        capability=note_capability,
        tool_executor=tool_executor,
        store=workflow_store,
        policy=auth_policy,
        requires_approval=False,
    )
    finalize_step = FinalizationStep()

    async def compensate_step_handler(state: WorkflowState) -> StepOutcome:
        """Local saga compensation step executing inverse note update."""
        customer_id = state.domain_context.get("customer_id", "")
        action_id = f"comp-note-{state.workflow_id}"
        comp_args = {
            "customer_id": customer_id,
            "note": f"COMPENSATION: Fee credit disbursement failed for workflow {state.workflow_id}. Concession note voided.",
            "action_id": action_id,
        }
        receipt, _ = await tool_executor.execute_tool(note_capability, comp_args, action_id=action_id)
        return StepOutcome(
            status=StepExecutionStatus.SUCCEEDED,
            outcome_type="compensation_completed",
            context_updates={"compensation_applied": True, "compensating_receipt_id": receipt.action_id},
            receipts=(receipt,),
        )

    # 2. Define steps and declared transitions
    steps = [
        # Step: INTAKE_VALIDATION
        StepDefinition(
            name="intake_validation",
            handler=intake_step.execute,
            transitions=(
                TransitionRule(
                    target_step="context_gathering",
                    condition_fn=lambda s, o: o.status == StepExecutionStatus.SUCCEEDED,
                    description="Valid input advances to context gathering",
                ),
            ),
            default_transition="terminal_failed",
        ),
        # Step: CONTEXT_GATHERING
        StepDefinition(
            name="context_gathering",
            handler=context_step.execute,
            transitions=(
                TransitionRule(
                    target_step="agentic_investigation",
                    condition_fn=lambda s, o: o.status == StepExecutionStatus.SUCCEEDED,
                    description="Context loaded advances to agentic investigation",
                ),
            ),
            default_transition="terminal_failed",
        ),
        # Step: AGENTIC_INVESTIGATION
        StepDefinition(
            name="agentic_investigation",
            handler=agentic_step.execute,
            transitions=(
                TransitionRule(
                    target_step="finalization",
                    condition_fn=lambda s, o: o.outcome_type == RemediationType.INFORMATIONAL.value,
                    description="Informational outcome advances directly to finalization",
                ),
                TransitionRule(
                    target_step="terminal_escalated",
                    condition_fn=lambda s, o: o.outcome_type == RemediationType.SECURITY_ESCALATION.value,
                    description="Security hold or fraud detection escalates to compliance",
                ),
                TransitionRule(
                    target_step="human_approval",
                    condition_fn=lambda s, o: o.outcome_type == RemediationType.FEE_CREDIT.value,
                    description="Fee credit mutation routes to human approval checkpoint",
                ),
                TransitionRule(
                    target_step="mutate_note",
                    condition_fn=lambda s, o: o.outcome_type == RemediationType.CUSTOMER_NOTE.value,
                    description="Customer note routes to direct mutation step",
                ),
            ),
            default_transition="terminal_failed",
        ),
        # Step: HUMAN_APPROVAL (Suspension Point)
        StepDefinition(
            name="human_approval",
            handler=human_step.execute,
            transitions=(
                TransitionRule(
                    target_step="mutation_execution",
                    condition_fn=lambda s, o: o.outcome_type == "approval_granted",
                    description="Approved credit advances to execution",
                ),
                TransitionRule(
                    target_step="terminal_rejected",
                    condition_fn=lambda s, o: o.outcome_type == "approval_rejected",
                    description="Rejected credit routes to terminal rejected",
                ),
            ),
            default_transition="terminal_failed",
        ),
        # Step: MUTATION_EXECUTION (Fee Credit)
        StepDefinition(
            name="mutation_execution",
            handler=mutation_credit_step.execute,
            transitions=(
                TransitionRule(
                    target_step="finalization",
                    condition_fn=lambda s, o: o.status == StepExecutionStatus.SUCCEEDED,
                    description="Successful mutation advances to finalization",
                ),
                TransitionRule(
                    target_step="compensate_mutation",
                    condition_fn=lambda s, o: o.status == StepExecutionStatus.FAILED
                    and bool(s.domain_context.get("has_prior_note")),
                    description="Multi-step failure triggers local saga backward compensation",
                ),
            ),
            default_transition="terminal_failed",
            is_mutating=True,
        ),
        # Step: MUTATE_NOTE (Customer Note)
        StepDefinition(
            name="mutate_note",
            handler=mutation_note_step.execute,
            transitions=(
                TransitionRule(
                    target_step="finalization",
                    condition_fn=lambda s, o: o.status == StepExecutionStatus.SUCCEEDED,
                    description="Successful note mutation advances to finalization",
                ),
            ),
            default_transition="terminal_failed",
            is_mutating=True,
        ),
        # Step: COMPENSATE_MUTATION (Local Saga Step)
        StepDefinition(
            name="compensate_mutation",
            handler=compensate_step_handler,
            transitions=(),
            default_transition="terminal_failed",
            is_mutating=True,
        ),
        # Step: FINALIZATION
        StepDefinition(
            name="finalization",
            handler=finalize_step.execute,
            transitions=(),
            default_transition="terminal_completed",
        ),
        # Terminal Steps
        StepDefinition(
            name="terminal_completed",
            handler=lambda s: StepOutcome(status=StepExecutionStatus.SUCCEEDED, outcome_type="completed"),
            is_terminal=True,
            terminal_status=WorkflowStatus.COMPLETED,
        ),
        StepDefinition(
            name="terminal_failed",
            handler=lambda s: StepOutcome(status=StepExecutionStatus.FAILED, outcome_type="failed"),
            is_terminal=True,
            terminal_status=WorkflowStatus.FAILED,
        ),
        StepDefinition(
            name="terminal_rejected",
            handler=lambda s: StepOutcome(status=StepExecutionStatus.SUCCEEDED, outcome_type="rejected"),
            is_terminal=True,
            terminal_status=WorkflowStatus.REJECTED,
        ),
        StepDefinition(
            name="terminal_escalated",
            handler=lambda s: StepOutcome(status=StepExecutionStatus.SUCCEEDED, outcome_type="escalated"),
            is_terminal=True,
            terminal_status=WorkflowStatus.ESCALATED,
        ),
    ]

    return WorkflowDefinition(
        definition_id="customer_account_remediation",
        version=definition_version,
        start_step="intake_validation",
        steps=steps,
        max_transitions=max_transitions,
    )
