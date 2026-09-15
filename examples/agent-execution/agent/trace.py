"""Auditable execution trace recording without persisting hidden chain-of-thought."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from contracts.agent import (
    AgentActor,
    AgentDecision,
    ApprovalDecision,
    AuthorizationDecision,
    ExecutionReceipt,
)
from contracts.validation import ValidationResult


@dataclass
class AgentStepRecord:
    """Detailed audit record of an individual reasoning and action cycle."""

    step_number: int
    decision: AgentDecision
    validation_result: Optional[ValidationResult] = None
    authorization_result: Optional[AuthorizationDecision] = None
    approval_result: Optional[ApprovalDecision] = None
    execution_receipt: Optional[ExecutionReceipt] = None
    sanitized_observation: Optional[str] = None
    step_latency_ms: float = 0.0


@dataclass
class AgentTrajectoryTrace:
    """Complete auditable execution trace for an agent run."""

    run_id: str
    goal: str
    actor: AgentActor
    steps: List[AgentStepRecord] = field(default_factory=list)
    final_status: str = "PENDING"  # COMPLETED | NEEDS_CLARIFICATION | DENIED | REJECTED | FAILED | MAX_STEPS_REACHED
    final_answer: Optional[str] = None
    total_latency_ms: float = 0.0
    start_time: float = field(default_factory=time.time)

    def record_step(self, step: AgentStepRecord) -> None:
        """Append an audited step record."""
        self.steps.append(step)

    def complete(self, status: str, answer: Optional[str] = None) -> None:
        """Mark the trajectory as concluded with final outcome."""
        self.final_status = status
        self.final_answer = answer
        self.total_latency_ms = round((time.time() - self.start_time) * 1000.0, 2)

    def to_audit_summary(self) -> Mapping[str, Any]:
        """Produce safe structured audit dictionary without secret or PII leakage."""
        step_summaries = []
        for s in self.steps:
            item: Dict[str, Any] = {
                "step": s.step_number,
                "decision_type": s.decision.decision_type.value,
            }
            if s.decision.action_name:
                item["action"] = s.decision.action_name
            if s.authorization_result:
                item["authorized"] = s.authorization_result.allowed
            if s.approval_result:
                item["approved"] = s.approval_result.approved
            if s.execution_receipt:
                item["execution_status"] = s.execution_receipt.status
                item["receipt_id"] = s.execution_receipt.action_id
            step_summaries.append(item)

        return {
            "run_id": self.run_id,
            "goal": self.goal,
            "actor_id": self.actor.actor_id,
            "actor_role": self.actor.role,
            "final_status": self.final_status,
            "step_count": len(self.steps),
            "total_latency_ms": self.total_latency_ms,
            "steps": step_summaries,
        }
