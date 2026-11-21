#!/usr/bin/env python3
"""Live local smoke verification for Phase 7 Agentic Workflow Orchestration.

Executes live workflow scenarios integrating real local Ollama with Phase 6 AgentExecutionEngine
over strictly read-only capabilities. Verifies that the workflow orchestrates live model reasoning
while retaining sovereign deterministic control over state machine routing.

If Ollama daemon is unreachable or models are missing:
Outputs 'STATUS: NOT VERIFIED' and exits non-zero (or exits 0 if --allow-unverified is passed).
Never substitutes fake/scripted stubs in live mode.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUILDING_BLOCKS_DIR = REPO_ROOT / "building-blocks" / "python"
AGENT_EXEC_DIR = REPO_ROOT / "examples" / "agent-execution"
OLLAMA_ADAPTER_DIR = REPO_ROOT / "platform" / "ollama-adapter"
WORKFLOW_DIR = Path(__file__).resolve().parent

for p in (BUILDING_BLOCKS_DIR, AGENT_EXEC_DIR, OLLAMA_ADAPTER_DIR, WORKFLOW_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from agent.approval import DeterministicApprovalHandler
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
from contracts.agent import AgentActor
from contracts.workflow import WorkflowStatus
from ollama_adapter.adapter import OllamaAdapter
from workflow.engine import WorkflowEngine
from workflow.remediation_workflow import build_customer_remediation_workflow
from workflow.state import WorkflowActorSnapshot, REMEDIATION_PROPOSAL_SCHEMA
from workflow.store import SQLiteWorkflowStore


async def run_live_smoke(
    endpoint: str = "http://localhost:11434",
    model_name: str = "qwen2.5:7b",
    allow_unverified: bool = False,
) -> int:
    print("=" * 70)
    print("PHASE 7 LIVE LOCAL OLLAMA SMOKE VERIFICATION")
    print("=" * 70)
    print(f"Target Endpoint:  {endpoint}")
    print(f"Target Model:     {model_name}")
    print(f"Allow Unverified: {allow_unverified}\n")

    # 1. Health check & provider verification
    adapter = OllamaAdapter(endpoint=endpoint, timeout_seconds=10.0)
    is_healthy = await adapter.check_health()

    if not is_healthy:
        print("=" * 70)
        print("STATUS: NOT VERIFIED")
        print(f"Reason: Ollama daemon is unreachable at '{endpoint}'.")
        print(
            "Note: In offline environments or CI without local GPU/Ollama, live verification is skipped."
        )
        print("      To run live verification, start Ollama locally (`ollama serve`).")
        print("=" * 70)
        return 0 if allow_unverified else 1

    installed_models = await adapter.get_installed_models()
    print("Ollama Daemon: Reachable (HTTP 200 OK)")
    print(f"Installed Models: {installed_models if installed_models else 'None'}")

    matched_model: Optional[str] = None
    for m in installed_models:
        if m == model_name or m.startswith(f"{model_name}:"):
            matched_model = m
            break

    if not matched_model:
        print("\n" + "=" * 70)
        print("STATUS: NOT VERIFIED")
        print(f"Reason: Required model '{model_name}' is not installed in local Ollama.")
        print(f"Installed models: {installed_models}")
        print(f"Resolution: Run `ollama pull {model_name}` to install.")
        print("=" * 70)
        return 0 if allow_unverified else 1

    effective_model = matched_model
    print(f"Using Model:   {effective_model}\n")

    # 2. Setup isolated store and live components
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "live_smoke.db")
        customer_store = InMemoryCustomerStore()
        auth_policy = CustomerSupportAuthorizationPolicy(store=customer_store)
        sqlite_store = SQLiteWorkflowStore(db_path)

        read_only_caps = [
            GetCustomerCapability(customer_store),
            GetAccountStatusCapability(customer_store),
            SearchPolicyCapability(),
        ]
        read_only_registry = CapabilityRegistry(read_only_caps)
        credit_cap = ApplyFeeCreditCapability(customer_store)
        note_cap = UpdateCustomerNoteCapability(customer_store)
        executor = ToolExecutor()

        # Build real Phase 6 AgentEngine wired to local Ollama and READ-ONLY tools
        live_agent_engine = AgentExecutionEngine(
            llm_client=OllamaAdapter(
                endpoint=endpoint,
                default_model=effective_model,
                timeout_seconds=240.0,
                max_retries=0,
            ),
            registry=read_only_registry,
            policy=auth_policy,
            approval_handler=DeterministicApprovalHandler(default_approved=True),
            executor=executor,
            max_steps=4,
            model=effective_model,
            max_duration_seconds=300.0,
            max_output_tokens=512,
            final_answer_schema=REMEDIATION_PROPOSAL_SCHEMA,
        )

        workflow_def = build_customer_remediation_workflow(
            customer_store=customer_store,
            agent_engine=live_agent_engine,
            read_only_registry=read_only_registry,
            credit_capability=credit_cap,
            note_capability=note_cap,
            tool_executor=executor,
            workflow_store=sqlite_store,
            actor_resolver=lambda identity: (
                AgentActor(identity, "senior_agent") if identity == "live_operator_1" else None
            ),
            auth_policy=auth_policy,
        )

        workflow_engine = WorkflowEngine(definition=workflow_def, store=sqlite_store)
        actor = WorkflowActorSnapshot(actor_id="live_operator_1", role="senior_agent")

        print("-" * 70)
        print("Scenario 1: Live Read-Only Account Status Investigation")
        print("-" * 70)
        s1_start = time.perf_counter()

        state_1 = await workflow_engine.start_workflow(
            workflow_id="wf-live-001",
            actor=actor,
            domain_context={
                "customer_id": "cust-001",
                "inquiry": "What is the current status and account balance for customer cust-001?",
            },
        )
        s1_dur = (time.perf_counter() - s1_start) * 1000.0

        print(f"Workflow ID:      {state_1.workflow_id}")
        print(f"Terminal Status:  {state_1.status.value.upper()}")
        print(f"Current Step:     {state_1.current_step}")
        print(f"Duration:         {s1_dur:.1f}ms")
        print(f"Steps Executed:   {[h.step_name for h in state_1.history]}")
        if state_1.status != WorkflowStatus.COMPLETED:
            print(
                f"Failure evidence: {[(h.outcome_type, h.error_message) for h in state_1.history]}"
            )
            print("STATUS: FAILED — read-only scenario did not complete")
            return 1

        # Invariant checks for live run:
        # 1. Zero mutations occurred during read-only investigation
        acc_1 = customer_store.get_account("cust-001")
        assert acc_1 is not None
        if acc_1.credits_applied_cents != 0 or len(acc_1.notes) != 1:
            print("SECURITY BREACH: Financial mutation executed during read-only investigation!")
            return 1
        print("PASS: Investigation remained strictly read-only (0 financial mutations).")

        print("\n" + "-" * 70)
        print("Scenario 2: Live Overdraft Dispute & Concession Reasoning")
        print("-" * 70)
        s2_start = time.perf_counter()

        state_2 = await workflow_engine.start_workflow(
            workflow_id="wf-live-002",
            actor=actor,
            domain_context={
                "customer_id": "cust-001",
                "inquiry": "Customer experienced a bank system outage and disputes a recent $10 fee.",
            },
        )
        s2_dur = (time.perf_counter() - s2_start) * 1000.0

        print(f"Workflow ID:      {state_2.workflow_id}")
        print(f"Current Status:   {state_2.status.value.upper()}")
        print(f"Current Step:     {state_2.current_step}")
        print(f"Duration:         {s2_dur:.1f}ms")
        print(f"Steps Executed:   {[h.step_name for h in state_2.history]}")
        if state_2.status != WorkflowStatus.AWAITING_APPROVAL:
            print("STATUS: FAILED — credit scenario did not request approval")
            return 1
        proposal = state_2.domain_context.get("remediation_proposal", {})
        if (
            proposal.get("proposal_type") != "fee_credit"
            or proposal.get("suggested_arguments", {}).get("amount_cents") != 1000
        ):
            print("STATUS: FAILED — proposal does not match the disputed $10 fee")
            return 1
        before_approval = customer_store.get_account("cust-001")
        if (
            before_approval is None
            or before_approval.credits_applied_cents != 0
            or len(before_approval.notes) != 1
        ):
            print("STATUS: FAILED — mutation occurred before approval")
            return 1

        # If it reached awaiting_approval (the model proposed fee credit), test resume!
        if state_2.status == WorkflowStatus.AWAITING_APPROVAL:
            print(
                "\nModel generated a valid fee credit proposal! Testing operator approval resume..."
            )
            state_2_resumed = await workflow_engine.resume_workflow(
                workflow_id="wf-live-002",
                decision="approved",
                approver_id="manager_live_eval",
                reason="Live smoke verified concession",
            )
            print(f"Resumed Status:   {state_2_resumed.status.value.upper()}")
            if state_2_resumed.status != WorkflowStatus.COMPLETED:
                print("STATUS: FAILED — approved mutation did not complete")
                return 1
            print(f"Current Step:     {state_2_resumed.current_step}")
            final_account = customer_store.get_account("cust-001")
            if final_account is None:
                print("STATUS: FAILED — durable domain account is missing")
                return 1
            if final_account.credits_applied_cents != 1000 or final_account.balance_cents != 16000:
                print("STATUS: FAILED — approved business effect does not match $10 credit")
                return 1
            print(f"Final Balance:    ${final_account.balance_cents / 100:.2f}")

        print("\n" + "=" * 70)
        print("STATUS: VERIFIED")
        print(f"Local Ollama provider '{effective_model}' successfully executed live reasoning.")
        print("Read-only investigation invariant and workflow state sovereignty preserved.")
        print("=" * 70)
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Live Local Ollama Smoke Verification for Phase 7")
    parser.add_argument(
        "--endpoint", type=str, default="http://localhost:11434", help="Ollama API endpoint"
    )
    parser.add_argument("--model", type=str, default="qwen2.5:7b", help="Ollama model name")
    parser.add_argument(
        "--allow-unverified", action="store_true", help="Exit 0 even if daemon is unreachable"
    )
    args = parser.parse_args()

    exit_code = asyncio.run(
        run_live_smoke(
            endpoint=args.endpoint,
            model_name=args.model,
            allow_unverified=args.allow_unverified,
        )
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    from ai_telemetry import configure_local_tracing

    configure_local_tracing()
    # Windows redirected output otherwise inherits a legacy code page.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
