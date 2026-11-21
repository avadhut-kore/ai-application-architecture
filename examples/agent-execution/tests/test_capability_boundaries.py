"""Capability error results and metadata-only audit serialization."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "building-blocks/python"))

from agent.capabilities import (
    GetCustomerCapability,
    GetAccountStatusCapability,
    SearchPolicyCapability,
    UpdateCustomerNoteCapability,
    ApplyFeeCreditCapability,
)
from agent.domain import InMemoryCustomerStore
from agent.trace import AgentTrajectoryTrace, AgentStepRecord
from contracts.agent import (
    AgentActor,
    AgentDecision,
    AgentDecisionType,
    ApprovalDecision,
    AuthorizationDecision,
    ExecutionReceipt,
)


class TestCapabilityBoundaries(unittest.IsolatedAsyncioTestCase):
    async def test_missing_customer_and_invalid_mutations_are_explicit_failures(self):
        store = InMemoryCustomerStore()
        for capability, args in [
            (GetCustomerCapability(store), {"customer_id": "missing"}),
            (GetAccountStatusCapability(store), {"customer_id": "missing"}),
            (UpdateCustomerNoteCapability(store), {"customer_id": "cust-001", "note": ""}),
            (UpdateCustomerNoteCapability(store), {"customer_id": "missing", "note": "note"}),
            (ApplyFeeCreditCapability(store), {"customer_id": "cust-001", "amount_cents": 0}),
            (ApplyFeeCreditCapability(store), {"customer_id": "missing", "amount_cents": 100}),
        ]:
            result = await capability.execute(args)
            self.assertTrue(result.get("error"))
        matched = await SearchPolicyCapability().execute({"topic": "credit_limit"})
        self.assertTrue(matched["found"])
        unmatched = await SearchPolicyCapability().execute({"topic": "NO_SUCH_POLICY_923"})
        self.assertFalse(unmatched["found"])

    def test_audit_summary_omits_raw_goal_and_observations(self):
        trace = AgentTrajectoryTrace(
            "run", "PRIVATE customer inquiry", AgentActor("a", "senior_agent")
        )
        trace.record_step(
            AgentStepRecord(
                1,
                AgentDecision(
                    AgentDecisionType.ACTION,
                    action_name="get_customer",
                    arguments={"secret": "PRIVATE"},
                ),
                authorization_result=AuthorizationDecision(True, "authorized"),
                approval_result=ApprovalDecision(True, "manager"),
                execution_receipt=ExecutionReceipt("id", "get_customer", "succeeded"),
                sanitized_observation="PRIVATE observation",
            )
        )
        trace.complete("COMPLETED")
        summary = trace.to_audit_summary()
        self.assertNotIn("PRIVATE", json.dumps(summary))
        self.assertEqual(summary["steps"][0]["execution_status"], "succeeded")
