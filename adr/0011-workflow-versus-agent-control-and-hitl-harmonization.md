# ADR-0011: Workflow versus Agent Control and Human-in-the-Loop Harmonization

* **Status**: Accepted
* **Deciders**: Principal AI Systems Architect, Application Security Architect, AI Safety Engineer
* **Date**: 2026-09-15
* **Technical Story**: Phase 7 — Agentic Workflow Orchestration ([`ROADMAP.md`](../ROADMAP.md#phase-7-agentic-workflow-orchestration))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

When introducing workflow orchestration around agentic task execution, a fundamental control ambiguity arises: *Where does authority belong?*

If a language model in an agentic step is permitted to emit workflow transitions (e.g. `next_step: "FINALIZE"` or `goto: "ADMIN_OVERRIDE"`), the model usurps control over the business process, defeating deterministic workflow governance.

Furthermore, Phase 6 established capability-level Human-in-the-Loop (HITL) approval checks inside the synchronous `AgentExecutionEngine` loop. In Phase 7, however, human approvals must pause asynchronously, survive process restarts, and resume hours or days later. If the workflow-level approval bypasses or desynchronizes from Phase 6 execution controls, severe security vulnerabilities (privilege escalation, approval replay, argument substitution) are introduced.

---

## 2. Problem Statement

How should Phase 7 establish sovereign application authority over workflow transitions while safely delegating bounded problem-solving to a Phase 6 agent, and how should asynchronous workflow-level approvals harmonize with Phase 6 capability execution?

---

## 3. Decision Drivers

* **Sovereign Application Authority**: Workflow transitions, stage progression, and terminal states must be deterministically governed by code-defined rules, not model hallucinations.
* **Separation of Proposal from Execution**: Probabilistic agents must never directly execute state mutations during problem investigation.
* **Seven-Point Approval Binding**: Human approvals must strictly bind to workflow identity, definition version, stable action ID, capability name, canonical arguments, actor identity, and non-expired status.
* **Time-of-Check / Time-of-Use (TOCTOU) Defense**: Changes in actor privileges or resource security holds during prolonged approval pauses must be caught before mutation execution.
* **Replay Protection**: An approval token must be single-use and transition to `CONSUMED` upon verified physical execution.

---

## 4. Key Architectural Decisions

### 4.1 Read-Only Agentic Investigation Boundary
The `AgenticInvestigationStep` passes a `CapabilityRegistry` containing **strictly read-only capabilities** (`get_customer`, `get_account_status`, `search_policy`) to the Phase 6 `AgentExecutionEngine`.
*Mutating capabilities (`update_customer_note`, `apply_fee_credit`) are strictly excluded from the investigation registry.*
The agent returns an untrusted diagnostic text which is parsed into a typed `RemediationProposal`. The agent cannot execute mutations or prompt for approval during investigation.

### 4.2 Application-Controlled Transition Mapping
The workflow definition defines deterministic transition rules matching on `RemediationType` (`INFORMATIONAL`, `CUSTOMER_NOTE`, `FEE_CREDIT`, `SECURITY_ESCALATION`).
The model is strictly prohibited from emitting workflow node names. Unrecognized proposals abort to `FAILED`.

### 4.3 Pre-Execution Approval Verification (`WorkflowApprovalVerifier`)
Because Phase 6 `ToolExecutor` performs zero approval checks (approval lived in `AgentExecutionEngine` in Phase 6), the deterministic `MUTATION_EXECUTION` step explicitly performs pre-execution verification:
```text
Resume
  ↓
Revalidate Actor Authorization (Policy check)
  ↓
WorkflowApprovalVerifier.verify_approval(...)
  - 1. record.status == ApprovalStatus.APPROVED
  - 2. record.workflow_id == expected_workflow_id
  - 3. record.action_id == expected_action_id
  - 4. record.capability_name == capability.name
  - 5. record.canonical_arguments_json == canonicalize(args)
  - 6. record.actor_id == actor.actor_id and role == actor.role
  - 7. not expired
  ↓
Ledger.record_intent(action_id, EXECUTION_STARTED)
  ↓
ToolExecutor.execute_tool(capability, canonical_args, action_id)
  ↓
Atomic Commit: Ledger.status = EXECUTED, Approval.status = CONSUMED
```

### 4.4 Local Saga Compensation Pattern
If a multi-step mutation sequence encounters a permanent downstream failure (e.g. note appended, but fee credit disbursement fails permanently), the state machine routes to `COMPENSATE_MUTATION`.
The compensating step deterministically executes the inverse action (appending a voiding note) and records auditable compensation receipts.

---

## 5. Consequences

### Positive
* Mathematical guarantee that models cannot force arbitrary workflow transitions.
* Zero mutation risk during agent investigation.
* Complete protection against approval replay, argument tampering, and TOCTOU privilege drift.
* Deterministic backward compensation restores consistency upon partial multi-step failure.

### Negative / Trade-offs
* State mutations must be explicitly modeled in dedicated workflow steps rather than autonomously discovered by the agent loop.
* Compensating actions must be manually defined for each reversible capability.

---

## 6. Compliance with Repository Principles

* **Principle 1 (System Integrity)**: Models are never granted unmediated or unvalidated execution authority.
* **Principle 13 (Capability Safety & Human Agency Preservation)**: Human judgment governs state mutations through strictly bound, single-use approval records.
