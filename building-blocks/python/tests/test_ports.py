"""Unit tests for capability ports using hermetic test doubles."""

from __future__ import annotations

import asyncio
import unittest
from typing import List, Optional

from contracts.models import (
    CompletionRequest,
    CompletionResponse,
    FinishReason,
    UsageMetrics,
)
from contracts.ports import ILlmClient, LlmClientPort, TextGenerationPort
from contracts.telemetry import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_REQUEST_MODEL,
    GEN_AI_SYSTEM,
    AiOperationContext,
)


class FakeLlmClient:
    """Deterministic in-memory test double conforming to TextGenerationPort.

    Used strictly for unit testing application logic without live models.
    """

    def __init__(
        self,
        canned_responses: Optional[List[str]] = None,
        default_response: str = "Fake model response",
    ) -> None:
        self._canned_responses = list(canned_responses) if canned_responses else []
        self._default_response = default_response
        self.recorded_requests: List[CompletionRequest] = []
        self.recorded_contexts: List[Optional[AiOperationContext]] = []

    async def generate(
        self,
        request: CompletionRequest,
        context: Optional[AiOperationContext] = None,
    ) -> CompletionResponse:
        self.recorded_requests.append(request)
        self.recorded_contexts.append(context)

        text = (
            self._canned_responses.pop(0)
            if self._canned_responses
            else self._default_response
        )

        return CompletionResponse(
            text=text,
            model=request.model,
            finish_reason=FinishReason.STOP,
            usage=UsageMetrics(input_tokens=15, output_tokens=30, total_tokens=45),
            latency_ms=1.5,
        )


class TestPorts(unittest.TestCase):
    """Test suite verifying capability port protocol adherence."""

    def test_fake_client_satisfies_protocol(self) -> None:
        fake = FakeLlmClient()
        self.assertIsInstance(fake, TextGenerationPort)
        self.assertIsInstance(fake, LlmClientPort)
        self.assertIsInstance(fake, ILlmClient)

    def test_non_conforming_object_fails_protocol(self) -> None:
        class IncompatibleObject:
            pass

        self.assertNotIsInstance(IncompatibleObject(), TextGenerationPort)

    def test_generate_execution(self) -> None:
        fake = FakeLlmClient(canned_responses=["Step 1 output", "Step 2 output"])
        req1 = CompletionRequest(prompt="First step", model="test-model")
        ctx = AiOperationContext(
            trace_id="0123456789abcdef0123456789abcdef",
            span_id="0123456789abcdef",
            operation_name="chat",
            system="in-memory-test",
            model="test-model",
            attributes={"environment": "test"},
        )

        # Run async call hermetically
        resp1 = asyncio.run(fake.generate(req1, ctx))
        self.assertEqual(resp1.text, "Step 1 output")
        self.assertEqual(resp1.model, "test-model")
        self.assertIsNotNone(resp1.usage)
        self.assertEqual(resp1.usage.total_tokens, 45)  # type: ignore[union-attr]

        # Verify recorded context
        self.assertEqual(len(fake.recorded_requests), 1)
        self.assertEqual(len(fake.recorded_contexts), 1)
        otel_attrs = ctx.to_otel_attributes()
        self.assertEqual(otel_attrs[GEN_AI_OPERATION_NAME], "chat")
        self.assertEqual(otel_attrs[GEN_AI_SYSTEM], "in-memory-test")
        self.assertEqual(otel_attrs[GEN_AI_REQUEST_MODEL], "test-model")
        self.assertEqual(otel_attrs["gen_ai.environment"], "test")

        # Second call returns next canned response
        req2 = CompletionRequest(prompt="Second step", model="test-model")
        resp2 = asyncio.run(fake.generate(req2))
        self.assertEqual(resp2.text, "Step 2 output")

        # Third call falls back to default response
        req3 = CompletionRequest(prompt="Third step", model="test-model")
        resp3 = asyncio.run(fake.generate(req3))
        self.assertEqual(resp3.text, "Fake model response")


if __name__ == "__main__":
    unittest.main()
