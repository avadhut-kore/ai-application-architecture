"""Hermetic unit tests for OllamaAdapter."""

from __future__ import annotations

import asyncio
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure paths
SCRIPT_DIR = Path(__file__).resolve().parent
COMPONENT_DIR = SCRIPT_DIR.parent
REPO_ROOT = COMPONENT_DIR.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"

if str(BUILDING_BLOCKS_DIR) not in sys.path:
    sys.path.insert(0, str(BUILDING_BLOCKS_DIR))
if str(COMPONENT_DIR) not in sys.path:
    sys.path.insert(0, str(COMPONENT_DIR))

from contracts.errors import (
    AiInvalidRequestError,
    AiModelNotFoundError,
    AiProviderUnavailableError,
    AiRateLimitError,
    AiTimeoutError,
)
from contracts.models import (
    ChatMessage,
    CompletionRequest,
    FinishReason,
    Role,
)
from contracts.ports import TextGenerationPort
from ollama_adapter.adapter import OllamaAdapter


class TestOllamaAdapter(unittest.TestCase):
    """Test suite verifying OllamaAdapter behavior, payload mapping, and error resilience."""

    def setUp(self) -> None:
        self.adapter = OllamaAdapter(
            endpoint="http://mock-ollama:11434",
            default_model="llama3.2",
            timeout_seconds=5.0,
            max_retries=2,
            backoff_base_seconds=0.01,  # Fast backoff for tests
        )

    def test_satisfies_text_generation_port_protocol(self) -> None:
        """Verify that OllamaAdapter conforms to the runtime checkable TextGenerationPort."""
        self.assertIsInstance(self.adapter, TextGenerationPort)

    def test_build_payload_prompt_mode(self) -> None:
        """Verify request mapping for single-prompt completion."""
        request = CompletionRequest(
            prompt="Translate hello to French",
            model="llama3.2",
            system_prompt="You are a translator.",
            temperature=0.2,
            max_tokens=50,
            stop_sequences=["\n\n"],
            metadata={"format": "json"},
        )
        payload = self.adapter._build_payload(request)

        self.assertEqual(payload["model"], "llama3.2")
        self.assertEqual(payload["prompt"], "Translate hello to French")
        self.assertEqual(payload["system"], "You are a translator.")
        self.assertFalse(payload["stream"])
        self.assertEqual(payload["format"], "json")
        self.assertEqual(payload["options"]["temperature"], 0.2)
        self.assertEqual(payload["options"]["num_predict"], 50)
        self.assertEqual(payload["options"]["stop"], ["\n\n"])

    def test_build_payload_chat_mode(self) -> None:
        """Verify request mapping for conversational multi-turn messages."""
        request = CompletionRequest(
            prompt="fallback prompt",
            model="qwen",
            messages=[
                ChatMessage(role=Role.SYSTEM, content="System instructions"),
                ChatMessage(role=Role.USER, content="User question"),
            ],
            temperature=0.5,
        )
        payload = self.adapter._build_payload(request)

        self.assertEqual(payload["model"], "qwen")
        self.assertNotIn("prompt", payload)
        self.assertEqual(len(payload["messages"]), 2)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["content"], "User question")

    def test_successful_generate_mapping(self) -> None:
        """Verify successful response parsing and usage extraction."""
        raw_ollama_response = {
            "model": "llama3.2",
            "created_at": "2026-09-14T10:00:00Z",
            "response": "Bonjour",
            "done": True,
            "done_reason": "stop",
            "total_duration": 450_000_000,  # 450ms
            "prompt_eval_count": 15,
            "eval_count": 5,
        }

        with patch.object(self.adapter, "_send_http_request", return_value=raw_ollama_response):
            request = CompletionRequest(prompt="Hello", model="llama3.2")
            response = asyncio.run(self.adapter.generate(request))

            self.assertEqual(response.text, "Bonjour")
            self.assertEqual(response.model, "llama3.2")
            self.assertEqual(response.finish_reason, FinishReason.STOP)
            self.assertIsNotNone(response.usage)
            self.assertEqual(response.usage.input_tokens, 15)
            self.assertEqual(response.usage.output_tokens, 5)
            self.assertEqual(response.usage.total_tokens, 20)
            self.assertAlmostEqual(response.latency_ms, 450.0)

    def test_model_not_found_error_mapping(self) -> None:
        """Verify HTTP 404 maps to non-transient AiModelNotFoundError without retry."""
        http_err = urllib.error.HTTPError(
            url="http://mock-ollama:11434/api/generate",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"error":"model \'unknown-model\' not found"}'),
        )

        with patch("urllib.request.urlopen", side_effect=http_err) as mock_url:
            request = CompletionRequest(prompt="Hello", model="unknown-model")
            with self.assertRaises(AiModelNotFoundError) as ctx:
                asyncio.run(self.adapter.generate(request))

            self.assertEqual(ctx.exception.model_name, "unknown-model")
            self.assertFalse(ctx.exception.is_transient)
            # Fatal error must fail immediately (exactly 1 call)
            self.assertEqual(mock_url.call_count, 1)

    def test_invalid_request_error_mapping(self) -> None:
        """Verify HTTP 400 maps to non-transient AiInvalidRequestError."""
        http_err = urllib.error.HTTPError(
            url="http://mock-ollama:11434/api/generate",
            code=400,
            msg="Bad Request",
            hdrs={},
            fp=io.BytesIO(b'{"error":"malformed options"}'),
        )

        with patch("urllib.request.urlopen", side_effect=http_err):
            request = CompletionRequest(prompt="Hello", model="llama3.2")
            with self.assertRaises(AiInvalidRequestError) as ctx:
                asyncio.run(self.adapter.generate(request))

            self.assertFalse(ctx.exception.is_transient)

    def test_rate_limit_error_mapping(self) -> None:
        """Verify HTTP 429 maps to transient AiRateLimitError."""
        http_err = urllib.error.HTTPError(
            url="http://mock-ollama:11434/api/generate",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=io.BytesIO(b'{"error":"rate limit"}'),
        )

        with patch("urllib.request.urlopen", side_effect=http_err):
            request = CompletionRequest(prompt="Hello", model="llama3.2")
            with self.assertRaises(AiRateLimitError) as ctx:
                asyncio.run(self.adapter.generate(request))

            self.assertTrue(ctx.exception.is_transient)

    def test_transient_retry_success(self) -> None:
        """Verify that a transient 503 error is retried and succeeds on subsequent attempt."""
        server_err = urllib.error.HTTPError(
            url="http://mock-ollama:11434/api/generate",
            code=503,
            msg="Service Unavailable",
            hdrs={},
            fp=io.BytesIO(b"busy"),
        )
        success_response = {
            "model": "llama3.2",
            "response": "Recovered answer",
            "done": True,
            "total_duration": 100_000_000,
        }

        call_count = 0

        def side_effect(path, payload):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise AiProviderUnavailableError("Server busy", details={"status": 503})
            return success_response

        with patch.object(self.adapter, "_send_http_request", side_effect=side_effect):
            request = CompletionRequest(prompt="Hello", model="llama3.2")
            response = asyncio.run(self.adapter.generate(request))

            self.assertEqual(call_count, 2)
            self.assertEqual(response.text, "Recovered answer")

    def test_transient_retry_exhaustion(self) -> None:
        """Verify that persistent transient errors fail after max_retries."""
        call_count = 0

        def side_effect(path, payload):
            nonlocal call_count
            call_count += 1
            raise AiProviderUnavailableError("Persistent down")

        with patch.object(self.adapter, "_send_http_request", side_effect=side_effect):
            request = CompletionRequest(prompt="Hello", model="llama3.2")
            with self.assertRaises(AiProviderUnavailableError):
                asyncio.run(self.adapter.generate(request))

            # Initial call + 2 retries = 3 calls
            self.assertEqual(call_count, 3)

    def test_check_health(self) -> None:
        """Verify check_health returns True on success and False on connection error."""
        with patch.object(self.adapter, "_send_http_request", return_value={"models": []}):
            healthy = asyncio.run(self.adapter.check_health())
            self.assertTrue(healthy)

        with patch.object(self.adapter, "_send_http_request", side_effect=urllib.error.URLError("Refused")):
            healthy = asyncio.run(self.adapter.check_health())
            self.assertFalse(healthy)

    def test_get_installed_models(self) -> None:
        """Verify get_installed_models extracts list of names."""
        mock_tags = {
            "models": [
                {"name": "llama3.2:latest"},
                {"name": "qwen2.5:7b"},
            ]
        }
        with patch.object(self.adapter, "_send_http_request", return_value=mock_tags):
            models = asyncio.run(self.adapter.get_installed_models())
            self.assertEqual(models, ["llama3.2:latest", "qwen2.5:7b"])


if __name__ == "__main__":
    unittest.main()
