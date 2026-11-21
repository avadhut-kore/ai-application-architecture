"""Ownership, audit integrity, retry accounting and public recovery boundaries."""

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "building-blocks/python"), str(ROOT / "examples/agentic-workflow")]
from contracts.workflow import WorkflowStatus, StepExecutionStatus
from workflow.audit import WorkflowAuditEvent, WorkflowAuditRecorder
from workflow.definition import WorkflowDefinition, StepDefinition, TransitionRule
from workflow.engine import WorkflowEngine
from workflow.errors import (
    ConcurrentResumeConflictError,
    IncompatibleWorkflowDefinitionError,
    InvalidTransitionError,
)
from workflow.retry import StepRetryPolicy
from workflow.state import StepOutcome, WorkflowActorSnapshot
from workflow.store import InMemoryWorkflowStore, SQLiteWorkflowStore


class TestEngineBoundaries(unittest.IsolatedAsyncioTestCase):
    def make_engine(self, handler, default="done", rules=()):
        definition = WorkflowDefinition(
            "test",
            "1",
            "start",
            [
                StepDefinition("start", handler, transitions=rules, default_transition=default),
                StepDefinition(
                    "done",
                    lambda _: StepOutcome(StepExecutionStatus.SUCCEEDED, "done"),
                    is_terminal=True,
                    terminal_status=WorkflowStatus.COMPLETED,
                ),
            ],
        )
        return WorkflowEngine(
            definition,
            InMemoryWorkflowStore(),
            retry_policy=StepRetryPolicy(max_retries=2, base_delay_ms=0),
        )

    async def test_retry_records_actual_attempt_and_time(self):
        attempts = []

        async def handler(state):
            attempts.append(1)
            if len(attempts) == 1:
                raise ConnectionError("Transient read failure")
            return StepOutcome(StepExecutionStatus.SUCCEEDED, "ok")

        engine = self.make_engine(handler)
        state = await engine.start_workflow("id", WorkflowActorSnapshot("a", "operator"))
        self.assertEqual(state.history[0].attempt, 2)
        self.assertGreaterEqual(state.history[0].completed_at, state.history[0].started_at)
        with self.assertRaises(ValueError):
            await engine.start_workflow("id", WorkflowActorSnapshot("a", "operator"))

    async def test_invalid_handler_and_unmatched_transition_fail_closed(self):
        engine = self.make_engine(
            lambda _: "invalid", default=None, rules=(TransitionRule("done", lambda s, o: False),)
        )
        state = await engine.start_workflow("id", WorkflowActorSnapshot("a", "operator"))
        self.assertEqual(state.status, WorkflowStatus.FAILED)
        with self.assertRaises(ValueError):
            await engine.recover_workflow("missing")
        incompatible = replace(state, definition=replace(state.definition, version="other"))
        engine.store.save_state(incompatible)
        with self.assertRaises(IncompatibleWorkflowDefinitionError):
            await engine.recover_workflow("id")

    async def test_terminal_recovery_and_missing_step(self):
        engine = self.make_engine(lambda _: StepOutcome(StepExecutionStatus.SUCCEEDED, "ok"))
        state = await engine.start_workflow("id", WorkflowActorSnapshot("a", "operator"))
        self.assertEqual((await engine.recover_workflow("id")).status, WorkflowStatus.COMPLETED)
        bad = replace(state, current_step="unknown", status=WorkflowStatus.RUNNING)
        with self.assertRaises(InvalidTransitionError):
            await engine._run_loop(bad)
        terminal = replace(state, current_step="done", status=WorkflowStatus.RUNNING)
        self.assertEqual((await engine._run_loop(terminal)).status, WorkflowStatus.COMPLETED)

    def test_live_owner_cannot_be_stolen(self):
        memory = InMemoryWorkflowStore()
        with memory.execution_lock("id"):
            with self.assertRaises(ConcurrentResumeConflictError):
                with memory.execution_lock("id"):
                    self.fail("duplicate owner acquired")
        with tempfile.TemporaryDirectory() as directory:
            one = SQLiteWorkflowStore(str(Path(directory) / "store.db"))
            two = SQLiteWorkflowStore(str(Path(directory) / "store.db"))
            with one.execution_lock("id"):
                with self.assertRaises(ConcurrentResumeConflictError):
                    with two.execution_lock("id"):
                        self.fail("duplicate owner acquired")

    def test_audit_event_roundtrip_and_workflow_filter(self):
        recorder = WorkflowAuditRecorder()
        event = recorder.record("one", "started", details={"safe": True})
        recorder.record("two", "started")
        self.assertEqual(WorkflowAuditEvent.from_dict(event.to_dict()), event)
        self.assertEqual(len(recorder.get_events()), 2)
        self.assertEqual(recorder.get_events("one"), [event])
