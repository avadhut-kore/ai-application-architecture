# Technology Governance & Evaluation Framework

## 1. Governance Philosophy

In modern AI engineering, new frameworks, vector databases, and model provider libraries emerge weekly. Adopting technologies based on industry hype or popularity creates brittle architectures, severe maintenance overhead, and rapid obsolescence.

This repository enforces a strict **Architectural Evaluation Framework** for all technology decisions:
1. Technologies are evaluated against **architectural requirements**, not popularity.
2. Applications depend on **internal architectural abstractions**, never directly on concrete third-party tools.
3. Every technology must support **local-first execution**, enterprise-grade security, and open standards.

---

## 2. Required Core Architectural Abstractions

Before any external library or service is integrated into this repository, an internal port/interface must be defined in `building-blocks/`. The ten mandatory architectural abstractions are:

```
                               Core Architectural Abstractions
                               
 ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
 │    ILlmProvider      │  │  IEmbeddingProvider  │  │     IVectorStore     │
 │ Complete, Stream,    │  │ Embed Text,          │  │ Similarity Search,   │
 │ Structured Output    │  │ Batch Embeddings     │  │ Filter, Index        │
 └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
 ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
 │        ITool         │  │     IMemoryStore     │  │      IGuardrail      │
 │ Schema Definition,   │  │ Working, Session,    │  │ Pre-Prompt Validate, │
 │ Typed Execute, Audit │  │ Episodic Persistence │  │ Post-Output Validate │
 └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
 ┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
 │    IWorkflowEngine   │  │      IAgentLoop      │  │  IEvaluationHarness  │
 │ Deterministic DAG,   │  │ ReAct, Tool Calling, │  │ Groundedness, Recall,│
 │ State Persistence    │  │ Bounded Execution    │  │ Faithfulness Scoring │
 └──────────────────────┘  └──────────────────────┘  └──────────────────────┘
                           ┌──────────────────────┐
                           │   IObservability     │
                           │ Spans, Token Metric, │
                           │ Latency Tracking     │
                           └──────────────────────┘
```

### Abstraction Specifications

1. **`ILlmProvider`**: Decouples model inference. Must support text generation, chunked streaming, structured JSON schema generation, and token counting. Adapters implement this for Ollama, OpenAI, Azure OpenAI, Anthropic, and vLLM.
2. **`IEmbeddingProvider`**: Computes dense vector representations from text or multimodal inputs with dimension verification and batching.
3. **`IVectorStore`**: Manages vector indexing, similarity search (cosine, dot product), metadata filtering, and partition isolation.
4. **`ITool`**: Defines a callable unit of work. Must expose an immutable JSON schema for arguments, a deterministic execution method, and structured error handling.
5. **`IMemoryStore`**: Manages conversational history and semantic memory across turns. Isolates short-term session state from long-term episodic memory.
6. **`IGuardrail`**: Implements pre-inference scanning (prompt injection detection, PII masking) and post-inference validation (schema compliance, hallucination filtering).
7. **`IWorkflowEngine`**: Coordinates multi-step, deterministic business processes, supporting state persistence, pause/resume, and saga rollbacks.
8. **`IAgentLoop`**: Governs bounded autonomous reasoning loops, enforcing maximum iteration limits, tool permission checks, and cycle detection.
9. **`IEvaluationHarness`**: Automates evaluation scoring for groundedness, context relevance, faithfulness, and schema compliance against curated datasets.
10. **`IObservability`**: Standardizes OpenTelemetry GenAI semantic spans, token counters, latency histograms, and structured diagnostic logging.

---

## 3. Technology Evaluation Matrix

When a new technology, library, or runtime is proposed, it must be scored across the following six architectural criteria (scale 1 to 5):

| Evaluation Criterion | Assessment Question | Weight |
| :--- | :--- | :--- |
| **Local-First Feasibility** | Can this technology run entirely on a standard developer workstation (via Docker / local binary) without requiring commercial internet access or paid licenses? | 25% |
| **Architectural Decoupling** | Does the library allow clean separation via interfaces, or does it force an invasive, framework-wide programming model? | 20% |
| **Enterprise Readiness** | Does it support connection pooling, transactions, authentication, RBAC, high availability, and telemetry? | 20% |
| **Type Safety & Contracts** | Does it offer first-class static typing, explicit schemas, and deterministic serialization? | 15% |
| **Community & Longevity** | Is it backed by open standards, active multi-vendor contributions, and an established release cadence? | 10% |
| **Operational Overhead** | Is the operational and resource footprint justifiable for reference architectures on developer hardware? | 10% |

A technology must achieve a weighted score of **$\ge 4.0 / 5.0$** to be accepted for reference implementations.

---

## 4. Technology Adoption Lifecycle (Radar)

The repository classifies technologies into four explicit lifecycle states:

```
       HOLD          ASSESS          TRIAL          ADOPT
 ┌──────────────┬──────────────┬──────────────┬──────────────┐
 │ Brittle      │ Promising    │ Validated    │ Recommended  │
 │ Frameworks,  │ Emerging     │ Reference    │ Enterprise   │
 │ Vendor Clones│ Standards    │ Patterns     │ Standards    │
 └──────────────┴──────────────┴──────────────┴──────────────┘
```

### 4.1 ADOPT (Standard Enterprise Baseline)
* **Ollama**: Default local foundation model runtime for development and testing.
* **PostgreSQL + pgvector**: Canonical relational and vector storage engine, providing transactional integrity and ACID compliance alongside vector similarity.
* **Redis**: High-performance distributed cache, working session memory store, and rate-limiting coordinator.
* **OpenTelemetry**: Universal standard for distributed tracing, metrics, and GenAI semantic conventions.
* **Docker & Docker Compose**: Universal container runtime for deterministic local execution.
* **Python (3.11+)**: Primary language for AI-native pipelines, evaluation harnesses, and ML integration.
* **.NET (8.0+) / C#**: Enterprise service language for mission-critical APIs, transactional workflows, and enterprise integration.

### 4.2 TRIAL (Validated for Specific Reference Architectures)
* **Qdrant**: Specialized, high-throughput dedicated vector database for large-scale production retrieval workloads.
* **TypeScript / Node.js (20+)**: Full-stack UI frontends, real-time WebSocket voice gateways, and lightweight streaming clients.
* **MinIO**: S3-compatible local object store for document AI and multimodal asset storage.

### 4.3 ASSESS (Under Architectural Evaluation)
* **vLLM / TGI**: High-throughput inference engines evaluated for dedicated self-hosted production GPU clusters.
* **Apache Kafka**: Event streaming backbone evaluated for high-volume asynchronous agentic workflows.
* **Java (21 LTS)**: Enterprise integration patterns in legacy enterprise landscapes.

### 4.4 HOLD (Prohibited / Anti-Patterns)
* **Monolithic Wrapper Frameworks**: Frameworks that obfuscate low-level model interactions behind excessive abstraction layers and rapidly become outdated.
* **Proprietary-Only Vector Clouds**: Vector services that cannot be run locally or require mandatory cloud subscriptions.
* **Single-Vendor SDKs in Core Domain Logic**: Any direct dependency on vendor libraries (`openai`, `anthropic`) outside of designated infrastructure adapter packages.
