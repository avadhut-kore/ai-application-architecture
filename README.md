# AI Application Architecture

[![Architecture First](https://img.shields.io/badge/Architecture-First-blue.svg)](docs/architecture/principles.md)
[![Local First](https://img.shields.io/badge/Policy-Local--First-purple.svg)](docs/architecture/local-first.md)
[![Quality Gates](https://img.shields.io/badge/Quality--Gates-A--J-red.svg)](QUALITY-GATES.md)

An architectural reference standard, taxonomy, and implementation repository for Artificial Intelligence applications.

---

## 1. Purpose & Mission

The purpose of **`ai-application-architecture`** is to establish an architectural foundation for designing, building, evaluating, securing, observing, and operating AI applications in enterprise software environments.

Modern AI engineering frequently suffers from structural anti-patterns: simple prompt scripts marketed as autonomous agents, brittle prompt chains mistaken for deterministic workflows, hardcoded vendor SDKs creating deep lock-in, unobservable model calls, and an absence of formal evaluation harnesses.

This repository exists to replace ad-hoc AI scripting with **disciplined software architecture**.

```text
                           AI Application System Topology

 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Client & Consumption Layer                        │
 │        Web / Mobile UI  │  Enterprise APIs  │  Async Event Triggers     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │                     Application & Workflow Boundary                     │
 │   ┌───────────────────────────────┴────────────────────────────────┐   │
 │   │               Deterministic Orchestration Layer                │   │
 │   │  State Machines │ Saga Coordinators │ Business Rules │ Security │   │
 │   └───────────────┬────────────────────────────────┬───────────────┘   │
 │                   │                                │                   │
 │   ┌───────────────▼──────────────┐ ┌───────────────▼──────────────┐   │
 │   │  Intelligence Patterns       │ │  Enterprise Integrations     │   │
 │   │  RAG │ Tool Agents │ Memory  │ │  ERP │ CRM │ Data Lake │ RDBMS│   │
 │   └───────────────┬──────────────┘ └───────────────┬──────────────┘   │
 └───────────────────┼────────────────────────────────┼───────────────────┘
                     │                                │
 ┌───────────────────▼────────────────────────────────▼───────────────────┐
 │               Architectural Port (ILlmClient / Gateway)                │
 │    Direct Port Interface OR Conditional Model Gateway (Routing/Quotas) │
 └───────────────────┬────────────────────────────────────────────────────┘
                     │
 ┌───────────────────▼────────────────────────────────────────────────────┐
 │                       Provider Execution Layer                         │
 │   Local Runtime (Ollama / vLLM)  │  Cloud Adapters (Azure, OpenAI, GCP)│
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Principles

All implementations in this repository adhere to non-negotiable principles defined in [`docs/architecture/principles.md`](docs/architecture/principles.md):

1. **Model Output Is Untrusted**: All model outputs must be parsed, schema-validated, and sanitized before ingestion.
2. **Deterministic Business Rules Remain Deterministic**: Core business logic and calculations must not depend on probabilistic models.
3. **Provider Decoupling**: Domain logic interfaces with architectural ports, not vendor SDKs.
4. **Model Gateway Is Conditional**: Centralized gateways are introduced only when multi-provider routing, rate limiting, or shared quotas justify them; small apps use direct port adapters.
5. **RAG, Memory, Tools, Agents, and Workflows Are Distinct**: Strict conceptual separation across intelligence and orchestration mechanisms.
6. **Agent Autonomy Must Be Bounded**: Hard caps on iterations, timeouts, token budgets, and tool execution boundaries.
7. **Local-First AI Execution**: Designed for local development and testing under three defined execution modes (Offline Local, Local-First, Cloud-Comparable).
8. **Evaluation Is Mandatory for Probabilistic Behavior**: Automated evaluation harnesses scoring groundedness, relevance, and schema adherence against versioned datasets.

---

## 3. Four Reference Implementation Tiers

To avoid forcing a single monolithic standard across disparate components, this repository defines four distinct tiers in [`docs/architecture/reference-standard.md`](docs/architecture/reference-standard.md):

* **Tier 1 — Reference Application**: Comprehensive end-to-end production architecture with complete specifications, unit tests, evals, threat models, observability, and local docker execution.
* **Tier 2 — Pattern Example**: Focused, runnable demonstration of a single intelligence or architecture pattern without extraneous enterprise plumbing.
* **Tier 3 — Platform Component**: Reusable building block, adapter, or infrastructure capability (e.g., evaluation runner, model routing, guardrail middleware).
* **Tier 4 — Template**: Canonical scaffolding archetypes accelerating development.

---

## 4. Repository Navigation

| Document / Directory | Focus Area | Description |
| :--- | :--- | :--- |
| **[`VISION.md`](VISION.md)** | Strategic Vision | Long-term roadmap, architectural charter, and enterprise differentiation. |
| **[`SCOPE.md`](SCOPE.md)** | Operational Scope | Clear delineation of what is in-scope vs. out-of-scope for the repository. |
| **[`ROADMAP.md`](ROADMAP.md)** | Phased Roadmap | 15-phase delivery plan from Governance (Phase 0) to v1.0 Reference Release. |
| **[`AGENTS.md`](AGENTS.md)** | Agent Constitution | Operating instructions, coding standards, and quality gates for AI coding agents. |
| **[`QUALITY-GATES.md`](QUALITY-GATES.md)** | Quality Gates | Gates A through J establishing objective release criteria for all deliverables. |
| **[`docs/architecture/`](docs/architecture/)** | Architecture Core | Lean, authoritative architectural standards, principles, taxonomy, and policies. |
| **[`docs/engineering/`](docs/engineering/README.md)** | Engineering Standards | Enforceable engineering standards, testing, evaluation, security, and DoD. |
| **[`adr/`](adr/)** | Decision Records | Formal Architecture Decision Records (ADRs) and standardized templates. |

---

## 5. Architectural Standards Index

Consult the authoritative standards in `docs/architecture/`:

* **[Architecture Principles](docs/architecture/principles.md)**: The 14 non-negotiable engineering principles governing all implementations.
* **[Application Taxonomy](docs/architecture/taxonomy.md)**: The 15 application domains, intelligence patterns, architecture patterns, and classification dimensions.
* **[Repository Structure](docs/architecture/repository-structure.md)**: Modular Monorepo layout, zone responsibilities, and dependency rules.
* **[Reference Standards & Tiers](docs/architecture/reference-standard.md)**: Four reference implementation tiers and deliverables matrix.
* **[Local-First AI Policy](docs/architecture/local-first.md)**: The three execution modes (Mode A, B, C) and Ollama runtime governance.
* **[Technology Governance](docs/architecture/technology-governance.md)**: Technology evaluation criteria and Just-in-Time Abstraction Policy.
* **[Programming Language Strategy](docs/architecture/language-strategy.md)**: Role boundaries for Python, .NET, TypeScript, and Java.
* **[Prohibited Anti-Patterns](docs/architecture/anti-patterns.md)**: Catalog of 19 prohibited architectural and AI anti-patterns.

---

## 6. Current Phase Status

Implementation extends through the **Phase 7 Tier 2 single-agent workflow baseline**.
Current verification and independent acceptance are tracked in the
[remediation evidence record](docs/engineering/phase1-7-remediation.md), with scope
owned by [ROADMAP.md](ROADMAP.md) and explained in [ADR-0012](adr/0012-phase1-7-verification-and-local-recovery.md).

### Reproduce the locked environment

```powershell
python -m pip install uv==0.13.9
uv sync --frozen
uv run --frozen python scripts/validate.py
uv run --frozen python scripts/quality.py
```

Deterministic tests require no models or paid API keys. Runtime demos use real
local inference; explicitly selected `--mode fake` runs only verify harnesses.
Follow [local setup](docs/setup/local-ai-environment.md) for model installation.
Generated verification logs are written to `.quality/`; CI retains them as artifacts.
