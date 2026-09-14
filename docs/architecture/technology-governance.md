# Technology Governance & Abstraction Policy

## 1. Governance Philosophy

In modern AI software engineering, technologies evolve rapidly. Treating any specific library, framework, or database as an eternal architectural standard guarantees premature obsolescence and technical debt.

This repository enforces two core principles for technology management:
1. **Technologies are Reference Choices, Not Eternal Mandates**: Tools (PostgreSQL, Ollama, Redis, Qdrant) are selected to demonstrate working architectural patterns, not as permanent dogma.
2. **Abstractions Are Introduced on Concrete Need**: We strictly prohibit inventing speculative abstraction layers ahead of demonstrable application requirements.

---

## 2. Abstraction Policy: Just-in-Time Ports

> [!CRITICAL]
> **No Speculative Abstractions**  
> We do **not** mandate interfaces such as `IAgentLoop`, `IMemoryStore`, `IWorkflowEngine`, `IVectorStore`, `IGuardrail`, or `IEvaluationHarness` ahead of time in Phase 0.  
> **Abstractions must be introduced only when a concrete application or platform capability proves the architectural necessity.**

### Abstraction Lifecycle Rules
1. **Phase 0 (Governance)**: Establishes the policy. Zero interfaces are implemented.
2. **Phase 2 (Foundations)**: Establishes minimum viable contracts for core model interactions (`ILlmClient`, `IEmbeddingClient`) and telemetry context propagation.
3. **Phases 5+ (Applications)**: Specialized abstractions (e.g., vector indexing, agent execution, workflow compensation) are introduced alongside the specific reference applications that require them.
4. **Leak-Proof Contracts**: When introduced, abstractions must never expose vendor-specific types, exceptions, or connection flags in their signatures.

---

## 3. Technology Evaluation Framework

When selecting a technology for a reference application or platform building block, engineers and architects must evaluate the choice across nine objective architectural criteria:

| Evaluation Criterion | Evaluation Question |
| :--- | :--- |
| **1. Architecture Fit** | Does the technology cleanly decouple via ports and adapters, or does it impose an invasive runtime model? |
| **2. Ecosystem Maturity** | Is the technology backed by active multi-vendor governance, stable semantic versioning, and comprehensive documentation? |
| **3. Maintainability** | Does the codebase benefit from clear type safety, deterministic testing support, and predictable upgrade paths? |
| **4. Performance & Sizing** | Does the component operate within reasonable latency and memory bounds on standard developer workstations? |
| **5. Portability** | Can the component run locally (containerized or native) and transition smoothly to cloud environments? |
| **6. Operational Complexity** | Is the setup and operational overhead proportionate to the architectural value delivered? |
| **7. Security & Compliance** | Does it support least-privilege credentials, network isolation, and zero unauthorized data egress? |
| **8. Cost Model** | Is it open-source or permissively licensed, avoiding mandatory ongoing subscription costs for development? |
| **9. Educational Value** | Does the technology demonstrate a standard industry pattern that architects and engineers can learn from? |

Significant technology selections (e.g., adopting a new vector database engine or inference runtime) must be supported by an Architecture Decision Record in [`adr/`](../../adr/README.md).

---

## 4. Reference Technology Catalog (Non-Mandatory Options)

The following technologies represent evaluated, viable reference choices that may be introduced when justified by application requirements:

* **Inference Runtimes**: Ollama (default local), vLLM (high-throughput GPU serving), llama.cpp (embedded/C++ runtime).
* **Databases & Vector Storage**: PostgreSQL with pgvector (unified transactional and vector storage), Qdrant (dedicated vector search), SQLite (lightweight embedded).
* **Caching & State**: Redis (ephemeral session state, rate limiting, embedding cache).
* **Object Storage**: MinIO (local S3-compatible document and multimodal asset storage).
* **Observability**: OpenTelemetry SDKs, Prometheus, Grafana, Jaeger.
* **Containers**: Docker and Docker Compose for hermetic local bootstrapping.
* **Programming Languages**: Python, .NET (C#), TypeScript, Java.
