# Enterprise Quality Gates (Gates A through J)

To ensure that every contribution and reference implementation meets enterprise production standards, all deliverables must pass the ten objective **Quality Gates** defined in this document. 

No application, pull request, or architecture phase may be considered complete or marked as "Ready" if any mandatory gate fails.

---

## Quality Gate Matrix

| Gate | Category | Objective Focus | Verification Mechanism |
| :--- | :--- | :--- | :--- |
| **Gate A** | Architecture & Design | Hexagonal boundaries, ADRs, 4D alignment | Architectural Review & Linting |
| **Gate B** | Code Quality | Clean code, strict typing, zero duplication | Static Analysis, Type Checkers |
| **Gate C** | Software Testing | Unit, integration, scenario tests | Automated Test Runners (`pytest`, `dotnet test`) |
| **Gate D** | AI Evaluation | Groundedness, relevance, schema adherence | Automated Eval Harness (`eval_dataset.jsonl`) |
| **Gate E** | Security & Safety | OWASP Top 10 for LLMs, secrets, RBAC | Security Scanners (`bandit`, `trivy`, `semgrep`) |
| **Gate F** | Observability | OpenTelemetry tracing, metrics, logs | Telemetry Spans & Prometheus Validation |
| **Gate G** | Performance & Sizing | Latency, TTFT, token consumption, memory | Benchmark Harness, Hardware Profiling |
| **Gate H** | Documentation | Complete reference contract, diagrams | Markdown Lint, Link Validation, Review |
| **Gate I** | Demo & Local Run | Local execution via Ollama without API keys | Docker Compose & CLI Demo Verification |
| **Gate J** | Production Readiness | Resilience, graceful degradation, rollback | Fault Injection & Chaos Testing |

---

## Gate A: Architecture & Design

* **A.1 Hexagonal Separation**: Domain business rules must have zero dependency on frameworks, databases, or LLM provider SDKs. Verified by import dependency inspection.
* **A.2 Four-Dimension Model Alignment**: The system must be explicitly classified across all four dimensions (Application Type, Intelligence Pattern, Architecture Pattern, Production Capability) per [four-dimension-model.md](docs/architecture/four-dimension-model.md).
* **A.3 Architecture Decision Records**: Every major structural decision or pattern selection must have an approved ADR in `adr/` following [adr/template.md](adr/template.md).
* **A.4 Provider Decoupling**: Application must depend strictly on `ILlmProvider` or `IModelGateway`, never on vendor packages (`openai`, `anthropic`, etc.).

---

## Gate B: Code Quality

* **B.1 Strict Static Typing**:
  * Python: `mypy --strict` with zero type errors.
  * .NET: Zero compiler warnings (`<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`).
  * TypeScript: Zero `tsc --noEmit` errors with `"strict": true`.
* **B.2 Linting & Formatting**: Clean run of configured linters (`ruff`, `dotnet format`, `eslint`) with zero rule violations.
* **B.3 Complexity & Maintainability**: Cyclomatic complexity per function must not exceed 10. No duplicated logic or copy-pasted provider blocks.
* **B.4 Structured Output Schemas**: All model responses must be parsed into strongly typed domain models using Pydantic, Zod, or C# records.

---

## Gate C: Software Testing

* **C.1 Unit Test Coverage**: Minimum **85% statement coverage** across domain logic, workflow state machines, and data mappers.
* **C.2 Deterministic Test Execution**: Unit tests must execute in isolation using in-memory test doubles without requiring live network access or active LLM endpoints.
* **C.3 Integration Testing**: Integration test suite verifying end-to-end wiring with local Ollama, vector stores, and relational databases.
* **C.4 Scenario / Boundary Testing**: Explicit test cases covering context overflow, malformed JSON responses, rate limits, and network timeout errors.

---

## Gate D: AI Evaluation

* **D.1 Evaluation Dataset**: Application must include a versioned, curated evaluation dataset (`eval_dataset.jsonl`) containing minimum 30 representative test prompts with reference contexts.
* **D.2 Groundedness & Faithfulness**: Automated evaluation score must achieve:
  * **Faithfulness / Groundedness** $\ge 0.85$ (answer relies strictly on context).
  * **Context Relevance** $\ge 0.80$ (retrieved chunks are pertinent to query).
