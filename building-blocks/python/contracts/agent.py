"""Core domain models, protocols, and contracts for agentic task execution."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Protocol, Sequence, runtime_checkable

from .telemetry import AiOperationContext


class SideEffectLevel(str, Enum):
    """Classification of tool side effects and state modification impact."""

    READ_ONLY = "read_only"
    STATE_MUTATING = "state_mutating"


@dataclass(frozen=True)
class CapabilityMetadata:
    """Metadata describing an application capability exposed to models."""

    name: str
    description: str
    input_schema: Mapping[str, Any]
    side_effect_level: SideEffectLevel
    requires_approval: bool = False

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("Capability name cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Capability description cannot be empty")
        if not isinstance(self.input_schema, dict):
            raise TypeError("Capability input_schema must be a mapping dictionary")


@runtime_checkable
class CapabilityPort(Protocol):
    """Port interface for executable capabilities (tools) available to agents."""

    @property
    def metadata(self) -> CapabilityMetadata:
        """Return the capability metadata and input schema."""
        ...

    async def execute(
        self,
        arguments: Mapping[str, Any],
        context: Optional[AiOperationContext] = None,
    ) -> Any:
        """Execute the capability with validated arguments."""
        ...


class AgentDecisionType(str, Enum):
    """Classification of an agent's reasoning step decision."""

    ACTION = "action"
    FINAL = "final"
    CLARIFICATION = "clarification"


@dataclass(frozen=True)
class AgentDecision:
    """Structured decision emitted by the model during an agent step."""

    decision_type: AgentDecisionType
    action_name: Optional[str] = None
    arguments: Mapping[str, Any] = field(default_factory=dict)
    final_answer: Optional[str] = None
    clarification_question: Optional[str] = None
    explanation: Optional[str] = None

    def __post_init__(self) -> None:
        if self.decision_type == AgentDecisionType.ACTION:
            if not self.action_name or not self.action_name.strip():
                raise ValueError("Action decision must specify an action_name")
        elif self.decision_type == AgentDecisionType.FINAL:
            if not self.final_answer or not self.final_answer.strip():
                raise ValueError("Final decision must specify a final_answer")
        elif self.decision_type == AgentDecisionType.CLARIFICATION:
            if not self.clarification_question or not self.clarification_question.strip():
                raise ValueError("Clarification decision must specify a clarification_question")


@dataclass(frozen=True)
class AgentActor:
    """Identity and authorization context of the actor driving or initiating the agent."""

    actor_id: str
    role: str
    permissions: Sequence[str] = field(default_factory=list)


@dataclass(frozen=True)
class AuthorizationDecision:
    """Result of an application authorization check against an action proposal."""

    allowed: bool
    reason: str


@runtime_checkable
class AuthorizationPort(Protocol):
    """Port interface for evaluating whether an actor is authorized to execute a capability."""

    def authorize(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> AuthorizationDecision:
        """Evaluate authorization policy for the requested action."""
        ...


@dataclass(frozen=True)
class ApprovalDecision:
    """Result of a human-in-the-loop approval request."""

    approved: bool
    approver: str
    reason: Optional[str] = None


@runtime_checkable
class ApprovalPort(Protocol):
    """Port interface for obtaining human-in-the-loop approval for state-mutating actions."""

    async def request_approval(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> ApprovalDecision:
        """Prompt or request approval for a pending state-mutating operation."""
        ...


@dataclass(frozen=True)
class ExecutionReceipt:
    """Auditable receipt proving execution outcome of a capability."""

    action_id: str
    capability_name: str
    status: str  # "succeeded" | "failed" | "denied" | "rejected"
    executed_at: float = field(default_factory=time.time)
    result_summary: str = ""
    error_message: Optional[str] = None
