"""Workflow orchestration domain errors and failure hierarchy."""

from __future__ import annotations


class WorkflowExecutionError(Exception):
    """Base exception for all workflow execution errors."""


class WorkflowDefinitionError(WorkflowExecutionError):
    """Raised when a workflow graph definition is structurally invalid."""


class IncompatibleWorkflowDefinitionError(WorkflowExecutionError):
    """Raised when a persisted workflow cannot be safely resumed by active code."""


class InvalidTransitionError(WorkflowExecutionError):
    """Raised when a step attempts an undeclared or illegal state transition."""


class MaxTransitionsExceededError(WorkflowExecutionError):
    """Raised when execution transitions exceed the configured global ceiling."""


class ApprovalVerificationError(WorkflowExecutionError):
    """Raised when approval binding or authorization validation fails prior to execution."""


class ApprovalReplayError(ApprovalVerificationError):
    """Raised when an already-consumed approval is presented for execution."""


class ApprovalMismatchError(ApprovalVerificationError):
    """Raised when approval arguments, capability, or actor do not match the intended action."""


class ConcurrentResumeConflictError(WorkflowExecutionError):
    """Raised when optimistic concurrency (compare-and-swap) detects competing execution."""


class CorruptedCheckpointError(WorkflowExecutionError):
    """Raised when checkpoint deserialization detects checksum integrity failure."""


class AmbiguousExecutionError(WorkflowExecutionError):
    """Raised when a mutation state is ambiguous and cannot be automatically reconciled."""


class SagaCompensationError(WorkflowExecutionError):
    """Raised when a compensating action in the local saga fails."""
