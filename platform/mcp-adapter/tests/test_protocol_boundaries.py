"""Protocol error paths, stdio parsing and bounded initialization."""

import concurrent.futures
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "platform/mcp-adapter")]
from mcp_adapter.client import McpClient, McpClientError
from mcp_adapter.server import McpServer
from mcp_adapter.adapter import McpCapabilityAdapter
from contracts.agent import SideEffectLevel
from mcp_adapter.protocol import JsonRpcRequest, JsonRpcResponse, JsonRpcError


class TestProtocolBoundaries(unittest.TestCase):
    def test_nonfinite_request_deadlines_are_rejected(self):
        for value in (float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                McpClient(server_instance=McpServer(), request_timeout_seconds=value)

    def test_boolean_response_id_cannot_impersonate_numeric_request(self):
        source = 'import sys,json\nfor line in sys.stdin:\n request=json.loads(line); print(json.dumps({"jsonrpc":"2.0","id":True,"result":{}}),flush=True)'
        client = McpClient(command=[sys.executable, "-u", "-c", source], request_timeout_seconds=1)
        try:
            with self.assertRaises(McpClientError):
                client.initialize()
        finally:
            client.close()

    def test_wire_version_and_required_envelope_fields(self):
        for payload in (
            {"jsonrpc": "1.0"},
            {"jsonrpc": "2.0", "id": 1},
            {"jsonrpc": "2.0", "method": "tools/list"},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                JsonRpcRequest.from_dict(payload)
        for payload in ({"jsonrpc": "1.0"}, {"jsonrpc": "2.0"}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                JsonRpcResponse.from_dict(payload)
        self.assertEqual(
            JsonRpcError(-1, "error", {"retryable": False}).to_dict()["data"], {"retryable": False}
        )

    def test_server_malformed_missing_tool_and_failing_handler(self):
        server = McpServer()
        self.assertEqual(server.process_message(""), "")
        self.assertIn("error", json.loads(server.process_message("not-json")))
        self.assertIsNotNone(
            server.handle_request(JsonRpcRequest("tools/call", 1, {"name": 1})).error
        )
        McpClient(server_instance=server).initialize()
        server.register_tool("failure", "fails", {"type": "object"}, lambda _: 1 / 0)
        response = server.handle_request(JsonRpcRequest("tools/call", 1, {"name": "failure"}))
        self.assertTrue(response.result["isError"])
        with (
            patch("sys.stdin", io.StringIO('{"jsonrpc":"2.0","method":"tools/list","id":1}\n')),
            patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            server.run_stdio()
            self.assertEqual(json.loads(out.getvalue())["id"], 1)

    def test_stalled_initialize_has_deadline(self):
        client = McpClient(
            command=[sys.executable, "-c", "import sys,time; sys.stdin.readline(); time.sleep(10)"],
            request_timeout_seconds=0.05,
        )
        try:
            with self.assertRaises(McpClientError):
                client.initialize()
            self.assertIsNone(client._process)
        finally:
            client.close()

    def test_concurrent_stdio_responses_remain_correlated(self):
        client = McpClient(command=[sys.executable, "-m", "mcp_adapter.server"])
        try:
            client.initialize()
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(
                    pool.map(
                        lambda value: client.call_tool("ping", {"echo": value}), ["one", "two"]
                    )
                )
            self.assertEqual(
                [json.loads(result["content"][0]["text"])["echo"] for result in results],
                ["one", "two"],
            )
        finally:
            client.close()


class TestMcpResultBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_error_json_plain_text_and_discovery_failure(self):
        server = McpServer()
        server.register_tool("plain", "text", {}, lambda _: "plain text")
        server.register_tool("invalid", "text", {}, lambda _: "{invalid")
        server.register_tool("failure", "text", {}, lambda _: 1 / 0)
        client = McpClient(server_instance=server)
        for name in ("plain", "invalid", "failure"):
            adapter = McpCapabilityAdapter(
                client, name, allowlist=[name], side_effect_level=SideEffectLevel.READ_ONLY
            )
            result = await adapter.execute({})
            self.assertIn("error" if name == "failure" else "output", result)
        with self.assertRaises(ValueError):
            McpCapabilityAdapter(client, "missing", allowlist=["missing"])
        with self.assertRaises(ValueError):
            McpClient()
