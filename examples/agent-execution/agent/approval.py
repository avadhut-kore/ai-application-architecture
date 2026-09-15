"""Human-in-the-Loop (HITL) approval boundary implementations."""

from __future__ import annotations

import sys
from typing import Any, Dict, List, Mapping, Optional

from contracts.agent import (
    AgentActor,
    ApprovalDecision,
    ApprovalPort,
    CapabilityMetadata,
)


class DeterministicApprovalHandler(ApprovalPort):
    """Deterministic, non-interactive approval handler for automated testing and CI evaluation."""

    def __init__(self, default_approved: bool = True, canned_decisions: Optional[Mapping[str, bool]] = None) -> None:
        self.default_approved = default_approved
        self.canned_decisions: Dict[str, bool] = dict(canned_decisions or {})
        self.recorded_requests: List[Dict[str, Any]] = []

    async def request_approval(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> ApprovalDecision:
        action_id = str(arguments.get("action_id", ""))
        self.recorded_requests.append({
            "actor_id": actor.actor_id,
            "capability_name": capability.name,
            "arguments": dict(arguments),
            "action_id": action_id,
        })

        if action_id in self.canned_decisions:
            is_approved = self.canned_decisions[action_id]
        elif capability.name in self.canned_decisions:
            is_approved = self.canned_decisions[capability.name]
        else:
            is_approved = self.default_approved

        if is_approved:
            return ApprovalDecision(
                approved=True,
                approver="automated_evaluator",
                reason="Pre-configured deterministic approval granted.",
            )
        return ApprovalDecision(
            approved=False,
            approver="automated_evaluator",
            reason="Pre-configured deterministic approval rejected.",
        )


class CliApprovalHandler(ApprovalPort):
    """Interactive CLI approval handler prompting a human operator before state mutations."""

    def __init__(self, stdin_stream=sys.stdin, stdout_stream=sys.stdout) -> None:
        self.stdin = stdin_stream
        self.stdout = stdout_stream

    async def request_approval(
        self,
        actor: AgentActor,
        capability: CapabilityMetadata,
        arguments: Mapping[str, Any],
    ) -> ApprovalDecision:
        self.stdout.write("\n" + "=" * 60 + "\n")
        self.stdout.write("⚠️  HUMAN-IN-THE-LOOP APPROVAL REQUIRED\n")
        self.stdout.write("=" * 60 + "\n")
        self.stdout.write(f"Proposed Capability: {capability.name}\n")
        self.stdout.write(f"Side-Effect Level:   {capability.side_effect_level.value.upper()}\n")
        self.stdout.write(f"Initiating Actor:    {actor.actor_id} (Role: {actor.role})\n")
        self.stdout.write(f"Target Arguments:    {dict(arguments)}\n")
        self.stdout.write("=" * 60 + "\n")
        self.stdout.write("Approve this state mutation? [y/N]: ")
        self.stdout.flush()

        line = self.stdin.readline().strip().lower()
        if line in ("y", "yes"):
            self.stdout.write(">> Operation APPROVED by human operator.\n\n")
            self.stdout.flush()
            return ApprovalDecision(
                approved=True,
                approver="cli_human_operator",
                reason="Human operator confirmed execution at CLI prompt.",
            )

        self.stdout.write(">> Operation REJECTED by human operator.\n\n")
        self.stdout.flush()
        return ApprovalDecision(
            approved=False,
            approver="cli_human_operator",
            reason="Human operator declined confirmation at CLI prompt.",
        )
