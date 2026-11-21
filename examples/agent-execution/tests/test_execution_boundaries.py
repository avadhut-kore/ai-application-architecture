"""Scoped replay, bounded results and trace retention at failure boundaries."""

import asyncio
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "examples/agent-execution")]
from agent.executor import ToolExecutor
from agent.observation import bounded_json, bounded_text, exception_message
from contracts.agent import SideEffectLevel
from tests.test_executor import DummyTool


class TestExecutionBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_scope_and_capability_instance_are_bound_to_action(self):
        executor = ToolExecutor()
        tool = DummyTool(side_effect_level=SideEffectLevel.STATE_MUTATING)
        await executor.execute_tool(tool, {}, "id", execution_scope="actor-one")
        for cap, scope in [
            (tool, "actor-two"),
            (DummyTool(side_effect_level=SideEffectLevel.STATE_MUTATING), "actor-one"),
        ]:
            with self.assertRaises(ValueError):
                await executor.execute_tool(cap, {}, "id", execution_scope=scope)
        with self.assertRaises(ValueError):
            await executor.execute_tool(tool, {}, "next", execution_scope=" ")

    async def test_large_and_invalid_mutation_results_are_ambiguous_and_not_repeated(self):
        class Large(DummyTool):
            async def execute(self, arguments, context=None):
                self.call_count += 1
                return {"value": "x" * 100000}

        executor = ToolExecutor()
        tool = Large(side_effect_level=SideEffectLevel.STATE_MUTATING)
        first, result = await executor.execute_tool(tool, {}, "id")
        self.assertEqual(first.status, "ambiguous")
        self.assertLessEqual(len(result["preview"]), 16384)
        result["message"] = "changed by caller"
        _, replay = await executor.execute_tool(tool, {}, "id")
        self.assertNotEqual(replay["cached_result"]["message"], result["message"])
        self.assertEqual(tool.call_count, 1)
        with self.assertRaises(ValueError):
            await executor.execute_tool(tool, {"value": "x" * 20000}, "new")
        self.assertEqual(tool.call_count, 1)

    async def test_argument_snapshot_survives_caller_mutation(self):
        entered, proceed = asyncio.Event(), asyncio.Event()

        class Capture(DummyTool):
            async def execute(self, arguments, context=None):
                entered.set()
                await proceed.wait()
                return arguments

        args = {"nested": {"amount": 1}}
        task = asyncio.create_task(ToolExecutor().execute_tool(Capture(), args))
        await entered.wait()
        args["nested"]["amount"] = 999
        proceed.set()
        _, result = await task
        self.assertEqual(result["nested"]["amount"], 1)

    def test_broken_exception_and_invalid_preview_limits(self):
        class Broken(Exception):
            def __str__(self):
                raise RuntimeError("formatter failed")

        self.assertEqual(exception_message(Broken()), "Broken")
        self.assertLessEqual(len(exception_message(Exception("x" * 2000))), 1024)
        for function in [lambda: bounded_text("", 1), lambda: bounded_json({}, 1)]:
            with self.assertRaises(ValueError):
                function()
