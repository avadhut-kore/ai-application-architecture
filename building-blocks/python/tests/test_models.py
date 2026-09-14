"""Unit tests for core models and data structures."""

import unittest
from dataclasses import FrozenInstanceError

from contracts.models import (
    ChatMessage,
    CompletionRequest,
    CompletionResponse,
    FinishReason,
    Role,
    UsageMetrics,
)


class TestModels(unittest.TestCase):
    """Test suite verifying contract models behavior and immutability."""

    def test_chat_message_creation_and_immutability(self) -> None:
        msg = ChatMessage(role=Role.USER, content="Hello, AI!")
        self.assertEqual(msg.role, Role.USER)
        self.assertEqual(msg.content, "Hello, AI!")
        self.assertIsNone(msg.name)

        with self.assertRaises(FrozenInstanceError):
            msg.content = "New content"  # type: ignore[misc]

    def test_usage_metrics_calculation(self) -> None:
        # Automatic total_tokens calculation
        usage = UsageMetrics(input_tokens=10, output_tokens=25)
        self.assertEqual(usage.input_tokens, 10)
        self.assertEqual(usage.output_tokens, 25)
        self.assertEqual(usage.total_tokens, 35)

        # Explicit total_tokens accepted if >= sum
        explicit_usage = UsageMetrics(input_tokens=10, output_tokens=25, total_tokens=40)
        self.assertEqual(explicit_usage.total_tokens, 40)

        # Negative tokens rejected
        with self.assertRaises(ValueError):
            UsageMetrics(input_tokens=-1, output_tokens=10)
        with self.assertRaises(ValueError):
            UsageMetrics(input_tokens=10, output_tokens=-5)

        # Invalid total rejected if less than sum
        with self.assertRaises(ValueError):
            UsageMetrics(input_tokens=20, output_tokens=30, total_tokens=40)

    def test_completion_request_validation(self) -> None:
        # Valid request
        req = CompletionRequest(prompt="Summarize this text", model="llama3.2:latest")
        self.assertEqual(req.prompt, "Summarize this text")
        self.assertEqual(req.model, "llama3.2:latest")
        self.assertEqual(req.temperature, 0.7)
        self.assertIsNone(req.max_tokens)

        # Immutability
        with self.assertRaises(FrozenInstanceError):
            req.temperature = 0.5  # type: ignore[misc]

        # Missing both prompt and messages
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="", model="llama3.2:latest")

        # Missing model
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="Valid prompt", model="")

        # Temperature out of bounds
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="Valid prompt", model="llama3.2:latest", temperature=-0.1)
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="Valid prompt", model="llama3.2:latest", temperature=2.5)

        # Non-positive max tokens
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="Valid prompt", model="llama3.2:latest", max_tokens=0)
        with self.assertRaises(ValueError):
            CompletionRequest(prompt="Valid prompt", model="llama3.2:latest", max_tokens=-50)

    def test_completion_response_defaults(self) -> None:
        resp = CompletionResponse(text="Generated text", model="llama3.2:latest")
        self.assertEqual(resp.text, "Generated text")
        self.assertEqual(resp.model, "llama3.2:latest")
        self.assertEqual(resp.finish_reason, FinishReason.STOP)
        self.assertIsNone(resp.usage)
        self.assertIsNone(resp.latency_ms)

        with self.assertRaises(FrozenInstanceError):
            resp.text = "Tampered text"  # type: ignore[misc]


if __name__ == "__main__":
    unittest.main()
