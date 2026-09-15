"""Synthetic customer and account domain models and in-memory repository."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Customer:
    """Customer account record."""

    customer_id: str
    name: str
    email: str
    risk_level: str  # "low" | "high"
    status: str  # "active" | "frozen"
    created_at: float = field(default_factory=time.time)


@dataclass
class Account:
    """Customer financial and operational account state."""

    customer_id: str
    balance_cents: int
    currency: str = "USD"
    notes: List[str] = field(default_factory=list)
    activity_log: List[str] = field(default_factory=list)
    credits_applied_cents: int = 0


class InMemoryCustomerStore:
    """Deterministic, in-memory store for customer support operations."""

    def __init__(self) -> None:
        self._customers: Dict[str, Customer] = {}
        self._accounts: Dict[str, Account] = {}
        self.reset()

    def reset(self) -> None:
        """Reset repository to clean synthetic baseline state."""
        self._customers = {
            "cust-001": Customer(
                customer_id="cust-001",
                name="Alice Smith",
                email="alice@example.com",
                risk_level="low",
                status="active",
            ),
            "cust-002": Customer(
                customer_id="cust-002",
                name="Bob Jones",
                email="bob@example.com",
                risk_level="high",
                status="active",
            ),
            "cust-003": Customer(
                customer_id="cust-003",
                name="Carol White",
                email="carol@example.com",
                risk_level="high",
                status="frozen",  # Security hold
            ),
            "cust-004": Customer(
                customer_id="cust-004",
                name="David Miller",
                email="david@example.com",
                risk_level="low",
                status="active",
            ),
        }

        self._accounts = {
            "cust-001": Account(
                customer_id="cust-001",
                balance_cents=15000,  # $150.00
                notes=["Account opened via mobile app."],
                activity_log=["2026-09-01: Standard subscription charge $15.00", "2026-09-10: Late fee charged $10.00"],
            ),
            "cust-002": Account(
                customer_id="cust-002",
                balance_cents=2000,  # $20.00
                notes=["Flagged for high transaction velocity."],
                activity_log=["2026-09-05: Disputed transaction $45.00", "2026-09-12: Chargeback request received"],
            ),
            "cust-003": Account(
                customer_id="cust-003",
                balance_cents=50000,  # $500.00
                notes=["Account frozen pending identity verification."],
                activity_log=["2026-08-30: Multiple failed MFA attempts", "2026-09-01: Administrative freeze applied"],
            ),
            "cust-004": Account(
                customer_id="cust-004",
                balance_cents=0,  # $0.00
                notes=["New account with no billing issues."],
                activity_log=["2026-09-14: Welcome credit applied"],
            ),
        }

    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Fetch customer profile by ID."""
        return self._customers.get(customer_id)

    def get_account(self, customer_id: str) -> Optional[Account]:
        """Fetch account state by customer ID."""
        return self._accounts.get(customer_id)

    def add_note(self, customer_id: str, note: str) -> bool:
        """Append an operational note to customer account."""
        account = self._accounts.get(customer_id)
        if not account:
            return False
        clean_note = note.strip()
        account.notes.append(clean_note)
        account.activity_log.append(f"Note added: {clean_note}")
        return True

    def apply_credit(self, customer_id: str, amount_cents: int, reason: str) -> bool:
        """Apply financial credit to customer account balance."""
        account = self._accounts.get(customer_id)
        if not account:
            return False
        if amount_cents <= 0:
            raise ValueError("Credit amount must be strictly positive")
        account.balance_cents += amount_cents
        account.credits_applied_cents += amount_cents
        account.activity_log.append(f"Credit applied: +${amount_cents / 100:.2f} (Reason: {reason})")
        return True
