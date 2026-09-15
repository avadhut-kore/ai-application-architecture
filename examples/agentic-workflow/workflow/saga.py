"""Local Saga compensation models and coordinator for backward recovery."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

from contracts.agent import CapabilityPort, ExecutionReceipt
from contracts.telemetry import AiOperationContext

from .errors import SagaCompensationError
from .ledger import generate_stable_action_id


@dataclass(frozen=True)
class CompensatingAction:
    """Defined compensating capability call intended to reverse a prior forward mutation."""

    original_action_id: str
    step_name: str
    capability: CapabilityPort
    arguments: Mapping[str, Any]
    reason: str


@dataclass(frozen=True)
class SagaCompensationRecord:
    """Auditable evidence of a completed or attempted compensating action."""

    original_action_id: str
    compensating_action_id: str
    capability_name: str
    status: str  # "succeeded" | "failed"
    executed_at: float = field(default_factory=time.time)
    receipt: Optional[ExecutionReceipt] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_action_id": self.original_action_id,
            "compensating_action_id": self.compensating_action_id,
            "capability_name": self.capability_name,
            "status": self.status,
            "executed_at": self.executed_at,
            "error_message": self.error_message,
        }


class SagaCompensationCoordinator:
    """Coordinates local linear backward compensation when a multi-step mutation fails."""

    def __init__(self, workflow_id: str) -> None:
        self.workflow_id = workflow_id
        self._registered_compensations: List[CompensatingAction] = []
        self.executed_compensations: List[SagaCompensationRecord] = []

    def register(
        self,
        original_action_id: str,
        step_name: str,
        capability: CapabilityPort,
        arguments: Mapping[str, Any],
        reason: str,
    ) -> None:
        """Register a compensating action to be executed if downstream steps fail."""
        self._registered_compensations.append(
            CompensatingAction(
                original_action_id=original_action_id,
                step_name=step_name,
                capability=capability,
                arguments=dict(arguments),
                reason=reason,
            )
        )

    async def compensate_all(
        self,
        context: Optional[AiOperationContext] = None,
    ) -> Sequence[SagaCompensationRecord]:
        """Execute all registered compensating actions in reverse order (LIFO)."""
        records: List[SagaCompensationRecord] = []
        has_failure = False

        # Reverse order for backward compensation
        for action in reversed(self._registered_compensations):
            comp_action_id = generate_stable_action_id(
                workflow_id=self.workflow_id,
                step_name=f"comp_{action.step_name}",
                capability_name=action.capability.metadata.name,
                canonical_args=str(action.arguments),
            )
            # Merge action_id into arguments for capability execution
            args_with_id = dict(action.arguments)
            args_with_id["action_id"] = comp_action_id

            try:
                result = await action.capability.execute(args_with_id, context=context)
                receipt = ExecutionReceipt(
                    action_id=comp_action_id,
                    capability_name=action.capability.metadata.name,
                    status="succeeded",
                    executed_at=time.time(),
                    result_summary=f"Compensated {action.original_action_id}: {action.reason}",
                )
                rec = SagaCompensationRecord(
                    original_action_id=action.original_action_id,
                    compensating_action_id=comp_action_id,
                    capability_name=action.capability.metadata.name,
                    status="succeeded",
                    receipt=receipt,
                )
                records.append(rec)
                self.executed_compensations.append(rec)
            except Exception as exc:
                has_failure = True
                rec = SagaCompensationRecord(
                    original_action_id=action.original_action_id,
                    compensating_action_id=comp_action_id,
                    capability_name=action.capability.metadata.name,
                    status="failed",
                    error_message=str(exc),
                )
                records.append(rec)
                self.executed_compensations.append(rec)

        if has_failure:
            raise SagaCompensationError(
                f"Saga backward compensation failed for workflow '{self.workflow_id}'. "
                "Manual intervention required."
            )

        return records
