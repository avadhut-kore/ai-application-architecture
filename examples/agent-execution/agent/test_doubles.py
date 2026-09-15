"""Deterministic test doubles conforming to TextGenerationPort for agent testing."""

from __future__ import annotations

import json
from typing import Any, List, Mapping, Optional, Sequence, Union

from contracts.agent import AgentDecision, AgentDecisionType
from contracts.models import (
    CompletionRequest,
    CompletionResponse,
    FinishReason,
    UsageMetrics,
)
from contracts.ports import TextGenerationPort
from contracts.telemetry import AiOperationContext


def decision_to_json(decision: AgentDecision) -> str:
    """Format AgentDecision as clean structured JSON string matching required schema."""
    payload: dict[str, Any] = {
        "type": decision.decision_type.value,
        "explanation": decision.explanation or "Deterministic reasoning step",
    }
    if decision.decision_type == AgentDecisionType.ACTION:
        payload["action_name"] = decision.action_name
        payload["arguments"] = dict(decision.arguments)
    elif decision.decision_type == AgentDecisionType.FINAL:
        payload["final_answer"] = decision.final_answer
    elif decision.decision_type == AgentDecisionType.CLARIFICATION:
        payload["clarification_question"] = decision.clarification_question
    return json.dumps(payload)


class ScriptedGenerationStub(TextGenerationPort):
    """Deterministic in-memory double conforming to TextGenerationPort.

    Returns scripted decision sequences without probabilistic inference or external network dependencies.
    """

    def __init__(
        self,
        responses: Optional[Sequence[Union[str, AgentDecision]]] = None,
        canned_map: Optional[Mapping[str, Union[str, AgentDecision]]] = None,
    ) -> None:
        self.queue: List[str] = []
        if responses:
            for r in responses:
                if isinstance(r, AgentDecision):
                    self.queue.append(decision_to_json(r))
                else:
                    self.queue.append(str(r))

        self.canned_map: dict[str, str] = {}
        if canned_map:
            for k, v in canned_map.items():
                if isinstance(v, AgentDecision):
                    self.canned_map[k] = decision_to_json(v)
                else:
                    self.canned_map[k] = str(v)

        self.recorded_requests: List[CompletionRequest] = []

    def queue_decision(self, decision: Union[str, AgentDecision]) -> None:
        """Enqueue an additional decision."""
        if isinstance(decision, AgentDecision):
            self.queue.append(decision_to_json(decision))
        else:
            self.queue.append(str(decision))

    async def generate(
        self,
        request: CompletionRequest,
        context: Optional[AiOperationContext] = None,
    ) -> CompletionResponse:
        self.recorded_requests.append(request)

        # Check keyword map first
        for key, text in self.canned_map.items():
            if key in request.prompt:
                return CompletionResponse(
                    text=text,
                    model=request.model,
                    finish_reason=FinishReason.STOP,
                    usage=UsageMetrics(input_tokens=50, output_tokens=30, total_tokens=80),
                    latency_ms=0.5,
                )

        # Fall back to FIFO queue
        if self.queue:
            next_text = self.queue.pop(0)
            return CompletionResponse(
                text=next_text,
                model=request.model,
                finish_reason=FinishReason.STOP,
                usage=UsageMetrics(input_tokens=50, output_tokens=30, total_tokens=80),
                latency_ms=0.5,
            )

        # Default fallback response if queue is exhausted
        default_fallback = json.dumps({
            "type": "final",
            "final_answer": "Scripted generation queue exhausted; stopping execution.",
            "explanation": "No further canned decisions available.",
        })
        return CompletionResponse(
            text=default_fallback,
            model=request.model,
            finish_reason=FinishReason.STOP,
            usage=UsageMetrics(input_tokens=10, output_tokens=10, total_tokens=20),
            latency_ms=0.1,
        )
