"""Strongly typed authority-bearing workflow state and execution record models."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Mapping, Optional, Sequence

from contracts.agent import ExecutionReceipt
from contracts.workflow import (
    StepExecutionStatus,
    WorkflowDefinitionRef,
    WorkflowStatus,
)


class RemediationType(str, Enum):
    """Classification of bounded diagnostic outcome proposed by the investigation agent."""

    INFORMATIONAL = "informational"
    CUSTOMER_NOTE = "customer_note"
    FEE_CREDIT = "fee_credit"
    SECURITY_ESCALATION = "security_escalation"


@dataclass(frozen=True)
class RemediationProposal:
    """Structured proposal emitted by the read-only investigation step (untrusted model output)."""

    proposal_type: RemediationType
    summary: str
    suggested_arguments: Mapping[str, Any] = field(default_factory=dict)
    requires_approval: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proposal_type": self.proposal_type.value,
            "summary": self.summary,
            "suggested_arguments": dict(self.suggested_arguments),
            "requires_approval": self.requires_approval,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> RemediationProposal:
        return cls(
            proposal_type=RemediationType(str(data["proposal_type"])),
            summary=str(data.get("summary", "")),
            suggested_arguments=dict(data.get("suggested_arguments", {})),
            requires_approval=bool(data.get("requires_approval", False)),
        )


@dataclass(frozen=True)
class WorkflowActorSnapshot:
    """Immutable identity and role context of the actor initiating the workflow."""

    actor_id: str
    role: str
    permissions: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.actor_id or not self.actor_id.strip():
            raise ValueError("Actor ID cannot be empty")
        if not self.role or not self.role.strip():
            raise ValueError("Actor role cannot be empty")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "role": self.role,
            "permissions": list(self.permissions),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowActorSnapshot:
        return cls(
            actor_id=str(data["actor_id"]),
            role=str(data["role"]),
            permissions=tuple(str(p) for p in data.get("permissions", ())),
        )


@dataclass(frozen=True)
class StepExecutionRecord:
    """Auditable record of a single step execution attempt."""

    step_name: str
    attempt: int
    status: StepExecutionStatus
    started_at: float
    completed_at: float
    outcome_type: Optional[str] = None
    execution_receipt_ids: Sequence[str] = field(default_factory=tuple)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "attempt": self.attempt,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "outcome_type": self.outcome_type,
            "execution_receipt_ids": list(self.execution_receipt_ids),
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> StepExecutionRecord:
        return cls(
            step_name=str(data["step_name"]),
            attempt=int(data["attempt"]),
            status=StepExecutionStatus(str(data["status"])),
            started_at=float(data["started_at"]),
            completed_at=float(data["completed_at"]),
            outcome_type=data.get("outcome_type"),
            execution_receipt_ids=tuple(str(rid) for rid in data.get("execution_receipt_ids", ())),
            error_message=data.get("error_message"),
        )


@dataclass(frozen=True)
class StepOutcome:
    """Immediate result payload returned by a step handler to the workflow engine."""

    status: StepExecutionStatus
    outcome_type: str
    proposal: Optional[RemediationProposal] = None
    context_updates: Mapping[str, Any] = field(default_factory=dict)
    receipts: Sequence[ExecutionReceipt] = field(default_factory=tuple)
    error_message: Optional[str] = None


@dataclass(frozen=True)
class WorkflowState:
    """Strongly typed authority-bearing workflow state model."""

    workflow_id: str
    definition: WorkflowDefinitionRef
    status: WorkflowStatus
    current_step: str
    initiator_actor: WorkflowActorSnapshot
    history: Sequence[StepExecutionRecord] = field(default_factory=tuple)
    pending_approval_id: Optional[str] = None
    step_retries: Mapping[str, int] = field(default_factory=dict)
    domain_context: Mapping[str, Any] = field(default_factory=dict)
    checkpoint_version: int = 1
    checksum: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def compute_checksum(self) -> str:
        """Compute SHA-256 integrity checksum for accidental corruption and tampering detection."""
        canon_domain = json.dumps(self.domain_context, sort_keys=True, default=str)
        canon_history = json.dumps([r.to_dict() for r in self.history], sort_keys=True, default=str)
        canon_retries = json.dumps(dict(self.step_retries), sort_keys=True)
        payload = (
            f"{self.workflow_id}|"
            f"{self.definition.definition_id}:{self.definition.version}|"
            f"{self.status.value}|"
            f"{self.current_step}|"
            f"{self.initiator_actor.actor_id}:{self.initiator_actor.role}|"
            f"{self.checkpoint_version}|"
            f"{self.pending_approval_id or ''}|"
            f"{canon_domain}|"
            f"{canon_history}|"
            f"{canon_retries}|"
            f"{self.created_at}|"
            f"{self.updated_at}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def with_updated_checksum(self) -> WorkflowState:
        """Return a copy of WorkflowState with fresh checksum computed."""
        new_checksum = self.compute_checksum()
        return WorkflowState(
            workflow_id=self.workflow_id,
            definition=self.definition,
            status=self.status,
            current_step=self.current_step,
            initiator_actor=self.initiator_actor,
            history=self.history,
            pending_approval_id=self.pending_approval_id,
            step_retries=self.step_retries,
            domain_context=self.domain_context,
            checkpoint_version=self.checkpoint_version,
            checksum=new_checksum,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to plain dictionary for durable JSON storage."""
        return {
            "workflow_id": self.workflow_id,
            "definition": {
                "definition_id": self.definition.definition_id,
                "version": self.definition.version,
            },
            "status": self.status.value,
            "current_step": self.current_step,
            "initiator_actor": self.initiator_actor.to_dict(),
            "history": [r.to_dict() for r in self.history],
            "pending_approval_id": self.pending_approval_id,
            "step_retries": dict(self.step_retries),
            "domain_context": dict(self.domain_context),
            "checkpoint_version": self.checkpoint_version,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowState:
        """Deserialize plain dictionary into typed WorkflowState."""
        definition_data = data["definition"]
        definition = WorkflowDefinitionRef(
            definition_id=str(definition_data["definition_id"]),
            version=str(definition_data["version"]),
        )
        actor = WorkflowActorSnapshot.from_dict(data["initiator_actor"])
        history = tuple(StepExecutionRecord.from_dict(r) for r in data.get("history", ()))
        return cls(
            workflow_id=str(data["workflow_id"]),
            definition=definition,
            status=WorkflowStatus(str(data["status"])),
            current_step=str(data["current_step"]),
            initiator_actor=actor,
            history=history,
            pending_approval_id=data.get("pending_approval_id"),
            step_retries=dict(data.get("step_retries", {})),
            domain_context=dict(data.get("domain_context", {})),
            checkpoint_version=int(data["checkpoint_version"]),
            checksum=str(data.get("checksum", "")),
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
        )
