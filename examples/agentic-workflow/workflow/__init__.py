"""Workflow orchestration module exports."""

from .approval import (
    DurableApprovalRecord,
    WorkflowApprovalAdapter,
    WorkflowApprovalVerifier,
    canonicalize_arguments,
)
from .audit import WorkflowAuditEvent, WorkflowAuditRecorder
from .definition import StepDefinition, TransitionRule, WorkflowDefinition
from .engine import WorkflowEngine
from .errors import (
    AmbiguousExecutionError,
    ApprovalMismatchError,
    ApprovalReplayError,
    ApprovalVerificationError,
    ConcurrentResumeConflictError,
    CorruptedCheckpointError,
    IncompatibleWorkflowDefinitionError,
    InvalidTransitionError,
    MaxTransitionsExceededError,
    SagaCompensationError,
    WorkflowDefinitionError,
    WorkflowExecutionError,
)
from .ledger import DurableMutationRecord, generate_stable_action_id
from .remediation_workflow import build_customer_remediation_workflow
from .retry import StepRetryPolicy
from .saga import CompensatingAction, SagaCompensationCoordinator, SagaCompensationRecord
from .state import (
    RemediationProposal,
    RemediationType,
    StepExecutionRecord,
    StepOutcome,
    WorkflowActorSnapshot,
    WorkflowState,
)
from .store import InMemoryWorkflowStore, SQLiteWorkflowStore

__all__ = [
    # Engine & Definition
    "WorkflowEngine",
    "WorkflowDefinition",
    "StepDefinition",
    "TransitionRule",
    "build_customer_remediation_workflow",
    # State & Proposals
    "WorkflowState",
    "WorkflowActorSnapshot",
    "StepOutcome",
    "StepExecutionRecord",
    "RemediationType",
    "RemediationProposal",
    # Approval
    "DurableApprovalRecord",
    "WorkflowApprovalVerifier",
    "WorkflowApprovalAdapter",
    "canonicalize_arguments",
    # Mutation Ledger
    "DurableMutationRecord",
    "generate_stable_action_id",
    # Persistence
    "InMemoryWorkflowStore",
    "SQLiteWorkflowStore",
    # Observability & Reliability
    "WorkflowAuditRecorder",
    "WorkflowAuditEvent",
    "StepRetryPolicy",
    # Saga
    "CompensatingAction",
    "SagaCompensationCoordinator",
    "SagaCompensationRecord",
    # Errors
    "WorkflowExecutionError",
    "WorkflowDefinitionError",
    "IncompatibleWorkflowDefinitionError",
    "InvalidTransitionError",
    "MaxTransitionsExceededError",
    "ApprovalVerificationError",
    "ApprovalReplayError",
    "ApprovalMismatchError",
    "ConcurrentResumeConflictError",
    "CorruptedCheckpointError",
    "AmbiguousExecutionError",
    "SagaCompensationError",
]
