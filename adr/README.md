# Architecture Decision Records (ADR) Governance

## 1. Purpose of ADRs

Architectural choices in AI systems frequently involve complex trade-offs between latency, model capabilities, deterministic guarantees, operational costs, and vendor independence.

To maintain an immutable historical record of these decisions, this repository enforces the use of **Architecture Decision Records (ADRs)**. An ADR captures a significant architectural decision along with its context, evaluated alternatives, consequences, and compliance with the repository's core principles.

---

## 2. When to Create an ADR

An ADR is **mandatory** whenever an architectural decision:
* Selects or changes an architectural pattern (e.g., Modular Monolith vs. Event-Driven Microservices).
* Adopts a new foundation model runtime or library (e.g., Ollama vs. vLLM).
* Introduces or alters a core abstraction layer (e.g., `ILlmProvider`, `IVectorStore`).
* Selects a primary database, vector store, message broker, or orchestrator.
* Establishes a cross-cutting security, evaluation, or observability policy.
* Introduces a significant deviation from an existing architectural pattern.

An ADR is **NOT** needed for routine bug fixes, internal refactoring within established interfaces, or standard test additions.

---

## 3. ADR Lifecycle & Statuses

Every ADR transitions through a documented lifecycle:

```
┌──────────┐      ┌──────────┐      ┌────────────┐
│ PROPOSED │ ───► │ ACCEPTED │ ───► │ SUPERSEDED │
└────┬─────┘      └──────────┘      └────────────┘
     │                  │
     ▼                  ▼
┌──────────┐      ┌────────────┐
│ REJECTED │      │ DEPRECATED │
└──────────┘      └────────────┘
```

* **Proposed**: The ADR is drafted and undergoing architectural review.
* **Accepted**: The decision has been approved by the architecture leads and is binding on implementations.
* **Rejected**: The decision was evaluated and rejected. The record is retained for historical context so team members understand why the path was not chosen.
* **Superseded**: A subsequent decision has replaced this ADR. The superseded ADR must explicitly link to the superseding ADR.
* **Deprecated**: The decision is no longer relevant or enforced due to architectural evolution.

---

## 4. File Naming & Numbering Convention

ADRs are stored in this directory (`adr/`) and must follow a sequential numbering scheme:

```text
adr/
├── 0001-record-architecture-decisions.md
├── 0002-adopt-ollama-as-local-runtime.md
├── 0003-hexagonal-architecture-pattern.md
...
```

Format: `NNNN-kebab-case-title.md` (where `NNNN` is a zero-padded 4-digit sequential integer).

---

## 5. Structure of an ADR

All ADRs must be drafted using [template.md](template.md). Fake ADRs or retrospective fabrications for unmade decisions are strictly prohibited.

Every ADR must include:
1. **Context & Problem Statement**: The business and technical context requiring a decision.
2. **Decision Drivers**: Factors influencing the outcome (cost, latency, security, portability).
3. **Options Considered**: Thorough evaluation of viable alternatives.
4. **Decision Outcome**: The chosen path and explicit rationale.
5. **Consequences**: Positive, negative, and neutral trade-offs.
6. **Alternatives Rejected**: Concrete reasons why other options were declined.
7. **Compliance with Principles**: Mapping to [docs/architecture/principles.md](../docs/architecture/principles.md).

---

## 6. ADR Index

| ADR Number | Title | Status | Date |
| :--- | :--- | :--- | :--- |
| *Template* | [ADR Standard Template](template.md) | Standard | 2026-09-14 |
| **[ADR-0001](0001-minimum-core-contracts-and-repository-foundation.md)** | [Minimum Core Contracts & Repository Foundation](0001-minimum-core-contracts-and-repository-foundation.md) | Accepted | 2026-09-14 |
| **[ADR-0002](0002-tiered-reference-implementation-templates.md)** | [Tiered Reference Implementation Templates](0002-tiered-reference-implementation-templates.md) | Accepted | 2026-09-14 |
