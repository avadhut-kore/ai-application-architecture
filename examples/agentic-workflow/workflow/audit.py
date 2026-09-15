"""Append-oriented workflow audit records and telemetry event logging."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional


@dataclass(frozen=True)
class WorkflowAuditEvent:
    """Structured, append-only audit event capturing a workflow progression milestone."""

    event_id: str
    workflow_id: str
    event_type: str
    step_name: Optional[str] = None
    details: Mapping[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "workflow_id": self.workflow_id,
            "event_type": self.event_type,
            "step_name": self.step_name,
            "details": dict(self.details),
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> WorkflowAuditEvent:
        return cls(
            event_id=str(data["event_id"]),
            workflow_id=str(data["workflow_id"]),
            event_type=str(data["event_type"]),
            step_name=data.get("step_name"),
            details=dict(data.get("details", {})),
            timestamp=float(data.get("timestamp", time.time())),
        )


class WorkflowAuditRecorder:
    """In-memory and persistent append-only event recorder for workflow telemetry."""

    def __init__(self) -> None:
        self._events: List[WorkflowAuditEvent] = []

    def record(
        self,
        workflow_id: str,
        event_type: str,
        step_name: Optional[str] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> WorkflowAuditEvent:
        """Create and append an audit event."""
        event = WorkflowAuditEvent(
            event_id=f"evt-{uuid.uuid4().hex[:12]}",
            workflow_id=workflow_id,
            event_type=event_type,
            step_name=step_name,
            details=details or {},
            timestamp=time.time(),
        )
        self._events.append(event)
        return event

    def get_events(self, workflow_id: Optional[str] = None) -> List[WorkflowAuditEvent]:
        """Return recorded events, optionally filtered by workflow ID."""
        if workflow_id is None:
            return list(self._events)
        return [e for e in self._events if e.workflow_id == workflow_id]
