# Operational Scope & Boundaries

## 1. Purpose of Scope Definition

To preserve architectural integrity and avoid maintenance collapse, this document defines the explicit **in-scope** and **out-of-scope** boundaries for the **`ai-application-architecture`** repository.

---

## 2. In-Scope Deliverables & Capabilities

### 2.1 Reference Architectures & Implementations
* **15 Strategic Application Domains**: Implementations systematically addressing the application taxonomy defined in [`docs/architecture/taxonomy.md`](docs/architecture/taxonomy.md), including Conversational Systems, Knowledge Intelligence, Document Intelligence, Agentic Task Execution, and Workflow Orchestration.
* **Tiered Reference Implementations**: Categorized according to the four tiers defined in [`docs/architecture/reference-standard.md`](docs/architecture/reference-standard.md) (Tier 1 Reference Applications, Tier 2 Pattern Examples, Tier 3 Platform Components, Tier 4 Templates).
* **Three-Mode Local-First Execution**: Support for Mode A (Offline Local), Mode B (Local-First, default), and Mode C (Cloud-Comparable) as specified in [`docs/architecture/local-first.md`](docs/architecture/local-first.md).

### 2.2 Reusable Architectural Abstractions & Building Blocks
* **Early Minimum Core Contracts**: Phase 2 delivery of mandatory minimum viable contracts (model client port, telemetry context, base evaluation result, and structured schema validation/error contracts) as authoritatively specified in [`ROADMAP.md`](ROADMAP.md).
* **Just-in-Time Ports**: Introducing specialized abstractions (vector storage, agent execution loops) only when concrete application requirements justify them.
* **Conditional Model Gateway**: Standalone or middleware gateway patterns introduced only when multi-provider routing, rate limiting, or shared quotas demand centralized management.

### 2.3 Quality, Safety, Evaluation & Observability
* **Automated Evaluation Pipelines**: Versioned evaluation datasets (`eval_dataset.jsonl`) scoring groundedness, context relevance, faithfulness, and schema adherence.
* **Distributed Tracing**: OpenTelemetry GenAI semantic conventions tracing model invocations, retrieval steps, latencies, and token expenditures.
* **Security & Threat Models**: STRIDE and OWASP Top 10 for LLMs threat analysis, input sanitization, and least-privilege tool execution controls.

---

## 3. Explicitly Out-of-Scope

The following items are strictly excluded from this repository:

| Out-of-Scope Item | Architectural Rationale for Exclusion |
| :--- | :--- |
| **Toy Chatbots & API Wrappers** | Trivial scripts that make raw vendor API calls without domain logic, validation schemas, or tests provide zero architectural value. |
| **Foundation Model Training from Scratch** | Pre-training raw LLMs belongs in machine learning research repositories; this repository focuses on AI software application architecture. |
| **Vendor-Locked Monolithic Demos** | Applications engineered specifically to showcase proprietary platform features that cannot be decoupled or swapped via ports and adapters. |
| **Unbounded Autonomous Agents** | Agents deployed with open-ended `while True` loops, unrestricted database write access, or unmonitored external tool execution. |
| **Fake / Simulated Production Behavior** | Hardcoding static return strings or fake sleep loops in production paths to pretend AI inference occurred. |
| **Premature Infrastructure Sprawl** | Provisioning Kubernetes clusters, service meshes, or distributed brokers before an application's non-functional requirements justify them. |
| **Documentation Sprawl & Placeholder Demos** | Creating empty directories full of placeholder README files or generating boilerplate without working code. |

---

## 4. Phase 0 Boundary Constraint

In accordance with Phase 0 governance rules:
* **Zero Application Code**: No RAG pipelines, chat interfaces, agents, workflows, or document AI code may be committed in this phase.
* **Zero Infrastructure Deployments**: No Docker environments, Ollama runtime installations, databases, or vector stores are deployed in this phase.
* **Governance Foundation Only**: Phase 0 delivers the architectural constitution, principles, taxonomy, quality gates, and roadmap that govern all future development.
