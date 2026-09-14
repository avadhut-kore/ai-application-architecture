# AI Application Architecture

[![Architecture First](https://img.shields.io/badge/Architecture-First-blue.svg)](#architecture-philosophy)
[![Local First](https://img.shields.io/badge/Local--First-Ollama-purple.svg)](docs/architecture/local-first-ai.md)
[![Provider Agnostic](https://img.shields.io/badge/Design-Provider--Agnostic-green.svg)](docs/architecture/architecture-principles.md)
[![Quality Gates](https://img.shields.io/badge/Quality--Gates-A--J-red.svg)](QUALITY-GATES.md)

An enterprise-grade reference architecture, architectural taxonomy, and production implementation repository for modern Artificial Intelligence applications.

---

## 1. Executive Mission

The mission of **`ai-application-architecture`** is to establish a rigorous, production-grade architectural reference standard for designing, engineering, testing, securing, evaluating, observing, and operating AI applications in modern enterprise environments.

Modern AI engineering suffers from pervasive architectural anti-patterns: toy chat interfaces marketed as autonomous agents, brittle prompt chains mistaken for deterministic workflows, hardcoded vendor SDKs creating deep lock-in, unobservable LLM calls, and a total absence of formal evaluation harnesses. 

This repository exists to replace ad-hoc AI scripting with **disciplined enterprise software architecture**.

```
                           Enterprise AI Application Topology
                           
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Client & Consumption Layer                        │
 │        Web / Mobile UI  │  Enterprise APIs  │  Async Event Triggers     │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
 ┌───────────────────────────────────▼────────────────────────────────────┐
 │                     Application & Workflow Boundary                     │
 │   ┌───────────────────────────────┴────────────────────────────────┐   │
 │   │               Deterministic Orchestration Engine               │   │
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
 │                   Model Gateway & Abstraction Layer                    │
 │    Auth & Tenancy │ Prompt Guardrails │ Caching │ Fallback Routing     │
 └───────────────────┬────────────────────────────────────────────────────┘
                     │
 ┌───────────────────▼────────────────────────────────────────────────────┐
 │                       Provider Execution Layer                         │
 │   Local Runtime (Ollama / vLLM)  │  Cloud Adapters (OpenAI, Azure, GCP)│
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Target Audience

This repository is engineered specifically for:

* **Solution Architects & Enterprise Architects**: Defining organizational AI blueprints, technology selection criteria, and integration boundaries.
* **AI Architects & Technical Architects**: Designing scalable retrieval pipelines, multi-agent coordination protocols, and context memory topologies.
* **Senior Software Engineers & AI Engineers**: Implementing robust, testable, type-safe, and evaluated AI subsystems without vendor lock-in.
* **Engineering Leaders & CTOs**: Assessing the maturity, operational cost, and risk profile of AI application patterns.

---

## 3. Core Architectural Pillars

All implementations within this repository adhere strictly to five foundational pillars:

1. **Architecture First**: No implementation precedes formal requirements, domain modeling, architecture diagrams, and Architecture Decision Records (ADRs).
2. **Local-First AI**: Every reference system must be fully runnable locally without commercial API keys using **Ollama** or compatible local runtimes, while maintaining zero application-level rewrites when deployed to cloud providers.
3. **Provider-Agnostic Core**: Business logic and intelligence patterns depend exclusively on internal architectural abstractions—never directly on vendor SDKs (`openai`, `anthropic`, `google-generativeai`).
4. **Deterministic Boundaries**: Deterministic business logic remains deterministic. Probabilistic model output is treated as untrusted external data subject to strict schema validation and guardrails.
5. **Continuous Evaluation & Observability**: No AI capability is complete without reproducible evaluation datasets, automated scoring (groundedness, relevance, hallucination resistance), OpenTelemetry tracing, and token economics tracking.

---

## 4. Repository Navigation

| Document / Directory | Focus Area | Description |
| :--- | :--- | :--- |
| **[VISION.md](VISION.md)** | Strategic Vision | Long-term roadmap, architectural charter, and enterprise differentiation. |
| **[SCOPE.md](SCOPE.md)** | Operational Scope | Clear delineation of what is in-scope vs. out-of-scope for the repository. |
| **[ROADMAP.md](ROADMAP.md)** | Phased Roadmap | 15-phase delivery plan from Governance (Phase 0) to v1.0 Reference Release. |
| **[AGENTS.md](AGENTS.md)** | Agent Constitution | Operating instructions, coding standards, and quality gates for AI coding agents. |
| **[QUALITY-GATES.md](QUALITY-GATES.md)** | Quality Gates | Gates A through J establishing objective release criteria for all deliverables. |
| **[docs/architecture/](docs/architecture/)** | Architecture Core | Deep architectural specifications, standards, classification models, and principles. |
| **[adr/](adr/)** | Decision Records | Formal Architecture Decision Records (ADRs) and standardized templates. |
| **[docs/](docs/)** | Specialized Domains | Deep-dive domain documentation for AI, Security, Testing, Evaluation, and Observability. |

---

## 5. Architectural Standards Index

Before contributing or inspecting implementations, consult the authoritative architecture standards:

* **[Architecture Principles](docs/architecture/architecture-principles.md)**: The 17 mandatory engineering principles governing all AI implementations.
* **[Repository Structure Standard](docs/architecture/repository-structure.md)**: Directory layout, monorepo boundaries, and code isolation rules.
* **[Four-Dimension Architecture Model](docs/architecture/four-dimension-model.md)**: Taxonomy separating Application Type, Intelligence Pattern, Architecture Pattern, and Production Capability.
* **[Application Taxonomy](docs/architecture/application-taxonomy.md)**: Formal taxonomy across 18 specialized enterprise AI application domains.
* **[Technology Governance](docs/architecture/technology-governance.md)**: Required abstractions, evaluation matrices, and lifecycle statuses (Adopt, Trial, Assess, Hold).
* **[Reference Implementation Contract](docs/architecture/reference-implementation-standard.md)**: Mandatory vs. conditional deliverables for every reference application.
* **[Local-First AI Strategy](docs/architecture/local-first-ai.md)**: Architectural pattern for local execution with Ollama and zero-cloud development.
* **[Cloud & Production Strategy](docs/architecture/cloud-production-strategy.md)**: Local-to-cloud parity, model gateways, and enterprise scaling.
* **[Language Strategy](docs/architecture/language-strategy.md)**: Role boundaries for Python, .NET, TypeScript, and Java across the enterprise landscape.
* **[Architectural Anti-Patterns](docs/architecture/anti-patterns.md)**: 22 critical anti-patterns prohibited across this repository.

---

## 6. Current Phase Status

> [!IMPORTANT]
> **Current Phase: Phase 0 — Vision, Scope & Architecture Governance**  
> In accordance with Phase 0 constraints, **no application code or infrastructure is currently implemented**. This repository is establishing the governance foundation, architectural principles, taxonomies, and quality gates required to support future reference implementations. Consult [ROADMAP.md](ROADMAP.md) for future phase schedules.

---

## 7. Governance & Contribution Rule

All human contributors and AI coding agents must comply with [AGENTS.md](AGENTS.md) and pass all checks defined in [QUALITY-GATES.md](QUALITY-GATES.md). 

**Rule Zero**: No implementation may begin until its requirements, architecture specification, and ADR have been reviewed and approved.
