#!/usr/bin/env python3
"""Interactive and canned demonstration CLI for Phase 6 Bounded Agentic Task Execution."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
PLATFORM_OLLAMA_DIR = REPO_ROOT / "platform" / "ollama-adapter"
AGENT_EXEC_DIR = Path(__file__).resolve().parent

for p in (BUILDING_BLOCKS_DIR, PLATFORM_OLLAMA_DIR, AGENT_EXEC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from contracts.agent import AgentActor, ApprovalPort
from contracts.ports import TextGenerationPort
from agent.approval import CliApprovalHandler, DeterministicApprovalHandler
from agent.capabilities import (
    ApplyFeeCreditCapability,
    GetAccountStatusCapability,
    GetCustomerCapability,
    SearchPolicyCapability,
    UpdateCustomerNoteCapability,
)
from agent.domain import InMemoryCustomerStore
from agent.engine import AgentExecutionEngine
from agent.executor import ToolExecutor
from agent.policy import CustomerSupportAuthorizationPolicy
from agent.registry import CapabilityRegistry
from agent.test_doubles import ScriptedGenerationStub
from ollama_adapter.adapter import OllamaAdapter

SCENARIOS: Dict[str, Dict[str, Any]] = {
    "read": {
        "description": "Inspect customer profile for Alice Smith (cust-001)",
        "goal": (
            "Retrieve the customer and account records for cust-001, then report the name, "
            "status, risk, balance and recent activity from those observations. This is a "
            "read-only report: conclude after retrieving both records, without asking "
            "whether to proceed with other actions."
        ),
        "actor": AgentActor(actor_id="agent-alice", role="junior_agent"),
        "approval_response": True,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "get_customer",
                    "arguments": {"customer_id": "cust-001"},
                    "explanation": "Looking up customer profile for cust-001",
                }
            ),
            json.dumps(
                {
                    "type": "final",
                    "final_answer": "Customer Alice Smith is active with low risk tier and active account status.",
                    "explanation": "Verified records",
                }
            ),
        ],
    },
    "multi-read": {
        "description": "Multi-step inquiry retrieving profile and balance for cust-001",
        "goal": "Check full profile and account balance for customer cust-001",
        "actor": AgentActor(actor_id="agent-alice", role="junior_agent"),
        "approval_response": True,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "get_customer",
                    "arguments": {"customer_id": "cust-001"},
                    "explanation": "Check customer identity",
                }
            ),
            json.dumps(
                {
                    "type": "action",
                    "action_name": "get_account_status",
                    "arguments": {"customer_id": "cust-001"},
                    "explanation": "Retrieve account balance and activity",
                }
            ),
            json.dumps(
                {
                    "type": "final",
                    "final_answer": "Customer Alice Smith is active with low risk. Account balance is $150.00 with 2 recent transactions.",
                    "explanation": "Combined profile and balance",
                }
            ),
        ],
    },
    "mutation-approve": {
        "description": "Propose and approve $15 fee credit for cust-001 (human approval granted)",
        "goal": "Apply a $15 fee credit to cust-001 for recent late fee dispute",
        "actor": AgentActor(actor_id="agent-alice", role="junior_agent"),
        "approval_response": True,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "apply_fee_credit",
                    "arguments": {
                        "customer_id": "cust-001",
                        "amount_cents": 1500,
                        "reason": "Late fee dispute resolution",
                        "action_id": "demo-act-001",
                    },
                    "explanation": "Proposing $15 credit within junior agent threshold",
                }
            ),
            json.dumps(
                {
                    "type": "final",
                    "final_answer": "A fee credit of $15.00 has been successfully approved and applied to customer cust-001. New balance is $165.00.",
                    "explanation": "Confirmed via execution receipt",
                }
            ),
        ],
    },
    "mutation-reject": {
        "description": "Propose $15 fee credit for cust-001 but human operator declines approval",
        "goal": "Apply a $15 fee credit to cust-001",
        "actor": AgentActor(actor_id="agent-alice", role="junior_agent"),
        "approval_response": False,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "apply_fee_credit",
                    "arguments": {
                        "customer_id": "cust-001",
                        "amount_cents": 1500,
                        "reason": "Customer courtesy credit",
                        "action_id": "demo-act-002",
                    },
                    "explanation": "Proposing fee credit",
                }
            ),
        ],
    },
    "denied": {
        "description": "Junior agent proposes $35 credit exceeding $20 role limit (policy denial)",
        "goal": "Apply $35 fee credit for cust-001",
        "actor": AgentActor(actor_id="agent-alice", role="junior_agent"),
        "approval_response": True,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "apply_fee_credit",
                    "arguments": {
                        "customer_id": "cust-001",
                        "amount_cents": 3500,
                        "reason": "Service concession",
                        "action_id": "demo-act-003",
                    },
                    "explanation": "Proposing $35 credit",
                }
            ),
        ],
    },
    "frozen": {
        "description": "Attempt note update on frozen customer cust-003 (policy denial)",
        "goal": "Add operational note to cust-003",
        "actor": AgentActor(actor_id="agent-bob", role="senior_agent"),
        "approval_response": True,
        "canned_responses": [
            json.dumps(
                {
                    "type": "action",
                    "action_name": "update_customer_note",
                    "arguments": {
                        "customer_id": "cust-003",
                        "note": "Customer contacted support via web chat",
                        "action_id": "demo-act-004",
                    },
                    "explanation": "Appending note",
                }
            ),
        ],
    },
}


async def run_demo(
    scenario_name: str,
    mode: str,
    interactive: bool,
    model: str,
    endpoint: str = "http://localhost:11434",
) -> int:
    if scenario_name not in SCENARIOS:
        print(f"Unknown scenario '{scenario_name}'. Available: {list(SCENARIOS.keys())}")
        sys.exit(1)

    sc = SCENARIOS[scenario_name]
    print("\n" + "=" * 70)
    print("AI Application Architecture — Phase 6 Agentic Execution Demo")
    print("=" * 70)
    print(f"Scenario:    {scenario_name.upper()} — {sc['description']}")
    print(f"Mode:        {mode.upper()}")
    print(
        f"Approval mode: {'Human CLI' if mode == 'live' or interactive else 'Deterministic harness'}"
    )
    print(f"Actor:       {sc['actor'].actor_id} (Role: {sc['actor'].role})")
    print(f"Goal:        {sc['goal']}")
    print("=" * 70 + "\n")

    store = InMemoryCustomerStore()
    registry = CapabilityRegistry()
    registry.register(GetCustomerCapability(store))
    registry.register(GetAccountStatusCapability(store))
    registry.register(SearchPolicyCapability())
    registry.register(UpdateCustomerNoteCapability(store))
    registry.register(ApplyFeeCreditCapability(store))

    policy = CustomerSupportAuthorizationPolicy(store)
    approval_handler: ApprovalPort
    if interactive or mode == "live":
        approval_handler = CliApprovalHandler()
    else:
        approval_handler = DeterministicApprovalHandler(default_approved=sc["approval_response"])

    executor = ToolExecutor()
    llm_client: TextGenerationPort

    if mode == "fake":
        llm_client = ScriptedGenerationStub(sc["canned_responses"])
    else:
        llm_client = OllamaAdapter(
            endpoint=endpoint, default_model=model, timeout_seconds=240.0, max_retries=0
        )

    engine = AgentExecutionEngine(
        llm_client=llm_client,
        registry=registry,
        policy=policy,
        approval_handler=approval_handler,
        executor=executor,
        max_steps=4,
        model=model,
        max_duration_seconds=300.0,
        max_output_tokens=512,
    )

    result = await engine.run(sc["goal"], actor=sc["actor"])

    print("\n" + "-" * 70)
    print("EXECUTION TRAJECTORY AUDIT LOG")
    print("-" * 70)
    for s in result.trace.steps:
        print(f"Step {s.step_number}:")
        print(f"  Decision Type: {s.decision.decision_type.value.upper()}")
        if s.decision.action_name:
            print(f"  Action Name:   {s.decision.action_name}")
            print(f"  Arguments:     {s.decision.arguments}")
        if s.authorization_result:
            auth_str = "ALLOWED" if s.authorization_result.allowed else "DENIED"
            print(f"  Authorization: [{auth_str}] {s.authorization_result.reason}")
        if s.approval_result:
            app_str = "APPROVED" if s.approval_result.approved else "REJECTED"
            print(f"  Approval:      [{app_str}] Approver: {s.approval_result.approver}")
        if s.execution_receipt:
            print(
                f"  Receipt ID:    {s.execution_receipt.action_id} (Status: {s.execution_receipt.status.upper()})"
            )
        print(f"  Step Latency:  {s.step_latency_ms:.1f}ms")
        print()

    print("-" * 70)
    print(f"FINAL OUTCOME:   [{result.status}]")
    print(f"FINAL ANSWER:    {result.final_answer}")
    print(f"TOTAL STEPS:     {result.step_count}")
    print(f"TOTAL RECEIPTS:  {len(result.execution_receipts)}")
    print(f"TOTAL LATENCY:   {result.total_latency_ms:.1f}ms")
    print("=" * 70 + "\n")
    expected = {"denied": "DENIED", "frozen": "DENIED", "mutation-reject": "REJECTED"}.get(
        scenario_name, "COMPLETED"
    )
    if result.status != expected:
        return 1
    if scenario_name in {"read", "multi-read"} and not result.execution_receipts:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 6 Agentic Execution Interactive CLI Demo")
    parser.add_argument(
        "--scenario",
        choices=["read", "multi-read", "mutation-approve", "mutation-reject", "denied", "frozen"],
        default="mutation-approve",
        help="Pre-configured scenario to execute",
    )
    parser.add_argument(
        "--mode", choices=["fake", "live"], default="live", help="Execution mode (fake or live)"
    )
    parser.add_argument(
        "--interactive", action="store_true", help="Prompt human operator on stdin for approvals"
    )
    parser.add_argument("--model", default="qwen2.5:7b", help="Model name for live Ollama mode")
    parser.add_argument(
        "--endpoint", default="http://localhost:11434", help="Ollama daemon HTTP endpoint"
    )

    args = parser.parse_args()
    return asyncio.run(
        run_demo(
            scenario_name=args.scenario,
            mode=args.mode,
            interactive=args.interactive,
            model=args.model,
            endpoint=args.endpoint,
        )
    )


if __name__ == "__main__":
    from ai_telemetry import configure_local_tracing

    configure_local_tracing()
    # Windows redirected output otherwise inherits a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
