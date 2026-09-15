"""Hermetic unit tests for ToolExecutor idempotency, error sandboxing, and receipts."""

from __future__ import annotations

import asyncio
import sys
import unittest
from pathlib import Path
from typing import Any, Mapping, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import (
    CapabilityMetadata,
    CapabilityPort,
    SideEffectLevel,
)
from contracts.telemetry import AiOperationContext
from agent.executor import ToolExecutor


class DummyTool(CapabilityPort):
    """Simple test capability tracking call counts."""

    def __init__(
        self,
        name: str = "dummy_tool",
        side_effect_level: SideEffectLevel = SideEffectLevel.READ_ONLY,
        delay: float = 0.0,
        should_fail: bool = False,
    ) -> None:
        self._metadata = CapabilityMetadata(
            name=name,
            description="Test capability",
            input_schema={},
            side_effect_level=side_effect_level,
        )
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(self, arguments: Mapping[str, Any], context: Optional[AiOperationContext] = None) -> Any:
        self.call_count += 1
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        if self.should_fail:
            raise RuntimeError("Underlying capability crashed")
        return {"result": f"Executed with {dict(arguments)}", "call_count": self.call_count}


class TestToolExecutor(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.executor = ToolExecutor(timeout_seconds=0.5)

    async def test_read_only_tool_execution(self) -> None:
        tool = DummyTool(name="read_tool", side_effect_level=SideEffectLevel.READ_ONLY)
        receipt, result = await self.executor.execute_tool(
            capability=tool,
            arguments={"query": "test"},
            action_id="act-read-1",
        )
        self.assertEqual(receipt.status, "succeeded")
        self.assertEqual(receipt.capability_name, "read_tool")
        self.assertEqual(receipt.action_id, "act-read-1")
        self.assertIsNone(receipt.error_message)
        self.assertEqual(result["call_count"], 1)
        self.assertEqual(len(self.executor.execution_history), 1)

    async def test_state_mutating_idempotency_cache(self) -> None:
        tool = DummyTool(name="mutating_tool", side_effect_level=SideEffectLevel.STATE_MUTATING)

        # First execution
        receipt1, result1 = await self.executor.execute_tool(
            capability=tool,
            arguments={"account_id": "acc-1", "amount": 10},
            action_id="act-mut-1",
        )
        self.assertEqual(receipt1.status, "succeeded")
        self.assertEqual(tool.call_count, 1)

        # Replay execution with SAME action_id
        receipt2, result2 = await self.executor.execute_tool(
            capability=tool,
            arguments={"account_id": "acc-1", "amount": 10},
            action_id="act-mut-1",
        )
        # Verify tool was NOT called a second time
        self.assertEqual(tool.call_count, 1)
        self.assertEqual(receipt2.action_id, "act-mut-1")
        self.assertTrue(result2.get("idempotent_replay"))
        self.assertEqual(result2["cached_result"], result1)

    async def test_different_action_id_executes_again(self) -> None:
        tool = DummyTool(name="mutating_tool", side_effect_level=SideEffectLevel.STATE_MUTATING)

        # First execution
        await self.executor.execute_tool(
            capability=tool,
            arguments={"amount": 10},
            action_id="act-mut-A",
        )
        self.assertEqual(tool.call_count, 1)

        # Second execution with DIFFERENT action_id
        await self.executor.execute_tool(
            capability=tool,
            arguments={"amount": 10},
            action_id="act-mut-B",
        )
        self.assertEqual(tool.call_count, 2)

    async def test_tool_exception_sandboxing(self) -> None:
        failing_tool = DummyTool(name="bad_tool", should_fail=True)
        receipt, result = await self.executor.execute_tool(
            capability=failing_tool,
            arguments={},
            action_id="act-fail-1",
        )
        self.assertEqual(receipt.status, "failed")
        self.assertIn("Underlying capability crashed", receipt.error_message or "")
        self.assertTrue(result.get("error"))
        self.assertIn("Tool execution failed", result.get("message", ""))

    async def test_tool_timeout_handling(self) -> None:
        slow_tool = DummyTool(name="slow_tool", delay=1.0)
        # Executor timeout is 0.2s
        executor = ToolExecutor(timeout_seconds=0.2)
        receipt, result = await executor.execute_tool(
            capability=slow_tool,
            arguments={},
            action_id="act-timeout-1",
        )
        self.assertEqual(receipt.status, "failed")
        self.assertEqual(receipt.error_message, "Operation timed out")
        self.assertTrue(result.get("error"))
        self.assertIn("timed out", result.get("message", ""))

    async def test_mcp_adapter_timeout_handling(self) -> None:
        import time
        MCP_DIR = REPO_ROOT / "platform" / "mcp-adapter"
        if str(MCP_DIR) not in sys.path:
            sys.path.insert(0, str(MCP_DIR))
        from mcp_adapter.client import McpClient
        from mcp_adapter.adapter import McpCapabilityAdapter

        stalled_cmd = [sys.executable, "-c", "import sys, time; sys.stdin.readline(); time.sleep(10)"]
        client = McpClient(command=stalled_cmd)
        adapter = McpCapabilityAdapter(
            client=client,
            tool_name="stalled_tool",
            description="Stalled tool",
            input_schema={},
            allowlist=["stalled_tool"],
        )

        try:
            executor = ToolExecutor(timeout_seconds=0.2)
            t0 = time.time()
            receipt, result = await executor.execute_tool(adapter, {}, action_id="act-mcp-timeout")
            elapsed = time.time() - t0

            self.assertLess(elapsed, 0.8)
            self.assertEqual(receipt.status, "failed")
            self.assertEqual(receipt.error_message, "Operation timed out")
            self.assertTrue(result.get("error"))
            self.assertIn("timed out", result.get("message", ""))
        finally:
            client.close()


if __name__ == "__main__":
    unittest.main()
