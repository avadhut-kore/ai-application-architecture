# ADR-0010: Durable State Machine Persistence and Asynchronous Resumability

* **Status**: Accepted
* **Deciders**: Principal AI Systems Architect, Distributed Systems Architect, Reliability Engineer
* **Date**: 2026-09-15
* **Technical Story**: Phase 7 — Agentic Workflow Orchestration ([`ROADMAP.md`](../ROADMAP.md#phase-7-agentic-workflow-orchestration))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

Business workflows in enterprise AI systems frequently span hours or days while awaiting human approval, asynchronous webhook responses, or external business review. Maintaining active execution threads or open in-memory coroutines during prolonged waits is operationally fragile and prone to catastrophic state loss upon server restarts, process crashes, or infrastructure redeployments.

Furthermore, while Phase 6 established tool execution sandboxing and in-memory idempotency caching (`ToolExecutor._idempotency_cache`), in-memory caches are completely destroyed upon process exit. A process restart prior to post-step checkpointing creates a severe failure window where a state mutation could be re-executed, causing duplicate transactions.

---

## 2. Problem Statement

How should Phase 7 implement durable workflow persistence, optimistic concurrency control, crash-consistent resumption, and mutation reconciliation using standard local infrastructure without introducing distributed database clusters or violating local-first (Mode A) requirements?

---

## 3. Decision Drivers

* **Process-Restart Durability**: Workflow execution state, pending approvals, and mutation history must survive complete OS process termination and resume seamlessly in a newly spawned process.
* **Concurrent Resume Protection**: Multiple processes attempting to resume the same workflow instance simultaneously must be deterministically prevented from executing duplicate mutations.
* **Crash-Consistent Reconciliation**: If a process crashes after an external side effect is initiated but before durable success evidence is stored, the system must reconcile state safely rather than blindly re-executing.
* **Accidental Corruption Detection**: Deserialization of persisted state must detect partial disk writes or storage corruption before executing transitions.
* **Zero Infrastructure Overhead**: Persistence must use pure Python standard-library capabilities (`sqlite3`) runnable on any standard developer workstation without background service daemons.

---

## 4. Key Architectural Decisions

### 4.1 SQLite Standard-Library Persistence
We implement `SQLiteWorkflowStore` using standard library `sqlite3` in Write-Ahead Logging (WAL) mode:
* **`workflow_checkpoints`**: Stores serialized `WorkflowState`, monotonic `checkpoint_version`, definition reference, and SHA-256 checksum.
* **`workflow_approvals`**: Persists durable approval records with explicit lifecycle states (`PENDING`, `APPROVED`, `CONSUMED`, `REJECTED`, `EXPIRED`).
* **`workflow_mutation_ledger`**: Records stable action IDs, canonical argument representations, and execution lifecycle statuses (`PLANNED`, `EXECUTION_STARTED`, `EXECUTED`, `FAILED`, `AMBIGUOUS`).
* **`workflow_audit_log`**: Best-effort append-only table recording structured state transition and execution audit events.

### 4.2 Optimistic Concurrency Control (Compare-and-Swap)
To prevent split-brain execution when multiple processes attempt concurrent resumption:
```sql
UPDATE workflow_checkpoints
SET checkpoint_version = :next_version,
    status = 'RUNNING',
    updated_at = :now
WHERE workflow_id = :id
  AND checkpoint_version = :expected_version
  AND status = 'AWAITING_APPROVAL';
```
Exactly one process acquires the transition lock (`rows_affected == 1`). Any competing process receives `rows_affected == 0`, raises `ConcurrentResumeConflictError`, and halts cleanly without executing side effects.

### 4.3 Stable Action Identity & Durable Mutation Ledger
Every state-mutating operation is assigned a deterministic, stable identifier:
```text
action_id = act-{workflow_id}-{step_name}-{sha256(canonical_args)[:16]}
```
Process restarts do not alter this identifier. The mutation ledger tracks in-flight mutations (`EXECUTION_STARTED`). If a crash occurs mid-flight, resumption invokes domain reconciliation (e.g. verifying account ledger balances). If domain evidence confirms execution, the ledger is reconciled to `EXECUTED` without re-running the tool; if unexecuted, it resets to `PLANNED`; if ambiguous, it halts for manual intervention. Blind retries are strictly prohibited.

### 4.4 Checkpoint Corruption Detection
Checkpoints store a SHA-256 hash computed over state attributes. Mismatched checksums trigger `CorruptedCheckpointError` and fail closed.
*Limitation Disclosure*: The checksum detects accidental disk corruption or partial writes. It does not protect against an attacker with direct write access to the SQLite file who can rewrite both data and hash.

---

## 5. Consequences

### Positive
* 100% offline, durable persistence across OS process restarts.
* Complete elimination of double-mutation risks across process crashes through stable action IDs and domain reconciliation.
* Guaranteed race-free resume semantics via atomic SQLite compare-and-swap.
* Clean separation of durable business state from ephemeral LLM reasoning traces.

### Negative / Trade-offs
* Single-writer SQLite limits high-throughput multi-node concurrency; enterprise deployments must replace SQLite with PostgreSQL via the `CheckpointStorePort` protocol.
* Domain reconciliation logic is domain-specific and requires capability-level verification hooks.

---

## 6. Compliance with Repository Principles

* **Principle 6 (Local-First)**: Fully persistent under Mode A without external database engines.
* **Principle 7 (Observability & Auditability)**: Complete append-oriented audit log of all checkpoints, approvals, and mutations.
* **Principle 13 (Capability Safety)**: Strict protection against duplicate state mutations during crash recovery.
