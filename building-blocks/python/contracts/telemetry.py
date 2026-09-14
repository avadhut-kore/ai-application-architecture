"""OpenTelemetry GenAI semantic conventions and operational context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


# Standard OpenTelemetry GenAI Semantic Convention attribute keys
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_REQUEST_MODEL = "gen_ai.request.model"
GEN_AI_REQUEST_MAX_TOKENS = "gen_ai.request.max_tokens"
GEN_AI_REQUEST_TEMPERATURE = "gen_ai.request.temperature"
GEN_AI_RESPONSE_FINISH_REASONS = "gen_ai.response.finish_reasons"
GEN_AI_USAGE_INPUT_TOKENS = "gen_ai.usage.input_tokens"
GEN_AI_USAGE_OUTPUT_TOKENS = "gen_ai.usage.output_tokens"
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"


@dataclass(frozen=True)
class AiOperationContext:
    """Correlation and tracing context for an AI invocation.

    Adheres to OpenTelemetry GenAI semantic conventions.
    """

    trace_id: str
    span_id: str
    operation_name: str
    system: str
    model: str
    attributes: Mapping[str, Any] = field(default_factory=dict)

    def to_otel_attributes(self) -> Dict[str, Any]:
        """Export context as OpenTelemetry GenAI standard attributes."""
        attrs: Dict[str, Any] = {
            GEN_AI_OPERATION_NAME: self.operation_name,
            GEN_AI_SYSTEM: self.system,
            GEN_AI_REQUEST_MODEL: self.model,
        }
        for k, v in self.attributes.items():
            attrs[f"gen_ai.{k}" if not k.startswith("gen_ai.") else k] = v
        return attrs
