"""Verify actual exported spans and sensitive-content exclusion."""

import sys
import os
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
for directory in (
    ROOT / "platform/ollama-adapter",
    ROOT / "platform/ollama-embedding-adapter",
    ROOT / "platform/mcp-adapter",
):
    sys.path.insert(0, str(directory))

from contracts.models import CompletionRequest, EmbeddingRequest
from ollama_adapter.adapter import OllamaAdapter
from ollama_embedding_adapter.adapter import OllamaEmbeddingAdapter
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


class TestTelemetry(unittest.IsolatedAsyncioTestCase):
    async def test_workflow_correlation_hash_does_not_export_raw_identifier(self):
        import hashlib
        from ai_telemetry import traced

        @traced("workflow.start", "test")
        async def operation(*, workflow_id):
            return "done"

        await operation(workflow_id="PRIVATE IDENTIFIER")
        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(
            span.attributes["workflow.id_sha256"], hashlib.sha256(b"PRIVATE IDENTIFIER").hexdigest()
        )
        self.assertNotIn("PRIVATE IDENTIFIER", span.to_json())

    def test_local_exporter_bootstrap_writes_metadata_only_json(self):
        from ai_telemetry import configure_local_tracing

        with patch.dict(os.environ, {}, clear=True):
            configure_local_tracing()
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "trace.jsonl"
            with patch.dict(os.environ, {"AI_TRACE_FILE": str(destination)}):
                configure_local_tracing()
            self.assertFalse(destination.exists())
            env = dict(
                os.environ,
                AI_TRACE_FILE=str(destination),
                PYTHONPATH=str(ROOT / "building-blocks/python"),
            )
            code = 'import asyncio\nfrom ai_telemetry import traced,configure_local_tracing\nconfigure_local_tracing()\n@traced("operation", "test")\nasync def operation():\n return "PRIVATE"\nasyncio.run(operation())'
            result = subprocess.run(
                [sys.executable, "-c", code], env=env, capture_output=True, text=True
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            span = json.loads(destination.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(span["name"], "operation")
            self.assertNotIn("PRIVATE", json.dumps(span))

    async def test_mcp_error_payload_and_embedding_fallback_are_observable(self):
        from mcp_adapter.server import McpServer
        from mcp_adapter.client import McpClient
        from mcp_adapter.adapter import McpCapabilityAdapter
        from contracts.agent import SideEffectLevel
        from contracts.errors import AiError

        server = McpServer()
        server.register_tool("failure", "fails", {}, lambda _: 1 / 0)
        client = McpClient(server_instance=server)
        result = await McpCapabilityAdapter(
            client, "failure", allowlist=["failure"], side_effect_level=SideEffectLevel.READ_ONLY
        ).execute({})
        self.assertTrue(result["error"])
        self.assertEqual(self.exporter.get_finished_spans()[0].status.status_code.name, "ERROR")
        self.exporter.clear()
        adapter = OllamaEmbeddingAdapter(max_retries=0)
        with (
            patch.object(
                adapter,
                "_execute_embed_api",
                side_effect=AiError("missing endpoint", details={"http_status": 404}),
            ),
            patch.object(adapter, "_execute_legacy_embeddings_api", return_value=[0.1, 0.2]),
        ):
            await adapter.embed(EmbeddingRequest(["document"], "embedding"))
        self.assertTrue(self.exporter.get_finished_spans()[0].attributes["gen_ai.fallback_used"])

    async def test_failed_receipt_sets_error_without_exporting_payload(self):
        from ai_telemetry import traced
        from contracts.agent import ExecutionReceipt

        @traced("tool.execute", "test")
        async def operation():
            return ExecutionReceipt("action", "tool", "ambiguous", error_message="PRIVATE"), {
                "secret": "PRIVATE"
            }

        await operation()
        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(span.status.status_code.name, "ERROR")
        self.assertNotIn("PRIVATE", span.to_json())

    @classmethod
    def setUpClass(cls):
        cls.exporter = InMemorySpanExporter()
        cls.provider = TracerProvider()
        cls.provider.add_span_processor(SimpleSpanProcessor(cls.exporter))
        trace.set_tracer_provider(cls.provider)

    def setUp(self):
        self.exporter.clear()

    async def test_generation_export_has_model_usage_duration_and_parent(self):
        adapter = OllamaAdapter(max_retries=0)
        with trace.get_tracer("test").start_as_current_span("request") as parent:
            with patch.object(
                adapter,
                "_send_http_request",
                return_value={
                    "model": "local-model",
                    "response": "PRIVATE RESPONSE",
                    "prompt_eval_count": 10,
                    "eval_count": 2,
                },
            ):
                await adapter.generate(CompletionRequest("PRIVATE PROMPT", "local-model"))
        spans = self.exporter.get_finished_spans()
        span = next(s for s in spans if s.name == "gen_ai.generate")
        self.assertEqual(span.parent.span_id, parent.get_span_context().span_id)
        self.assertEqual(span.attributes["gen_ai.system"], "ollama")
        self.assertEqual(span.attributes["gen_ai.request.model"], "local-model")
        self.assertEqual(span.attributes["gen_ai.response.model"], "local-model")
        self.assertEqual(span.attributes["gen_ai.usage.input_tokens"], 10)
        self.assertEqual(span.attributes["gen_ai.usage.output_tokens"], 2)
        self.assertGreater(span.end_time, span.start_time)
        self.assertNotIn("PRIVATE", span.to_json())

    async def test_embedding_export_and_error_redaction(self):
        adapter = OllamaEmbeddingAdapter(max_retries=0)
        with patch.object(
            adapter,
            "_execute_embed_api",
            return_value={"embeddings": [[0.1, 0.2]], "prompt_eval_count": 3},
        ):
            await adapter.embed(EmbeddingRequest(["PRIVATE DOCUMENT"], "embedding"))
        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(span.name, "gen_ai.embed")
        self.assertEqual(span.attributes["gen_ai.response.model"], "embedding")
        self.exporter.clear()
        with patch.object(adapter, "_execute_embed_api", side_effect=ValueError("PRIVATE ERROR")):
            with self.assertRaises(ValueError):
                await adapter.embed(EmbeddingRequest(["PRIVATE DOCUMENT"], "embedding"))
        span = self.exporter.get_finished_spans()[0]
        self.assertEqual(span.status.status_code.name, "ERROR")
        self.assertNotIn("PRIVATE", span.to_json())
