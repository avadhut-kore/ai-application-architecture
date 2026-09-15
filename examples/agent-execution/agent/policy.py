"""Application-controlled authorization policy evaluating actor roles and operational boundaries."""

from __future__ import annotations

from typing import Any, Mapping, Optional

from contracts.agent import (
    AgentActor,
    AuthorizationDecision,
    AuthorizationPort,
    CapabilityMetadata,
    SideEffectLevel,
)

from .domain import InMemoryCustomerStore


class CustomerSupportAuthorizationPolicy(AuthorizationPort):
    """Deterministic authorization policy protecting customer accounts against unauthorized mutations.

    Enforces the Principle of Least Privilege:
    1. Read-only inspection is permissible for all authenticated internal roles.
    2. Frozen customer accounts are protected: all mutations are strictly denied.
    3. Financial fee credits are bounded by role thresholds ($20.00 for junior agents, $50.00 for senior/admin).
    4. Model cannot bypass policy or authorize itself.
    """

    MAX_CREDIT_CENTS = 5000  # $50.00 maximum systemic ceiling
    JUNIOR_MAX_CREDIT_CENTS = 2000  # $20.00 maximum for junior staff

    def __init__(self, store: Optional[InMemoryCustomerStore] = None) -> None:
        self.store = store

    def authorize(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> AuthorizationDecision:
        # 1. Read-only capabilities are accessible to all internal staff roles
        if capability.side_effect_level == SideEffectLevel.READ_ONLY:
            if actor.role in ("junior_agent", "senior_agent", "admin"):
                return AuthorizationDecision(allowed=True, reason=f"Role '{actor.role}' is authorized for read-only access.")
            return AuthorizationDecision(
                allowed=False,
                reason=f"Unrecognized or unauthenticated actor role '{actor.role}' cannot access operational data.",
            )

        # 2. State-mutating capabilities require explicit authorization
        customer_id = str(arguments.get("customer_id", ""))

        # Check account hold status if repository is attached
        if self.store and customer_id:
            cust = self.store.get_customer(customer_id)
            if cust and cust.status == "frozen":
                return AuthorizationDecision(
                    allowed=False,
                    reason=f"POLICY VIOLATION: Customer '{customer_id}' is FROZEN under security hold. State mutations are prohibited.",
                )

        # 3. Evaluate specific capability constraints
        if capability.name == "apply_fee_credit":
            amount_cents = int(arguments.get("amount_cents", 0))

            # Systemic ceiling
            if amount_cents > self.MAX_CREDIT_CENTS:
                return AuthorizationDecision(
                    allowed=False,
                    reason=f"Requested credit amount (${amount_cents / 100:.2f}) exceeds system ceiling of ${self.MAX_CREDIT_CENTS / 100:.2f}.",
                )

            # Junior agent threshold
            if actor.role == "junior_agent" and amount_cents > self.JUNIOR_MAX_CREDIT_CENTS:
                return AuthorizationDecision(
                    allowed=False,
                    reason=f"Role 'junior_agent' is restricted to credits <= ${self.JUNIOR_MAX_CREDIT_CENTS / 100:.2f}. "
                    f"Requested ${amount_cents / 100:.2f} requires 'senior_agent' or 'admin' role.",
                )

            if actor.role in ("junior_agent", "senior_agent", "admin"):
                return AuthorizationDecision(
                    allowed=True,
                    reason=f"Role '{actor.role}' is authorized to propose credit of ${amount_cents / 100:.2f} (subject to approval).",
                )

        elif capability.name == "update_customer_note":
            if actor.role in ("junior_agent", "senior_agent", "admin"):
                return AuthorizationDecision(
                    allowed=True,
                    reason=f"Role '{actor.role}' is authorized to append customer notes.",
                )

        return AuthorizationDecision(
            allowed=False,
            reason=f"Actor role '{actor.role}' lacks permission for capability '{capability.name}'.",
        )
