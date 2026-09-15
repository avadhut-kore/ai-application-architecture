# ADR-0007: Capability Safety Boundaries and Human-in-the-Loop Approval

* **Status**: Accepted
* **Deciders**: Principal AI Application Architect, Enterprise Governance Auditor, AI Safety Engineer
* **Date**: 2026-09-15
* **Technical Story**: Phase 6 — Agentic Task Execution ([`ROADMAP.md`](../ROADMAP.md#phase-6-agentic-task-execution))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

AI agents that execute operations on behalf of users introduce acute operational risks, including unauthorized transactions, state corruption, infinite execution loops, and prompt injection attacks.

In traditional software, execution authority is governed by caller identity and explicit code paths. In AI agent systems, however, the execution trigger originates from a non-deterministic, probabilistic model. If the application blindly executes whatever tool the model invokes, the model effectively inherits unrestricted root authority over the system.

---

## 2. Problem Statement

What safety boundaries, authorization mechanisms, and approval gates must intervene between a model's proposed tool invocation and its physical execution?

---

## 3. Decision Drivers

* **Zero-Tolerance Safety**: Unapproved state mutations, unauthorized financial disbursements, and bypass of security holds must have zero occurrences.
* **Defense-in-Depth**: No single layer (e.g. system prompt instructions) may be relied upon as the sole defense against adversarial behavior.
* **Non-Delegable Human Agency**: Critical decisions requiring human judgment must require affirmative human authorization.
* **Idempotent Operations**: Network retries or model hallucinations must not cause duplicate execution of side-effect operations.

---

## 4. Key Architectural Decisions

### 4.1 Explicit Capability Classification
Every capability registered in the system must declare its side-effect classification using `SideEffectLevel`:
* `READ_ONLY`: The capability reads data without modifying system state (e.g. `get_customer`, `get_account_status`, `search_policy`). Permissible for automated execution subject to actor RBAC.
* `STATE_MUTATING`: The capability alters system state, modifies data, or initiates transactions (e.g. `update_customer_note`, `apply_fee_credit`).

### 4.2 Multi-Stage Gate Pipeline
Before any tool is executed, the proposal must traverse five mandatory gates in strict sequential order:
1. **Decision Parse Gate**: Untrusted model output is parsed against a strict JSON schema. Malformed outputs are rejected with schema repair observations; two consecutive malformed outputs terminate the loop.
2. **Registry & Schema Gate**: The requested capability must exist in the allowlist registry. All arguments must validate against the capability's declared parameter schema.
3. **Authorization Policy Gate**: The application-controlled policy engine verifies that the initiating `AgentActor` holds permissions for the action and that operational constraints (e.g. $20 role limit, account security hold) are satisfied. The model cannot bypass or modify policy rules.
4. **Human-in-the-Loop Approval Gate**: If `capability.metadata.requires_approval` is `True`, an independent `ApprovalPort` must be invoked. If the approver declines, execution is blocked and the loop terminates with `REJECTED`.
5. **Tool Executor Sandboxing**:
   - **Timeout Guard**: Execution is bounded by an asynchronous timeout (default 10s).
   - **Exception Sandboxing**: Unhandled tool exceptions are caught and wrapped in a failed `ExecutionReceipt` rather than crashing the host process.
   - **Idempotency Cache**: State-mutating capabilities require an `action_id`. Subsequent proposals with an identical `action_id` return the cached execution receipt without re-executing side effects.

### 4.3 Untrusted Observation Framing
All tool outputs returned to the model are enclosed in untrusted data delimiters:
```text
=== BEGIN TOOL OBSERVATION (UNTRUSTED DATA) ===
Tool: <name>
Execution Receipt: <id> (Status: <status>)
Result:
<data>
=== END TOOL OBSERVATION ===
```
This isolates the model context from indirect prompt injections contained within retrieved records.

---

## 5. Consequences

### Positive
* Deterministic mathematical guarantee that unauthorized state mutations cannot occur, even under full model compromise or jailbreak.
* Complete traceability of every action proposal and human approval decision.
* Eliminates double-charging or duplicate mutations through idempotency keys.

### Negative / Trade-offs
* Human-in-the-loop approval introduces operational latency for state-mutating workflows.
* Every capability must maintain an explicit JSON parameter schema and side-effect classification.

---

## 6. Compliance with Repository Principles

* **Principle 1 (System Integrity)**: Models are never granted unmediated access to persistent systems.
* **Principle 13 (Capability Safety & Human Agency Preservation)**: Absolute enforcement of human-in-the-loop authorization for high-impact operations.
