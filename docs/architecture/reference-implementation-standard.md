# The Reference Implementation Contract

## 1. Executive Purpose

To ensure that every application in this repository serves as a genuine, enterprise-grade reference architecture, this document defines the **Reference Implementation Contract**.

A code snippet, an unvalidated script, or a simple chatbot wrapper does not constitute a reference implementation. Any application added to `apps/` must satisfy the deliverables and standards established by this contract before it can be merged or marked as complete.

---

## 2. Deliverables Matrix: Mandatory vs. Conditional

Every reference application must satisfy all **Mandatory** deliverables. **Conditional** deliverables are required whenever the application's domain or architectural pattern exercises the corresponding capability:

| Contract Component | Classification | Requirement & Verification Standard |
| :--- | :--- | :--- |
| **README.md** | **Mandatory** | Standardized overview, problem statement, architecture summary, quick start. |
| **Business Problem Statement** | **Mandatory** | Real-world enterprise business context, target personas, and value delivered. |
| **Functional Requirements (FR)** | **Mandatory** | Explicit enumerated list of functional capabilities supported. |
| **Non-Functional Requirements (NFR)** | **Mandatory** | Quantified latency, throughput, token budget, and availability targets. |
| **Architecture Specification** | **Mandatory** | Clean / Hexagonal architecture layer breakdown and component boundaries. |
| **Architecture Diagram** | **Mandatory** | Renderable Mermaid.js diagram illustrating component topology and data flow. |
| **Domain Model & Contracts** | **Mandatory** | Strongly typed domain entities, state machines, and invariants. |
| **API Contracts** | **Mandatory** | Formal OpenAPI / JSON Schema / Protobuf contracts for external interfaces. |
| **Architecture Decision Records** | **Mandatory** | Application-specific ADRs stored or indexed referencing key pattern choices. |
| **Security & Threat Model** | **Mandatory** | STRIDE or OWASP Top 10 for LLMs threat assessment and mitigations. |
| **Configuration Standard** | **Mandatory** | `.env.example` template with strict type validation at boot (zero secrets committed). |
| **Clean Source Code** | **Mandatory** | Idiomatic, modular, strictly typed code adhering to SOLID and Clean Architecture. |
| **Unit Test Suite** | **Mandatory** | Deterministic unit tests using in-memory test doubles ($\ge 85\%$ coverage). |
| **Integration Test Suite** | **Mandatory** | End-to-end integration tests verifying execution with local Ollama and DB. |
| **AI Evaluation Harness** | **Mandatory** | Automated eval scoring groundedness, relevance, faithfulness, and schema adherence. |
| **Evaluation Dataset** | **Mandatory** | Curated, versioned `eval_dataset.jsonl` with $\ge 30$ representative scenarios. |
| **OpenTelemetry Tracing** | **Mandatory** | GenAI semantic spans for prompts, completions, embeddings, and tool calls. |
| **Metrics & Structured Logging** | **Mandatory** | Contextual JSON logs and Prometheus metrics for TTFT, latency, and tokens. |
| **Resilience & Error Handling** | **Mandatory** | Circuit breakers, retries with exponential backoff, and graceful degradation. |
| **Local Docker Execution** | **Mandatory** | Fully functional `docker-compose.yml` running locally against Ollama. |
| **Demo Instructions** | **Mandatory** | Step-by-step verification script allowing execution in $< 5$ minutes. |
| **Trade-offs & Limitations** | **Mandatory** | Explicit documentation of architectural compromises and known boundaries. |
| **Human-in-the-Loop (HITL)** | *Conditional* | Mandatory for systems executing state mutations or financial transactions. |
| **Streaming / WebSockets** | *Conditional* | Mandatory for real-time voice, conversational chat, or interactive UI apps. |
| **Multi-Tenancy Partitioning** | *Conditional* | Mandatory for multi-user knowledge bases or shared enterprise services. |
| **Production Deployment Manifests** | *Conditional* | Kubernetes Helm charts or cloud infrastructure modules (Phases 12+). |

---

## 3. Detailed Component Standards

### 3.1 Documentation & Specification
* **`README.md`**: Must begin with a 1-page executive summary, followed by the Four-Dimension classification, quick start instructions, and links to detailed specifications.
* **`architecture.md`**: Detailed deep-dive containing Mermaid sequence and component diagrams, showing exact boundaries between domain logic, workflow orchestration, and external adapters.
* **`threat-model.md`**: Evaluation of potential attack vectors: prompt injection, indirect context contamination, tool misuse, and data exfiltration.

### 3.2 Source Code Architecture
Reference applications must follow Hexagonal / Clean Architecture:

```text
src/
├── domain/                  # 1. Domain Layer (Zero external dependencies)
│   ├── entities/            # Enterprise business objects & invariants
│   ├── exceptions/          # Domain-specific exception hierarchy
│   └── value_objects/       # Immutable value types
│
├── application/             # 2. Application Layer (Use cases & workflows)
│   ├── commands/            # State-mutating commands & handlers
│   ├── queries/             # Data retrieval queries & handlers
│   ├── ports/               # Outbound port interfaces (ILlmProvider, etc.)
│   └── workflows/           # Deterministic state machine orchestrators
│
└── infrastructure/          # 3. Infrastructure Layer (Adapters & frameworks)
    ├── api/                 # REST, GraphQL, or WebSocket controllers
    ├── persistence/         # Database repositories (PostgreSQL, Redis)
    └── providers/           # Outbound adapters implementing application ports
```

### 3.3 Testing & Evaluation Contracts
Every reference application must provide two distinct test gates:
1. **Deterministic Software Tests (`tests/`)**:
   * Runs in milliseconds.
   * Completely independent of active network connections or running models.
   * Exercises all state transitions, validators, and error handlers.
2. **Probabilistic AI Evaluations (`eval/`)**:
   * Evaluates system performance against real local models (Ollama).
   * Runs `eval_runner.py` against `eval_dataset.jsonl`.
   * Automatically asserts quality thresholds ($\text{Groundedness} \ge 0.85$, $\text{Schema Adherence} \ge 98\%$).

### 3.4 Local Developer Ergonomics
* Developers must be able to boot the complete environment with:
  ```bash
  cd apps/<app-name>
  docker compose up -d
  task demo # or ./scripts/demo.sh
  ```
* The demonstration must execute without prompting the user for external API keys or cloud subscriptions.

---

## 4. Contract Compliance Checklist

Before an application can be accepted into `apps/`, the following verification checklist must be signed off:

- [ ] Four-Dimension Model classification documented in `README.md`.
- [ ] Hexagonal directory structure implemented; zero vendor SDK imports in `domain/` or `application/`.
- [ ] All inputs and outputs validated with strict schemas (Pydantic / Zod / C# records).
- [ ] Unit test coverage $\ge 85\%$ verified via automated test runner.
- [ ] Evaluation harness executes successfully against local Ollama runtime.
- [ ] OpenTelemetry GenAI semantic conventions verified in emitted trace spans.
- [ ] Local execution verified via `docker-compose.yml` on a clean workstation.
- [ ] Threat model and architectural trade-offs explicitly documented.
