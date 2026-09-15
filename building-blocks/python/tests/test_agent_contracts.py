"""Unit tests for agent capability, decision, authorization, and approval contracts."""

from __future__ import annotations

import asyncio
import unittest
from typing import Any, Mapping, Optional

from contracts.agent import (
    AgentActor,
    AgentDecision,
    AgentDecisionType,
    ApprovalDecision,
    ApprovalPort,
    AuthorizationDecision,
    AuthorizationPort,
    CapabilityMetadata,
    CapabilityPort,
    ExecutionReceipt,
    SideEffectLevel,
)
from contracts.telemetry import AiOperationContext


class MockReadOnlyCapability:
    """Mock capability implementing CapabilityPort."""

    def __init__(self) -> None:
        self._metadata = CapabilityMetadata(
            name="get_customer",
            description="Fetch customer record",
            input_schema={"type": "object", "properties": {"customer_id": {"type": "string"}}},
            side_effect_level=SideEffectLevel.READ_ONLY,
            requires_approval=False,
        )

    @property
    def metadata(self) -> CapabilityMetadata:
        return self._metadata

    async def execute(
        self,
        arguments: Mapping[str, Any],
        context: Optional[AiOperationContext] = None,
    ) -> Any:
        return {"customer_id": arguments.get("customer_id"), "name": "Alice"}


class MockAuthorizationPolicy:
    """Mock authorization policy implementing AuthorizationPort."""

    def authorize(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> AuthorizationDecision:
        if "admin" in actor.permissions or capability.side_effect_level == SideEffectLevel.READ_ONLY:
            return AuthorizationDecision(allowed=True, reason="Authorized")
        return AuthorizationDecision(allowed=False, reason="Actor lacks permission")


class MockApprovalHandler:
    """Mock approval handler implementing ApprovalPort."""

    def __init__(self, should_approve: bool = True) -> None:
        self.should_approve = should_approve

    async def request_approval(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> ApprovalDecision:
        if self.should_approve:
            return ApprovalDecision(approved=True, approver="test_supervisor", reason="Test approved")
        return ApprovalDecision(approved=False, approver="test_supervisor", reason="Test rejected")


class TestAgentContracts(unittest.TestCase):
    """Test suite verifying agent contract invariants and runtime protocols."""

    def test_capability_metadata_validation(self) -> None:
        meta = CapabilityMetadata(
            name="test_tool",
            description="A test tool",
            input_schema={"type": "object"},
            side_effect_level=SideEffectLevel.STATE_MUTATING,
            requires_approval=True,
        )
        self.assertEqual(meta.name, "test_tool")
        self.assertEqual(meta.side_effect_level, SideEffectLevel.STATE_MUTATING)
        self.assertTrue(meta.requires_approval)

        with self.assertRaises(ValueError):
            CapabilityMetadata(
                name="",
                description="desc",
                input_schema={},
                side_effect_level=SideEffectLevel.READ_ONLY,
            )

        with self.assertRaises(TypeError):
            CapabilityMetadata(
                name="tool",
                description="desc",
                input_schema="not_a_dict",  # type: ignore[arg-type]
                side_effect_level=SideEffectLevel.READ_ONLY,
            )

    def test_capability_port_protocol_conformance(self) -> None:
        cap = MockReadOnlyCapability()
        self.assertIsInstance(cap, CapabilityPort)

        result = asyncio.run(cap.execute({"customer_id": "cust-123"}))
        self.assertEqual(result["customer_id"], "cust-123")
        self.assertEqual(result["name"], "Alice")

    def test_agent_decision_validation(self) -> None:
        action_decision = AgentDecision(
            decision_type=AgentDecisionType.ACTION,
            action_name="get_customer",
            arguments={"customer_id": "c1"},
            explanation="Need customer details",
        )
        self.assertEqual(action_decision.action_name, "get_customer")

        with self.assertRaises(ValueError):
            AgentDecision(decision_type=AgentDecisionType.ACTION, action_name="")

        final_decision = AgentDecision(
            decision_type=AgentDecisionType.FINAL,
            final_answer="The customer is active.",
        )
        self.assertEqual(final_decision.final_answer, "The customer is active.")

        with self.assertRaises(ValueError):
            AgentDecision(decision_type=AgentDecisionType.FINAL, final_answer="")

        clarify_decision = AgentDecision(
            decision_type=AgentDecisionType.CLARIFICATION,
            clarification_question="Which customer ID?",
        )
        self.assertEqual(clarify_decision.clarification_question, "Which customer ID?")

        with self.assertRaises(ValueError):
            AgentDecision(decision_type=AgentDecisionType.CLARIFICATION, clarification_question="")

    def test_authorization_port_and_decision(self) -> None:
        policy = MockAuthorizationPolicy()
        self.assertIsInstance(policy, AuthorizationPort)

        read_meta = CapabilityMetadata("read", "read", {}, SideEffectLevel.READ_ONLY)
        mutate_meta = CapabilityMetadata("mutate", "mutate", {}, SideEffectLevel.STATE_MUTATING)

        junior_actor = AgentActor(actor_id="user1", role="junior", permissions=["view"])
        admin_actor = AgentActor(actor_id="user2", role="admin", permissions=["admin", "view"])

        # Junior can read
        dec1 = policy.authorize(junior_actor, read_meta, {})
        self.assertTrue(dec1.allowed)

        # Junior cannot mutate
        dec2 = policy.authorize(junior_actor, mutate_meta, {})
        self.assertFalse(dec2.allowed)
        self.assertEqual(dec2.reason, "Actor lacks permission")

        # Admin can mutate
        dec3 = policy.authorize(admin_actor, mutate_meta, {})
        self.assertTrue(dec3.allowed)

    def test_approval_port_and_decision(self) -> None:
        approver = MockApprovalHandler(should_approve=True)
        self.assertIsInstance(approver, ApprovalPort)

        meta = CapabilityMetadata("credit", "apply credit", {}, SideEffectLevel.STATE_MUTATING, True)
        actor = AgentActor("agent1", "support", ["credit"])

        res = asyncio.run(approver.request_approval(actor, meta, {"amount": 2500}))
        self.assertTrue(res.approved)
        self.assertEqual(res.approver, "test_supervisor")

        rejecter = MockApprovalHandler(should_approve=False)
        res_reject = asyncio.run(rejecter.request_approval(actor, meta, {"amount": 2500}))
        self.assertFalse(res_reject.approved)

    def test_execution_receipt(self) -> None:
        receipt = ExecutionReceipt(
            action_id="act-001",
            capability_name="apply_fee_credit",
            status="succeeded",
            result_summary="Credited $25.00",
        )
        self.assertEqual(receipt.action_id, "act-001")
        self.assertEqual(receipt.status, "succeeded")
        self.assertGreater(receipt.executed_at, 0)


if __name__ == "__main__":
    unittest.main()
