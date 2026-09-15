"""Unit tests for application authorization policy."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = Path(__file__).resolve().parent.parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.capabilities import (
    ApplyFeeCreditCapability,
    GetCustomerCapability,
    UpdateCustomerNoteCapability,
)
from agent.domain import InMemoryCustomerStore
from agent.policy import CustomerSupportAuthorizationPolicy
from contracts.agent import AgentActor


class TestAuthorizationPolicy(unittest.TestCase):
    """Test suite verifying application-controlled authorization rules and security boundaries."""

    def setUp(self) -> None:
        self.store = InMemoryCustomerStore()
        self.policy = CustomerSupportAuthorizationPolicy(store=self.store)

        self.get_cust = GetCustomerCapability(self.store)
        self.apply_credit = ApplyFeeCreditCapability(self.store)
        self.add_note = UpdateCustomerNoteCapability(self.store)

        self.junior = AgentActor(actor_id="j1", role="junior_agent", permissions=["support"])
        self.senior = AgentActor(actor_id="s1", role="senior_agent", permissions=["support", "credit_approval"])
        self.guest = AgentActor(actor_id="g1", role="guest", permissions=[])

    def test_read_only_allowed_for_internal_staff(self) -> None:
        dec = self.policy.authorize(self.junior, self.get_cust.metadata, {"customer_id": "cust-001"})
        self.assertTrue(dec.allowed)

        dec_guest = self.policy.authorize(self.guest, self.get_cust.metadata, {"customer_id": "cust-001"})
        self.assertFalse(dec_guest.allowed)
        self.assertIn("cannot access operational data", dec_guest.reason)

    def test_junior_agent_credit_limits(self) -> None:
        # $15.00 (1500 cents) -> Allowed
        dec_ok = self.policy.authorize(
            self.junior,
            self.apply_credit.metadata,
            {"customer_id": "cust-001", "amount_cents": 1500},
        )
        self.assertTrue(dec_ok.allowed)

        # $25.00 (2500 cents) -> Denied for junior agent
        dec_denied = self.policy.authorize(
            self.junior,
            self.apply_credit.metadata,
            {"customer_id": "cust-001", "amount_cents": 2500},
        )
        self.assertFalse(dec_denied.allowed)
        self.assertIn("restricted to credits <= $20.00", dec_denied.reason)

    def test_senior_agent_credit_limits_and_system_ceiling(self) -> None:
        # $45.00 -> Allowed for senior agent
        dec_ok = self.policy.authorize(
            self.senior,
            self.apply_credit.metadata,
            {"customer_id": "cust-001", "amount_cents": 4500},
        )
        self.assertTrue(dec_ok.allowed)

        # $60.00 (6000 cents) -> Exceeds system ceiling ($50.00)
        dec_denied = self.policy.authorize(
            self.senior,
            self.apply_credit.metadata,
            {"customer_id": "cust-001", "amount_cents": 6000},
        )
        self.assertFalse(dec_denied.allowed)
        self.assertIn("exceeds system ceiling of $50.00", dec_denied.reason)

    def test_frozen_customer_account_denies_all_mutations(self) -> None:
        # cust-003 is frozen under security hold
        dec_credit = self.policy.authorize(
            self.senior,
            self.apply_credit.metadata,
            {"customer_id": "cust-003", "amount_cents": 1000},
        )
        self.assertFalse(dec_credit.allowed)
        self.assertIn("is FROZEN under security hold", dec_credit.reason)

        dec_note = self.policy.authorize(
            self.senior,
            self.add_note.metadata,
            {"customer_id": "cust-003", "note": "Test note"},
        )
        self.assertFalse(dec_note.allowed)
        self.assertIn("is FROZEN under security hold", dec_note.reason)


if __name__ == "__main__":
    unittest.main()
