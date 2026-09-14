# Operational Scope & Boundaries

## 1. Purpose of Scope Definition

To preserve the integrity, maintainability, and enterprise focus of `ai-application-architecture`, this document establishes immutable boundaries defining what is explicitly **in-scope** and **out-of-scope** across all phases of the repository lifecycle.

Creeping scope, toy experiments, and vendor marketing artifacts dilute architectural clarity. All pull requests, architecture proposals, and future implementations must pass the scope verification criteria outlined herein.

---

## 2. In-Scope Deliverables & Capabilities

The following categories constitute the core charter of this repository:

### 2.1 Enterprise AI Reference Architectures & Implementations
* **Production-Grade Architectures**: Complete, runnable application systems demonstrating clean architecture, separation of concerns, and robust error handling.
* **18 Strategic AI Application Domains**: Implementations systematically addressing the application taxonomy defined in [application-taxonomy.md](docs/architecture/application-taxonomy.md), including RAG, Agentic Workflows, Document AI, Voice/Real-Time, Decision Intelligence, and AIOps.
* **Local-First Executable Systems**: Baseline configurations permitting full execution on local developer workstations using **Ollama** and local open-source dependencies (e.g., PostgreSQL + pgvector, Redis).

### 2.2 Reusable Architectural Abstractions & Building Blocks
* **Provider Abstraction Layer**: Generic, decoupled interfaces for foundation models (LLMs, SLMs), embeddings, vector storage, semantic caches, and tool calling.
* **Model Gateway Patterns**: Resilient middleware addressing authentication, rate limiting, retry backoff, circuit breaking, fallback routing, and token usage accounting.
* **Workflow & State Orchestration**: Deterministic orchestration engines, finite state machines, saga coordinators, and human-in-the-loop validation checkpoints.
* **Agentic Frameworks & Guardrails**: Bounded, inspectable agent execution loops with explicit tool authorization, cycle prevention, and output sanitization.

### 2.3 Quality, Safety, Evaluation & Observability
* **Automated Evaluation Pipelines**: Reproducible test harnesses scoring model outputs on groundedness, context recall, answer faithfulness, and hallucination resistance.
* **End-to-End Distributed Tracing**: OpenTelemetry GenAI semantic convention implementations tracing prompts, completions, retrieval steps, token consumption, and latencies.
* **Security & Threat Models**: Defenses against prompt injection, data exfiltration, unauthorized tool invocation, and insecure output handling mapped to the OWASP Top 10 for LLMs.

### 2.4 Enterprise Cross-Cutting Patterns
* **Multi-Tenancy & Data Isolation**: Segregated vector indices, tenant-aware metadata filtering, and role-based access control (RBAC).
* **Polyglot Architectural Implementations**: Idiomatic implementations in Python (for AI-native patterns), .NET (for enterprise enterprise APIs and services), TypeScript (for full-stack/frontends), and Java (for enterprise integrations).

---

## 3. Explicitly Out-of-Scope

The following items are strictly prohibited from this repository:

| Out-of-Scope Area | Architectural Rationale for Exclusion |
| :--- | :--- |
| **Toy Chatbots & API Wrappers** | Script-level wrappers around vendor APIs that lack domain logic, validation schemas, or tests provide zero enterprise architectural value. |
| **Foundation Model Training from Scratch** | Pre-training raw LLMs from billions of tokens belongs in deep research / ML training repos. This repository focuses on *application architecture* using foundation models. |
| **Monolithic Vendor Lock-In Demos** | Applications engineered specifically to showcase a proprietary closed-source platform or vendor-specific feature set that cannot be abstracted or swapped. |
| **Unbounded Autonomous Agents** | Agents deployed with broad, unmonitored write permissions to public APIs or live databases without human-in-the-loop review, transaction rollback, or circuit breakers. |
| **Mock/Fake Implementations Marketed as Production** | Submitting hardcoded static strings, fake sleeping loops, or simulated mock responses and labeling them as "production reference architectures". |
| **Premature Infrastructure Sprawl** | Provisioning complex Kubernetes clusters, Kafka brokers, or multi-cloud service meshes before an application's architectural requirements objectively demand them. |
| **Framework Favoritism / Hype Chasing** | Rewriting applications merely to chase ephemeral wrapper frameworks without addressing underlying architectural patterns. |

---

## 4. Phase-Specific Boundary Constraints

To prevent premature implementation and maintain phased discipline:

* **Phase 0 (Current)**: Strictly restricted to governance, principles, standards, ADR templates, quality gates, and agent constitutions. **Zero application code, Dockerfiles, or database integrations may be committed.**
* **Phases 1–3**: Foundation layers, engineering tooling, and application templates. No domain business applications until foundations pass Quality Gates A and B.
* **Phases 4–12**: Systematic, one-by-one rollout of reference applications per the roadmap. Each application must be fully evaluated and audited before the next phase opens.

---

## 5. Scope Governance & Enforcement

Any proposed addition to the repository must answer four mandatory gating questions:
1. *Does this represent an enterprise architecture pattern rather than a one-off scripting trick?*
2. *Can this run locally using open-source / Ollama models without commercial API keys?*
3. *Does this include automated testing, evaluation datasets, and observability tracing?*
4. *Is this decoupled from specific underlying model vendors via our abstraction layers?*

If the answer to any of these questions is "No", the deliverable is out-of-scope and will be rejected.