* **D.3 Schema Adherence Rate**: Minimum **98% valid schema adherence** across evaluation iterations without unhandled parsing exceptions.
* **D.4 Hallucination & Negative Testing**: Evaluation suite must include negative test cases (unanswerable questions) where the model must abstain or report lack of context rather than fabricate answers.

---

## Gate E: Security & Safety

* **E.1 Secret Zero-Tolerance**: Zero committed API keys, secrets, or passwords. Scanned and verified using `gitleaks` or equivalent automated pre-commit scanners.
* **E.2 Prompt Injection Defense**: Input validation layer must detect and neutralize indirect/direct prompt injection attempts per OWASP LLM01.
* **E.3 Tool Authorization & Least Privilege**: Agents must enforce explicit tool whitelisting and require user authorization for destructive or state-mutating operations (OWASP LLM08).
* **E.4 Dependency Vulnerability Scan**: Zero `Critical` or `High` CVEs in application dependencies, verified via `trivy` or `pip-audit`.

---

## Gate F: Observability & Telemetry

* **F.1 OpenTelemetry GenAI Conventions**: Traces must be emitted for every LLM, retrieval, and tool invocation using standardized semantic conventions.
* **F.2 Token Tracking & Cost Attribution**: Telemetry must record input tokens, output tokens, total tokens, model name, and estimated cost per request.
* **F.3 Latency & Duration Metrics**: Standard metrics exported for Time-to-First-Token (TTFT), total request latency, and retrieval search duration.
* **F.4 Structured Logging**: Contextual JSON logs incorporating `trace_id`, `span_id`, tenant ID, and operation name. Zero raw PII in logs.

---

## Gate G: Performance & Sizing

* **G.1 Hardware Profiling**: Application documentation must declare minimum hardware requirements (RAM, VRAM, CPU cores) to run successfully on developer machines.
* **G.2 Latency Thresholds**:
  * Local Ollama inference: Time-to-first-token $\le 2.0$s on standard developer workstations (Apple Silicon M-series or 16GB RAM x86 with mid-range GPU).
  * Streaming responses enabled for interactive UI/chat endpoints.
* **G.3 Memory & Resource Leaks**: Process memory profile must remain stable across 1,000 consecutive simulated requests without memory leakage.

---

## Gate H: Documentation & Contracts

* **H.1 Reference Implementation Contract**: Application contains all mandatory files specified in [reference-implementation-standard.md](docs/architecture/reference-implementation-standard.md) (README, architecture diagram, domain model, API contract, threat model, run guide).
* **H.2 Visual Architecture Diagrams**: System architecture and data flow visualized using Mermaid.js diagrams directly embedded in markdown.
* **H.3 Trade-offs & Limitations**: Explicit section documenting architectural compromises, trade-offs, and known operational boundaries.
* **H.4 Zero Broken Links**: All relative markdown links and cross-references must resolve cleanly without 404s.

---

## Gate I: Demo & Local Execution

* **I.1 Zero-API-Key Local Execution**: Application must launch and execute completely using local Ollama and local containers without requiring paid cloud API keys.
* **I.2 Single-Command Bootstrapping**: Developer must be able to boot the entire stack with a single command (e.g., `docker compose up` or `task dev`).
* **I.3 Interactive Demonstration**: Includes a verified demonstration script or interactive CLI/UI allowing an architect to test the core value proposition in under 5 minutes.

---

## Gate J: Production Readiness & Resilience

* **J.1 Circuit Breaking & Retries**: External provider calls must be wrapped in configurable retries with exponential backoff and circuit breaking to prevent cascading failure.
* **J.2 Graceful Degradation**: If an AI model or vector store becomes unavailable, the application must degrade gracefully (e.g., return cached answers, notify user of service disruption) rather than crash with uncaught stack traces.
* **J.3 Health Checks & Probes**: Readiness and liveness endpoints (`/health/ready`, `/health/live`) reporting status of downstream vector stores, databases, and model endpoints.
* **J.4 Configuration Validation**: Application fails fast at startup if required configuration parameters or environment variables are missing or invalid.
