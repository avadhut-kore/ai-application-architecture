"""Unit tests for Model Context Protocol (MCP) JSON-RPC 2.0 adapter and stdio server."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
MCP_ADAPTER_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, MCP_ADAPTER_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import CapabilityPort, SideEffectLevel
from mcp_adapter.adapter import McpCapabilityAdapter, create_mcp_capabilities
from mcp_adapter.client import McpClient, McpClientError
from mcp_adapter.protocol import (
    JsonRpcError,
    JsonRpcErrorCode,
    JsonRpcRequest,
    JsonRpcResponse,
)
from mcp_adapter.server import McpServer


class TestMcpProtocol(unittest.TestCase):
    """Test suite verifying JSON-RPC 2.0 wire protocol handling."""

    def test_json_rpc_request_serialization(self) -> None:
        req = JsonRpcRequest(method="tools/list", id=1, params={"test": "val"})
        d = req.to_dict()
        self.assertEqual(d["jsonrpc"], "2.0")
        self.assertEqual(d["id"], 1)
        self.assertEqual(d["method"], "tools/list")
        self.assertEqual(d["params"], {"test": "val"})

        # Deserialize
        req_parsed = JsonRpcRequest.from_dict(d)
        self.assertEqual(req_parsed.method, "tools/list")
        self.assertEqual(req_parsed.id, 1)

    def test_json_rpc_response_success_and_error(self) -> None:
        # Success response
        res = JsonRpcResponse(id=1, result={"status": "ok"})
        d = res.to_dict()
        self.assertEqual(d["result"], {"status": "ok"})
        self.assertNotIn("error", d)

        # Error response
        err_res = JsonRpcResponse(
            id=2,
            error=JsonRpcError(code=JsonRpcErrorCode.METHOD_NOT_FOUND, message="Not found"),
        )
        d_err = err_res.to_dict()
        self.assertEqual(d_err["error"]["code"], -32601)
        self.assertEqual(d_err["error"]["message"], "Not found")


class TestMcpServerAndClient(unittest.TestCase):
    """Test suite verifying McpServer and McpClient in-memory dispatch."""

    def setUp(self) -> None:
        self.server = McpServer(server_name="test-server", version="0.9.0")
        self.client = McpClient(server_instance=self.server)

    def test_initialize_handshake(self) -> None:
        init_res = self.client.initialize()
        self.assertEqual(init_res.get("protocolVersion"), "2024-11-05")
        self.assertEqual(init_res["serverInfo"]["name"], "test-server")

    def test_list_tools(self) -> None:
        tools = self.client.list_tools()
        names = [t["name"] for t in tools]
        self.assertIn("get_system_status", names)
        self.assertIn("ping", names)

    def test_call_tool_ping(self) -> None:
        call_res = self.client.call_tool("ping", {"echo": "hello-mcp"})
        self.assertFalse(call_res.get("isError"))
        content = call_res.get("content", [])
        self.assertEqual(len(content), 1)
        self.assertIn("hello-mcp", content[0]["text"])

    def test_call_unknown_tool_raises_error(self) -> None:
        with self.assertRaises(McpClientError) as ctx:
            self.client.call_tool("unregistered_tool", {})
        self.assertIn("Tool 'unregistered_tool' is not registered", str(ctx.exception))


class TestMcpCapabilityAdapter(unittest.TestCase):
    """Test suite verifying McpCapabilityAdapter conformance and security boundaries."""

    def setUp(self) -> None:
        self.server = McpServer()
        self.client = McpClient(server_instance=self.server)

    def test_adapter_satisfies_capability_port(self) -> None:
        adapter = McpCapabilityAdapter(
            client=self.client,
            tool_name="get_system_status",
            allowlist=["get_system_status"],
        )
        self.assertIsInstance(adapter, CapabilityPort)
        self.assertEqual(adapter.metadata.name, "get_system_status")
        self.assertEqual(adapter.metadata.side_effect_level, SideEffectLevel.READ_ONLY)
        self.assertFalse(adapter.metadata.requires_approval)

    def test_allowlist_enforcement_blocks_unauthorized_tool(self) -> None:
        # 'ping' is available on server, but not in allowlist
        with self.assertRaises(ValueError) as ctx:
            McpCapabilityAdapter(
                client=self.client,
                tool_name="ping",
                allowlist=["get_system_status"],
            )
        self.assertIn("is not present in permitted allowlist", str(ctx.exception))

    def test_adapter_async_execution(self) -> None:
        adapter = McpCapabilityAdapter(
            client=self.client,
            tool_name="get_system_status",
            allowlist=["get_system_status"],
        )
        result = asyncio.run(adapter.execute({}))
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "operational")
        self.assertTrue(result.get("metrics", {}).get("subsystem_healthy"))

    def test_factory_creates_filtered_capabilities(self) -> None:
        # Server has get_system_status and ping. We allow only get_system_status.
        capabilities = create_mcp_capabilities(
            client=self.client,
            allowlist=["get_system_status"],
        )
        self.assertEqual(len(capabilities), 1)
        self.assertEqual(capabilities[0].metadata.name, "get_system_status")


class TestMcpSubprocessTransport(unittest.TestCase):
    """Test suite verifying real subprocess stdio communication loop."""

    def test_subprocess_stdio_roundtrip(self) -> None:
        # Launch server as subprocess using current python interpreter
        cmd = [sys.executable, "-m", "mcp_adapter.server"]
        client = McpClient(command=cmd)
        try:
            init_res = client.initialize()
            self.assertEqual(init_res.get("protocolVersion"), "2024-11-05")

            tools = client.list_tools()
            self.assertGreaterEqual(len(tools), 2)

            res = client.call_tool("ping", {"echo": "subprocess-test"})
            self.assertIn("subprocess-test", res["content"][0]["text"])
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
