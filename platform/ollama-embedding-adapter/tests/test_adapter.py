"""Unit tests for OllamaEmbeddingAdapter using hermetic urllib mocking."""

from __future__ import annotations

import asyncio
import io
import json
import socket
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
ADAPTER_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, ADAPTER_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.errors import (
    AiInvalidRequestError,
    AiModelNotFoundError,
    AiProviderUnavailableError,
    AiRateLimitError,
    AiTimeoutError,
)
from contracts.models import EmbeddingRequest
from contracts.ports import EmbeddingPort
from contracts.telemetry import AiOperationContext
from ollama_embedding_adapter.adapter import OllamaEmbeddingAdapter


class TestOllamaEmbeddingAdapter(unittest.TestCase):
    """Hermetic unit tests verifying OllamaEmbeddingAdapter functionality and error handling."""

    def setUp(self) -> None:
        self.adapter = OllamaEmbeddingAdapter(
            endpoint="http://localhost:11434",
            default_model="nomic-embed-text",
            timeout_seconds=5.0,
            max_retries=1,
            backoff_base_seconds=0.01,
        )

    def test_satisfies_embedding_port_protocol(self) -> None:
        self.assertIsInstance(self.adapter, EmbeddingPort)

    def _create_mock_response(self, status: int, data: dict) -> MagicMock:
        body = json.dumps(data).encode("utf-8")
        mock = MagicMock()
        mock.read.return_value = body
        mock.__enter__.return_value = mock
        mock.__exit__.return_value = None
        mock.status = status
        return mock

    @patch("urllib.request.urlopen")
    def test_embed_batch_success(self, mock_urlopen: MagicMock) -> None:
        mock_data = {
            "model": "nomic-embed-text",
            "embeddings": [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
            "total_duration": 15000000,
            "prompt_eval_count": 8,
        }
        mock_urlopen.return_value = self._create_mock_response(200, mock_data)

        req = EmbeddingRequest(inputs=["hello world", "test retrieval"], model="nomic-embed-text")
        resp = asyncio.run(self.adapter.embed(req))

        self.assertEqual(resp.model, "nomic-embed-text")
        self.assertEqual(resp.dimensions, 3)
        self.assertEqual(len(resp.embeddings), 2)
        self.assertEqual(resp.embeddings[0], [0.1, 0.2, 0.3])
        self.assertEqual(resp.embeddings[1], [0.4, 0.5, 0.6])
        self.assertEqual(resp.latency_ms, 15.0)
        self.assertIsNotNone(resp.usage)
        self.assertEqual(resp.usage.input_tokens, 8)  # type: ignore[union-attr]

    @patch("urllib.request.urlopen")
    def test_embed_with_telemetry_context(self, mock_urlopen: MagicMock) -> None:
        mock_data = {
            "model": "nomic-embed-text",
            "embeddings": [[0.5, -0.5]],
            "total_duration": 5000000,
        }
        mock_urlopen.return_value = self._create_mock_response(200, mock_data)

        ctx = AiOperationContext(
            trace_id="4bf92f3577b34da6a3ce929d0e0e4736",
            span_id="00f067aa0ba902b7",
            operation_name="embed",
            system="ollama",
            model="nomic-embed-text",
        )
        req = EmbeddingRequest(inputs=["single vector text"], model="nomic-embed-text")
        resp = asyncio.run(self.adapter.embed(req, ctx))

        self.assertIsNotNone(resp.metadata)
        self.assertEqual(resp.metadata["trace_id"], "4bf92f3577b34da6a3ce929d0e0e4736")  # type: ignore[index]
        self.assertEqual(resp.metadata["operation_name"], "embed")  # type: ignore[index]

    @patch("urllib.request.urlopen")
    def test_embed_empty_vectors_raises_error(self, mock_urlopen: MagicMock) -> None:
        mock_data = {"model": "nomic-embed-text", "embeddings": []}
        mock_urlopen.return_value = self._create_mock_response(200, mock_data)

        req = EmbeddingRequest(inputs=["text"], model="nomic-embed-text")
        with self.assertRaises(AiInvalidRequestError):
            asyncio.run(self.adapter.embed(req))

    @patch("urllib.request.urlopen")
    def test_fallback_to_legacy_embeddings_api(self, mock_urlopen: MagicMock) -> None:
        # First call to /api/embed raises 404 (endpoint not supported on older Ollama)
        http_404 = urllib.error.HTTPError(
            url="http://localhost:11434/api/embed",
            code=404,
            msg="Not Found",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b'{"error": "not found"}'),
        )
        # Second call to /api/embeddings succeeds with legacy response format
        mock_legacy = self._create_mock_response(200, {"embedding": [0.7, 0.8, 0.9]})
        mock_urlopen.side_effect = [http_404, mock_legacy]

        req = EmbeddingRequest(inputs=["fallback text"], model="nomic-embed-text")
        resp = asyncio.run(self.adapter.embed(req))

        self.assertEqual(resp.dimensions, 3)
        self.assertEqual(resp.embeddings[0], [0.7, 0.8, 0.9])

    @patch("urllib.request.urlopen")
    def test_model_not_found_error(self, mock_urlopen: MagicMock) -> None:
        http_404 = urllib.error.HTTPError(
            url="http://localhost:11434/api/embed",
            code=404,
            msg="Not Found",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b'{"error": "model \'missing-model\' not found"}'),
        )
        mock_urlopen.side_effect = http_404

        req = EmbeddingRequest(inputs=["text"], model="missing-model")
        with self.assertRaises(AiModelNotFoundError):
            asyncio.run(self.adapter.embed(req))

    @patch("urllib.request.urlopen")
    def test_rate_limit_retry_and_success(self, mock_urlopen: MagicMock) -> None:
        http_429 = urllib.error.HTTPError(
            url="http://localhost:11434/api/embed",
            code=429,
            msg="Too Many Requests",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b'{"error": "rate limit"}'),
        )
        mock_success = self._create_mock_response(
            200, {"model": "nomic-embed-text", "embeddings": [[0.1, 0.2]]}
        )
        mock_urlopen.side_effect = [http_429, mock_success]

        req = EmbeddingRequest(inputs=["text"], model="nomic-embed-text")
        resp = asyncio.run(self.adapter.embed(req))
        self.assertEqual(resp.dimensions, 2)
        self.assertEqual(mock_urlopen.call_count, 2)

    @patch("urllib.request.urlopen")
    def test_provider_unavailable_server_error(self, mock_urlopen: MagicMock) -> None:
        http_503 = urllib.error.HTTPError(
            url="http://localhost:11434/api/embed",
            code=503,
            msg="Service Unavailable",
            hdrs={},  # type: ignore[arg-type]
            fp=io.BytesIO(b'{"error": "service unavailable"}'),
        )
        mock_urlopen.side_effect = http_503

        req = EmbeddingRequest(inputs=["text"], model="nomic-embed-text")
        with self.assertRaises(AiProviderUnavailableError):
            asyncio.run(self.adapter.embed(req))

    @patch("urllib.request.urlopen")
    def test_timeout_error_handling(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = socket.timeout("timed out")

        req = EmbeddingRequest(inputs=["text"], model="nomic-embed-text")
        with self.assertRaises(AiTimeoutError):
            asyncio.run(self.adapter.embed(req))

    @patch("urllib.request.urlopen")
    def test_check_health(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = self._create_mock_response(200, {"status": "ok"})
        self.assertTrue(asyncio.run(self.adapter.check_health()))

        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")
        self.assertFalse(asyncio.run(self.adapter.check_health()))

    @patch("urllib.request.urlopen")
    def test_get_installed_models(self, mock_urlopen: MagicMock) -> None:
        mock_data = {
            "models": [
                {"name": "nomic-embed-text:latest"},
                {"name": "llama3.2:3b"},
            ]
        }
        mock_urlopen.return_value = self._create_mock_response(200, mock_data)
        models = asyncio.run(self.adapter.get_installed_models())
        self.assertEqual(models, ["nomic-embed-text:latest", "llama3.2:3b"])


if __name__ == "__main__":
    unittest.main()
