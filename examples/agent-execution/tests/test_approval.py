"""Hermetic unit tests for approval handlers (Deterministic and CLI)."""

from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import (
    AgentActor,
    CapabilityMetadata,
    SideEffectLevel,
)
from agent.approval import (
    CliApprovalHandler,
    DeterministicApprovalHandler,
)


class TestDeterministicApprovalHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.actor = AgentActor(actor_id="test-agent", role="agent_tier_1")
        self.metadata = CapabilityMetadata(
            name="apply_fee_credit",
            description="Apply a credit",
            side_effect_level=SideEffectLevel.STATE_MUTATING,
            requires_approval=True,
            input_schema={},
        )

    async def test_default_approved(self) -> None:
        handler = DeterministicApprovalHandler(default_approved=True)
        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-1", "customer_id": "cust-001", "amount": 10.0},
        )
        self.assertTrue(decision.approved)
        self.assertEqual(decision.approver, "automated_evaluator")
        self.assertEqual(len(handler.recorded_requests), 1)
        self.assertEqual(handler.recorded_requests[0]["action_id"], "act-1")

    async def test_default_rejected(self) -> None:
        handler = DeterministicApprovalHandler(default_approved=False)
        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-2", "customer_id": "cust-001", "amount": 10.0},
        )
        self.assertFalse(decision.approved)
        self.assertEqual(decision.approver, "automated_evaluator")

    async def test_canned_decision_by_action_id(self) -> None:
        canned = {"act-allow": True, "act-deny": False}
        handler = DeterministicApprovalHandler(default_approved=True, canned_decisions=canned)

        dec_allow = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-allow"},
        )
        self.assertTrue(dec_allow.approved)

        dec_deny = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-deny"},
        )
        self.assertFalse(dec_deny.approved)

    async def test_canned_decision_by_capability_name(self) -> None:
        canned = {"apply_fee_credit": False}
        handler = DeterministicApprovalHandler(default_approved=True, canned_decisions=canned)

        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "unlisted-id"},
        )
        self.assertFalse(decision.approved)


class TestCliApprovalHandler(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.actor = AgentActor(actor_id="test-agent", role="agent_tier_1")
        self.metadata = CapabilityMetadata(
            name="apply_fee_credit",
            description="Apply a credit",
            side_effect_level=SideEffectLevel.STATE_MUTATING,
            requires_approval=True,
            input_schema={},
        )

    async def test_cli_approval_yes(self) -> None:
        stdin_stream = io.StringIO("y\n")
        stdout_stream = io.StringIO()
        handler = CliApprovalHandler(stdin_stream=stdin_stream, stdout_stream=stdout_stream)

        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-cli-1", "amount": 25.0},
        )
        self.assertTrue(decision.approved)
        self.assertEqual(decision.approver, "cli_human_operator")
        output = stdout_stream.getvalue()
        self.assertIn("HUMAN-IN-THE-LOOP APPROVAL REQUIRED", output)
        self.assertIn("apply_fee_credit", output)
        self.assertIn("APPROVED", output)

    async def test_cli_approval_no(self) -> None:
        stdin_stream = io.StringIO("n\n")
        stdout_stream = io.StringIO()
        handler = CliApprovalHandler(stdin_stream=stdin_stream, stdout_stream=stdout_stream)

        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-cli-2", "amount": 25.0},
        )
        self.assertFalse(decision.approved)
        self.assertEqual(decision.approver, "cli_human_operator")
        output = stdout_stream.getvalue()
        self.assertIn("REJECTED", output)

    async def test_cli_approval_default_enter_rejects(self) -> None:
        stdin_stream = io.StringIO("\n")
        stdout_stream = io.StringIO()
        handler = CliApprovalHandler(stdin_stream=stdin_stream, stdout_stream=stdout_stream)

        decision = await handler.request_approval(
            actor=self.actor,
            capability=self.metadata,
            arguments={"action_id": "act-cli-3"},
        )
        self.assertFalse(decision.approved)


if __name__ == "__main__":
    unittest.main()
