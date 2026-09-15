"""Unit tests for capability registry and parameter schema validation."""

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
    GetAccountStatusCapability,
    GetCustomerCapability,
)
from agent.domain import InMemoryCustomerStore
from agent.registry import CapabilityRegistry


class TestCapabilityRegistry(unittest.TestCase):
    """Test suite verifying capability registration, allowlisting, and parameter validation."""

    def setUp(self) -> None:
        self.store = InMemoryCustomerStore()
        self.get_cust = GetCustomerCapability(self.store)
        self.get_acc = GetAccountStatusCapability(self.store)
        self.apply_credit = ApplyFeeCreditCapability(self.store)
        self.registry = CapabilityRegistry([self.get_cust, self.get_acc, self.apply_credit])

    def test_duplicate_registration_rejected(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            self.registry.register(self.get_cust)
        self.assertIn("already registered", str(ctx.exception))

    def test_lookup_registered_capability(self) -> None:
        self.assertTrue(self.registry.is_registered("get_customer"))
        self.assertFalse(self.registry.is_registered("delete_database"))
        self.assertIsNotNone(self.registry.get("get_account_status"))
        self.assertIsNone(self.registry.get("delete_database"))

    def test_validate_unknown_tool_fails(self) -> None:
        val_res = self.registry.validate_arguments("unknown_tool", {})
        self.assertFalse(val_res.is_valid)
        self.assertIn("Unknown capability 'unknown_tool'", val_res.errors[0])

    def test_validate_valid_arguments_passes(self) -> None:
        val_res = self.registry.validate_arguments("get_customer", {"customer_id": "cust-001"})
        self.assertTrue(val_res.is_valid)
        self.assertEqual(len(val_res.errors), 0)

    def test_validate_missing_required_arguments(self) -> None:
        val_res = self.registry.validate_arguments("apply_fee_credit", {"customer_id": "cust-001"})
        self.assertFalse(val_res.is_valid)
        error_text = " ".join(val_res.errors)
        self.assertIn("Missing required parameter 'amount_cents'", error_text)
        self.assertIn("Missing required parameter 'reason'", error_text)
        self.assertIn("Missing required parameter 'action_id'", error_text)

    def test_validate_incorrect_argument_type(self) -> None:
        # amount_cents must be integer, passed string
        val_res = self.registry.validate_arguments(
            "apply_fee_credit",
            {
                "customer_id": "cust-001",
                "amount_cents": "five hundred",
                "reason": "Test",
                "action_id": "act-1",
            },
        )
        self.assertFalse(val_res.is_valid)
        self.assertIn("must be an integer", val_res.errors[0])

    def test_validate_unexpected_argument_rejected(self) -> None:
        # schema specifies additionalProperties: False
        val_res = self.registry.validate_arguments(
            "get_customer",
            {
                "customer_id": "cust-001",
                "malicious_override": True,
            },
        )
        self.assertFalse(val_res.is_valid)
        self.assertIn("Unexpected parameter 'malicious_override'", val_res.errors[0])


if __name__ == "__main__":
    unittest.main()
