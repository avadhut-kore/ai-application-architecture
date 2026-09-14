"""Core outbound capability ports for model interactions."""

from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from .models import CompletionRequest, CompletionResponse
from .telemetry import AiOperationContext


@runtime_checkable
class TextGenerationPort(Protocol):
    """Port for text generation operations against local or remote models.

    Defines the contract for model adapters (e.g. Ollama, OpenAI) without
    introducing dependencies on provider-specific client libraries.
    """

    async def generate(
        self,
        request: CompletionRequest,
        context: Optional[AiOperationContext] = None,
    ) -> CompletionResponse:
        """Execute text generation against the configured provider."""
        ...


# Canonical port aliases for semantic alignment across documentation
LlmClientPort = TextGenerationPort
ILlmClient = TextGenerationPort
