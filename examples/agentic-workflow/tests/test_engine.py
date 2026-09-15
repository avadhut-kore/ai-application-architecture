"""Unit tests for WorkflowEngine, graph routing, and transition validation."""

import asyncio
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
WORKFLOW_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.workflow import (
    StepExecutionStatus,
    WorkflowDefinitionRef,
    WorkflowStatus,
)

from workflow.definition import StepDefinition, TransitionRule, WorkflowDefinition
from workflow.engine import WorkflowEngine
from workflow.errors import (
    InvalidTransitionError,
    MaxTransitionsExceededError,
    WorkflowDefinitionError,
)
from workflow.state import StepOutcome, WorkflowActorSnapshot, WorkflowState
from workflow.store import InMemoryWorkflowStore


class TestWorkflowEngine(unittest.IsolatedAsyncioTestCase):
    """Verify deterministic state machine progression, bounds, and transition guards."""

    def setUp(self) -> None:
        self.actor = WorkflowActorSnapshot(actor_id="test_actor", role="operator")
        self.store = InMemoryWorkflowStore()

    def test_workflow_definition_graph_validation_failures(self) -> None:
        # Empty steps
        with self.assertRaises(WorkflowDefinitionError):
            WorkflowDefinition(
                definition_id="bad",
                version="1.0",
                start_step="step1",
                steps=[],
            )

        # Missing start step
        with self.assertRaises(WorkflowDefinitionError):
            WorkflowDefinition(
                definition_id="bad",
                version="1.0",
                start_step="nonexistent",
                steps=[
                    StepDefinition(
                        name="step1",
                        handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "ok"),
                        default_transition="terminal",
                    ),
                    StepDefinition(
                        name="terminal",
                        handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "done"),
                        is_terminal=True,
                        terminal_status=WorkflowStatus.COMPLETED,
                    ),
                ],
            )

        # Transition to unknown target step
        with self.assertRaises(WorkflowDefinitionError):
            WorkflowDefinition(
                definition_id="bad",
                version="1.0",
                start_step="step1",
                steps=[
                    StepDefinition(
                        name="step1",
                        handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "ok"),
                        transitions=(TransitionRule(target_step="ghost_step", condition_fn=lambda s, o: True),),
                    ),
                    StepDefinition(
                        name="terminal",
                        handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "done"),
                        is_terminal=True,
                        terminal_status=WorkflowStatus.COMPLETED,
                    ),
                ],
            )

        # Terminal step cannot have outgoing transitions
        with self.assertRaises(ValueError):
            StepDefinition(
                name="bad_term",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "done"),
                is_terminal=True,
                terminal_status=WorkflowStatus.COMPLETED,
                default_transition="step1",
            )

    async def test_straight_through_execution_success(self) -> None:
        steps = [
            StepDefinition(
                name="step_a",
                handler=lambda s: StepOutcome(
                    StepExecutionStatus.SUCCEEDED, "a_done", context_updates={"val": 42}
                ),
                default_transition="step_b",
            ),
            StepDefinition(
                name="step_b",
                handler=lambda s: StepOutcome(
                    StepExecutionStatus.SUCCEEDED, "b_done", context_updates={"doubled": s.domain_context["val"] * 2}
                ),
                default_transition="term_complete",
            ),
            StepDefinition(
                name="term_complete",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "final"),
                is_terminal=True,
                terminal_status=WorkflowStatus.COMPLETED,
            ),
        ]

        definition = WorkflowDefinition(
            definition_id="linear_test",
            version="1.0.0",
            start_step="step_a",
            steps=steps,
        )

        engine = WorkflowEngine(definition=definition, store=self.store)
        final_state = await engine.start_workflow("wf-001", actor=self.actor)

        self.assertEqual(final_state.status, WorkflowStatus.COMPLETED)
        self.assertEqual(final_state.current_step, "term_complete")
        self.assertEqual(final_state.domain_context["doubled"], 84)
        self.assertEqual(len(final_state.history), 2)  # step_a and step_b

    async def test_conditional_branch_routing(self) -> None:
        steps = [
            StepDefinition(
                name="decision_step",
                handler=lambda s: StepOutcome(
                    StepExecutionStatus.SUCCEEDED,
                    outcome_type=s.domain_context.get("route_choice", "branch_a"),
                ),
                transitions=(
                    TransitionRule(
                        target_step="branch_a_step",
                        condition_fn=lambda s, o: o.outcome_type == "branch_a",
                    ),
                    TransitionRule(
                        target_step="branch_b_step",
                        condition_fn=lambda s, o: o.outcome_type == "branch_b",
                    ),
                ),
                default_transition="term_failed",
            ),
            StepDefinition(
                name="branch_a_step",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "a_ok"),
                default_transition="term_complete",
            ),
            StepDefinition(
                name="branch_b_step",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "b_ok"),
                default_transition="term_rejected",
            ),
            StepDefinition(
                name="term_complete",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "done"),
                is_terminal=True,
                terminal_status=WorkflowStatus.COMPLETED,
            ),
            StepDefinition(
                name="term_rejected",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "rejected"),
                is_terminal=True,
                terminal_status=WorkflowStatus.REJECTED,
            ),
            StepDefinition(
                name="term_failed",
                handler=lambda s: StepOutcome(StepExecutionStatus.FAILED, "failed"),
                is_terminal=True,
                terminal_status=WorkflowStatus.FAILED,
            ),
        ]

        definition = WorkflowDefinition(
            definition_id="branch_test",
            version="1.0.0",
            start_step="decision_step",
            steps=steps,
        )

        engine = WorkflowEngine(definition=definition, store=self.store)

        # Route A -> COMPLETED
        state_a = await engine.start_workflow("wf-route-a", actor=self.actor, domain_context={"route_choice": "branch_a"})
        self.assertEqual(state_a.status, WorkflowStatus.COMPLETED)

        # Route B -> REJECTED
        state_b = await engine.start_workflow("wf-route-b", actor=self.actor, domain_context={"route_choice": "branch_b"})
        self.assertEqual(state_b.status, WorkflowStatus.REJECTED)

    async def test_max_transitions_ceiling_cycle_protection(self) -> None:
        """Verify that infinite loop cycles hit the max_transitions ceiling and abort to FAILED."""
        steps = [
            StepDefinition(
                name="ping",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "ping_done"),
                default_transition="pong",
            ),
            StepDefinition(
                name="pong",
                handler=lambda s: StepOutcome(StepExecutionStatus.SUCCEEDED, "pong_done"),
                default_transition="ping",
            ),
            StepDefinition(
                name="term_failed",
                handler=lambda s: StepOutcome(StepExecutionStatus.FAILED, "failed"),
                is_terminal=True,
                terminal_status=WorkflowStatus.FAILED,
            ),
        ]

        # Ceiling set to 6 transitions
        definition = WorkflowDefinition(
            definition_id="cycle_test",
            version="1.0.0",
            start_step="ping",
            steps=steps,
            max_transitions=6,
        )

        engine = WorkflowEngine(definition=definition, store=self.store)

        with self.assertRaises(MaxTransitionsExceededError):
            await engine.start_workflow("wf-cycle", actor=self.actor)

        # State in store should be persisted as FAILED
        persisted = self.store.load_state("wf-cycle")
        assert persisted is not None
        self.assertEqual(persisted.status, WorkflowStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
