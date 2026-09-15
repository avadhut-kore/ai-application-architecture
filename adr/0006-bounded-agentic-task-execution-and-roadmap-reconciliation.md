# ADR-0006: Bounded Agentic Task Execution & Roadmap Reconciliation

* **Status**: Accepted
* **Deciders**: Principal AI Application Architect, Enterprise Governance Auditor, AI Platform Lead
* **Date**: 2026-09-15
* **Technical Story**: Phase 6 — Agentic Task Execution ([`ROADMAP.md`](../ROADMAP.md#phase-6-agentic-task-execution))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

In early Phase 0 repository roadmapping, Phase 6 was briefly sketched as a speculative "Tier 1 Enterprise Agent" with broad requirements encompassing autonomous multi-step reasoning, external tool execution, and Model Context Protocol (MCP) integrations.

During Phase 6 architectural research and implementation design, repository principles ([`docs/architecture/principles.md`](../docs/architecture/principles.md) — *Principle 4: Architecture Complexity Rule*, *Principle 6: Local-First Principle*, and *Principle 13: Capability Safety & Human Agency Preservation*) mandated that autonomous execution must be approached with extreme architectural discipline:
1. **Separation of Authority**: A probabilistic language model must never be granted direct, unsupervised execution authority. The model proposes actions; the host application deterministically validates schemas, enforces policy authorization, and requests Human-in-the-Loop (HITL) approval.
2. **Phase Boundary Discipline**: Speculative constructs such as multi-agent negotiation swarms, durable workflow engines (Temporal/Camunda), persistent vector memory stores, and autonomous code execution belong strictly to subsequent phases (Phase 7 and beyond).
3. **Artifact Tier Alignment**: Following the precedent set in [`ADR-0005`](0005-roadmap-reconciliation-knowledge-intelligence-and-rag.md), Phase 6 delivers its core capabilities as a **Tier 2 Pattern Example** (`examples/agent-execution`) demonstrating the bounded ReAct loop with HITL safety, and a **Tier 3 Platform Component** (`platform/mcp-adapter`) establishing the provider-neutral MCP JSON-RPC protocol boundary.

---

## 2. Problem Statement

How should Phase 6 reconcile early speculative roadmap notes with enterprise-grade bounded agent architecture, avoiding framework lock-in (LangChain, CrewAI, AutoGen) while guaranteeing 100% offline, local-first (Mode A) determinism?

---

## 3. Decision Drivers

* **Safety & Non-Delegable Human Agency**: High-consequence mutations must remain under human control; models must not authorize themselves.
* **Hermetic Local-First Execution**: The implementation must run completely on developer workstations without paid API keys, external cloud accounts, or third-party package dependencies.
* **Provider Neutrality**: Agent reasoning must consume the established Phase 4 `TextGenerationPort` without hardcoding OpenAI, Anthropic, or proprietary function-calling extensions.
* **Auditable State Transitions**: Every reasoning step, decision, authorization verdict, approval event, and execution receipt must be immutably recorded in an execution trajectory.

---

## 4. Key Architectural Decisions

### 4.1 Roadmap Reconciliation
The Phase 6 roadmap scope in [`ROADMAP.md`](../ROADMAP.md#phase-6-agentic-task-execution) is reconciled to deliver:
1. **Tier 2 Pattern Example (`examples/agent-execution`)**:
   - Bounded reasoning loop with strict `max_steps` ceiling and cycle detection;
   - Strongly typed action proposal schema parsed defensively from model output;
   - In-memory synthetic customer domain with explicit operational and financial constraints;
   - Role-based access control (RBAC) and security hold authorization policies;
   - Mandatory Human-in-the-Loop approval gate for state-mutating operations;
   - Centralized tool executor enforcing execution sandboxing, timeouts, and idempotency by `action_id`;
   - Auditable execution traces without persisting internal chain-of-thought tokens;
   - 32-scenario versioned evaluation dataset measuring zero-tolerance safety invariants.
2. **Tier 3 Platform Component (`platform/mcp-adapter`)**:
   - Standard-library JSON-RPC 2.0 client/server protocol implementation over stdio;
   - `McpCapabilityAdapter` conforming to `CapabilityPort` with strict capability allowlisting;
   - Hermetic unit tests and verification CLI.

### 4.2 Explicit Deferred Capabilities
The following capabilities are deliberately excluded from Phase 6 and deferred to future phases:
* Multi-agent collaboration swarms and negotiation protocols (deferred to Phase 7+);
* Durable workflow orchestration engines such as Temporal or Camunda (deferred to Phase 7+);
* Long-term persistent vector memory stores across sessions (deferred to Phase 7+);
* Dynamic unvetted code execution sandboxes (e.g. Docker/eBPF runtimes);
* Third-party agent frameworks (LangChain, LangGraph, AutoGen, CrewAI).

---

## 5. Consequences

### Positive
* Zero external package dependencies for core agent logic and MCP adapter (100% Python standard library).
* Complete protection against uncontrolled autonomous model actions.
* Verifiable, repeatable automated evaluation in CI via test doubles and live local models (Ollama).
* Clear architectural path for Phase 7 workflow orchestration.

### Negative / Trade-offs
* Full multi-agent orchestration is not available in Phase 6.
* Tool definitions must be registered and schema-defined manually in the host application registry.

---

## 6. Compliance with Repository Principles

* **Principle 4 (Architecture Complexity Rule)**: Bounded single-agent execution before complex multi-agent swarms.
* **Principle 6 (Local-First)**: 100% runnable under Mode A (offline standard library) and Mode B (local Ollama).
* **Principle 13 (Capability Safety & Human Agency Preservation)**: Absolute separation of proposal authority from execution authority.
