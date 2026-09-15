"""Durable mutation ledger, stable action identity, and reconciliation records."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional

from contracts.agent import ExecutionReceipt
from contracts.workflow import MutationStatus


def generate_stable_action_id(
    workflow_id: str,
    step_name: str,
    capability_name: str,
    canonical_args: str,
) -> str:
    """Generate a deterministic, stable action ID that survives process restarts."""
    payload = f"{workflow_id}:{step_name}:{capability_name}:{canonical_args}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"act-{workflow_id}-{step_name}-{digest}"


@dataclass(frozen=True)
class DurableMutationRecord:
    """Auditable state mutation record tracked durably in the mutation ledger."""

    action_id: str
    workflow_id: str
    step_name: str
    capability_name: str
    canonical_args: str
    status: MutationStatus = MutationStatus.PLANNED
    execution_receipt: Optional[ExecutionReceipt] = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        if isinstance(self.status, str):
            object.__setattr__(self, "status", MutationStatus(self.status))

    def to_dict(self) -> Dict[str, Any]:
        receipt_dict = None
        if self.execution_receipt:
            receipt_dict = {
                "action_id": self.execution_receipt.action_id,
                "capability_name": self.execution_receipt.capability_name,
                "status": self.execution_receipt.status,
                "executed_at": self.execution_receipt.executed_at,
                "result_summary": self.execution_receipt.result_summary,
                "error_message": self.execution_receipt.error_message,
            }
        return {
            "action_id": self.action_id,
            "workflow_id": self.workflow_id,
            "step_name": self.step_name,
            "capability_name": self.capability_name,
            "canonical_args": self.canonical_args,
            "status": self.status.value,
            "execution_receipt": receipt_dict,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> DurableMutationRecord:
        receipt = None
        receipt_data = data.get("execution_receipt")
        if receipt_data:
            receipt = ExecutionReceipt(
                action_id=str(receipt_data["action_id"]),
                capability_name=str(receipt_data["capability_name"]),
                status=str(receipt_data["status"]),
                executed_at=float(receipt_data["executed_at"]),
                result_summary=str(receipt_data.get("result_summary", "")),
                error_message=receipt_data.get("error_message"),
            )
        return cls(
            action_id=str(data["action_id"]),
            workflow_id=str(data["workflow_id"]),
            step_name=str(data["step_name"]),
            capability_name=str(data["capability_name"]),
            canonical_args=str(data["canonical_args"]),
            status=MutationStatus(str(data["status"])),
            execution_receipt=receipt,
            created_at=float(data.get("created_at", time.time())),
            updated_at=float(data.get("updated_at", time.time())),
        )
