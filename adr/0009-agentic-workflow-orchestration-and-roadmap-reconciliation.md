# ADR-0009: Agentic Workflow Orchestration & Roadmap Reconciliation

* **Status**: Accepted
* **Deciders**: Principal AI Systems Architect, Enterprise Governance Auditor, AI Platform Lead
* **Date**: 2026-09-15
* **Technical Story**: Phase 7 — Agentic Workflow Orchestration ([`ROADMAP.md`](../ROADMAP.md#phase-7-agentic-workflow-orchestration))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

In early Phase 0 roadmapping, Phase 7 was sketched as a speculative "Tier 1 Multi-Agent Collaborative Workflow Application" featuring distributed state machine orchestration and saga compensation.

During Phase 7 architectural analysis, repository governance ([`AGENTS.md`](../AGENTS.md)) and architecture principles ([`docs/architecture/principles.md`](../docs/architecture/principles.md) — *Principle 4: Architecture Complexity Rule*, *Principle 6: Local-First Principle*, and *Principle 13: Capability Safety & Human Agency Preservation*) mandated that workflow orchestration must coordinate bounded execution with sovereign application control:
1. **North Star Boundary**: Workflow orchestration coordinates agentic execution; it does not replace the Phase 6 agent runtime. The application owns process progression, while the agent owns bounded local reasoning.
2. **Phase Boundary Discipline**: Unconstrained multi-agent swarms negotiating arbitrarily violate Principle 4 when introduced before single-agent workflow orchestration is validated. Single bounded agent coordination must precede multi-agent collaboration.
3. **Artifact Tier Alignment**: Following the governance precedents established in [`ADR-0005`](0005-roadmap-reconciliation-knowledge-intelligence-and-rag.md) and [`ADR-0006`](0006-bounded-agentic-task-execution-and-roadmap-reconciliation.md), foundational orchestration semantics must be proven as a **Tier 2 Pattern Example** (`examples/agentic-workflow`) and **Core Contracts** (`building-blocks/python/contracts/workflow.py`).

---

## 2. Problem Statement

How should Phase 7 reconcile early speculative roadmap notes with enterprise-grade agentic workflow architecture, delivering durable state machine coordination, asynchronous human-in-the-loop checkpoints, and local saga compensation while adhering to 100% offline local-first (Mode A) determinism?

---

## 3. Decision Drivers

* **Separation of Authority**: The host application must retain sovereign authority over business process progression; probabilistic models must never determine workflow graph routing or rewrite execution policy.
* **Hermetic Local-First Execution**: The reference pattern must run completely offline without external network dependencies, third-party cloud services, or paid API keys.
* **Architectural Transparency & Pedagogical Clarity**: Enterprise architects must understand the fundamental mechanics of state machines, checkpoints, optimistic locking, and resumption without proprietary framework obscurity.
* **Minimal Dependency Surface**: For a Tier 2 reference pattern, standard-library implementations (`sqlite3`, `dataclasses`, `asyncio`) minimize supply chain risk and version churn.
* **Verifiable Safety Invariants**: Bounded execution, single-use human approvals, and idempotent state mutations must be verifiable by deterministic test harnesses.

---

## 4. Key Architectural Decisions

### 4.1 Tier 2 Delivery & Roadmap Scope Reconciliation
The Phase 7 scope in [`ROADMAP.md`](../ROADMAP.md#phase-7-agentic-workflow-orchestration) is reconciled to deliver:
1. **Tier 2 Pattern Example (`examples/agentic-workflow`)**:
   - Directed workflow graph / state machine engine with explicit step definitions and transition guards;
   - Single bounded Phase 6 agent integration restricted strictly to read-only capabilities during investigation;
   - Asynchronous Human-in-the-Loop (HITL) pause-to-disk and process-restart resumption;
   - Durable SQLite checkpoint store with optimistic concurrency compare-and-swap (CAS);
   - Stable action identity and durable mutation ledger preventing duplicate side effects across restarts;
   - Local Saga Compensation pattern (linear forward recovery and backward compensating steps);
   - 30-scenario deterministic evaluation suite and separate live local Ollama smoke runner.
2. **Core Contracts (`building-blocks/python/contracts/workflow.py`)**:
   - Provider-neutral domain models and protocols: `WorkflowStatus`, `StepExecutionStatus`, `ApprovalStatus`, `MutationStatus`, `WorkflowDefinitionRef`, and `CheckpointStorePort`.

### 4.2 Framework Selection: Plain Python Standard Library + SQLite
We select **Plain Python (Standard Library `sqlite3`, `dataclasses`, `asyncio`)** over LangGraph and Microsoft Agent Framework:
* *Mode A Alignment*: Mode A ([`docs/architecture/local-first.md`](../docs/architecture/local-first.md)) requires 100% offline execution. While third-party packages do not inherently violate Mode A, Plain Python standard library eliminates external packaging overhead and wheel installation requirements on developer workstations.
* *Transparency*: Directly demonstrates state machines, serialization, and restart resumption from first principles.
* *Portability*: Core primitives map cleanly 1-to-1 onto LangGraph (`StateGraph`) or Temporal (`WorkflowDefinition`) in subsequent enterprise phases.

### 4.3 Explicit Deferred Capabilities
The following capabilities are deliberately excluded from Phase 7:
* Multi-agent collaborative consensus swarms (deferred to Phase 8+);
* Distributed asynchronous event-driven sagas across microservices via message brokers (deferred to Phase 14);
* Distributed workflow engines (Temporal, Camunda, Airflow);
* Production enterprise Identity Provider (IdP) integration;
* Cross-workflow persistent vector memory systems.

---

## 5. Consequences

### Positive
* Zero third-party package dependencies for core workflow execution and SQLite persistence.
* Provable mathematical protection against model-injected workflow transitions.
* Complete restart/resume fidelity across independent OS processes.
* Clear architectural separation between workflow control and agent reasoning.

### Negative / Trade-offs
* Multi-agent negotiation is not demonstrated in Phase 7.
* Distributed multi-service saga rollbacks are not available; Phase 7 implements local linear saga compensation.
* Single-writer SQLite concurrency is suitable for local CLI patterns but requires replacement with PostgreSQL in high-throughput enterprise tiers.

---

## 6. Compliance with Repository Principles

* **Principle 4 (Architecture Complexity Rule)**: Bounded single-agent workflow orchestration before complex multi-agent swarms.
* **Principle 6 (Local-First)**: 100% runnable under Mode A offline without external services.
* **Principle 13 (Capability Safety & Human Agency Preservation)**: Absolute human authorization for high-consequence state mutations.
