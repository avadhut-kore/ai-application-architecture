"""Bounded core contracts and protocols for workflow orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, runtime_checkable


class WorkflowStatus(str, Enum):
    """Lifecycle status of a durable workflow instance."""

    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"
    ESCALATED = "escalated"

    @property
    def is_terminal(self) -> bool:
        """Return True if status represents a concluded workflow."""
        return self in (
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.REJECTED,
            WorkflowStatus.ESCALATED,
        )


class StepExecutionStatus(str, Enum):
    """Execution status returned by an individual workflow step handler."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SUSPENDED = "suspended"


class ApprovalStatus(str, Enum):
    """Durable lifecycle status of a human approval authorization request."""

    PENDING = "pending"
    APPROVED = "approved"
    CONSUMED = "consumed"
    REJECTED = "rejected"
    EXPIRED = "expired"

    @property
    def is_terminal(self) -> bool:
        """Return True if approval status represents a concluded decision."""
        return self in (
            ApprovalStatus.CONSUMED,
            ApprovalStatus.REJECTED,
            ApprovalStatus.EXPIRED,
        )


class MutationStatus(str, Enum):
    """Lifecycle states of a physical state mutation in the durable mutation ledger."""

    PLANNED = "planned"
    EXECUTION_STARTED = "execution_started"
    EXECUTED = "executed"
    FAILED = "failed"
    AMBIGUOUS = "ambiguous"

    @property
    def is_terminal(self) -> bool:
        """Return True if mutation status represents completed reconciliation or execution."""
        return self in (
            MutationStatus.EXECUTED,
            MutationStatus.FAILED,
        )


@dataclass(frozen=True)
class WorkflowDefinitionRef:
    """Immutable identifier and version reference for a workflow definition."""

    definition_id: str
    version: str

    def __post_init__(self) -> None:
        if not self.definition_id or not self.definition_id.strip():
            raise ValueError("Workflow definition_id cannot be empty")
        if not self.version or not self.version.strip():
            raise ValueError("Workflow definition version cannot be empty")


@runtime_checkable
class CheckpointStorePort(Protocol):
    """Provider-neutral port for durable workflow checkpoint persistence."""

    async def save_checkpoint(
        self,
        workflow_id: str,
        state_payload: Mapping[str, Any],
        checkpoint_version: int,
    ) -> None:
        """Save a workflow checkpoint with optimistic concurrency version checking."""
        ...

    async def load_checkpoint(
        self,
        workflow_id: str,
    ) -> Optional[Mapping[str, Any]]:
        """Load a persisted workflow checkpoint by unique workflow instance ID."""
        ...
