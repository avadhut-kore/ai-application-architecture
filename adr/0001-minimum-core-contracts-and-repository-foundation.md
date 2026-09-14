# ADR-0001: Minimum Core Contracts & Repository Foundation

* **Status**: Accepted
* **Deciders**: Principal Software Architect, Enterprise AI Architect, Platform Engineer
* **Date**: 2026-09-14
* **Technical Story**: Phase 2 — Repository Foundation & Minimum Core Contracts ([`ROADMAP.md`](../ROADMAP.md#phase-2-repository-foundation--minimum-core-contracts))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

Following the completion and freeze of Phase 0 (Architecture Governance) and Phase 1 (Engineering Standards), the `ai-application-architecture` repository requires establishing the physical monorepo foundation, dependency boundaries, cross-platform validation tooling, and minimal core capability contracts before building reference templates (Phase 3) and foundational AI adapters (Phase 4).

In accordance with repository governance ([`AGENTS.md`](../AGENTS.md) and [`docs/engineering/general.md`](../docs/engineering/general.md)), this repository strictly avoids speculative architecture, universal frameworks, and premature abstractions.

---

## 2. Problem Statement

How should the repository organize its physical structure, implement its first minimum contracts, validate architectural boundaries across a polyglot environment, and avoid speculative framework bloat while providing a clean foundation for Phase 3 and Phase 4?

---

## 3. Decision Drivers

* **Just-in-Time Abstraction**: Concrete need $\rightarrow$ minimal contract $\rightarrow$ implementation experience $\rightarrow$ proven reuse $\rightarrow$ abstraction.
* **Phase Boundary Integrity**: Zero premature implementation of RAG, agents, workflows, memory, vector databases, MCP, or model gateways.
* **Single Authoritative Quality Gates**: Compliance with Gates A through J in [`QUALITY-GATES.md`](../QUALITY-GATES.md).
* **Cross-Platform Repeatability**: Single validation entry point executing identically on developer workstations (macOS, Linux, Windows) and in continuous integration.
* **First-Implementation Ecosystem Fit**: Selecting the language implementation strategy that most directly supports Phase 4 AI Foundations without speculative polyglot duplication.

---

## 4. Options Considered

### Option 1: Language-Neutral Specification Only (No Code)
* **Description**: Define contracts purely in Markdown or JSON Schema without any executable programming language types or tests.
* **Pros**: Zero language-specific code in Phase 2.
* **Cons**: Provides no executable type safety, cannot be verified with automated unit tests, and forces Phase 3/4 to invent the first concrete types without prior contract testing.

### Option 2: Universal Polyglot Duplication (.NET, Python, TypeScript, Java)
* **Description**: Implement identical copies of all core interfaces and models across all four supported languages simultaneously.
* **Pros**: Superficial symmetry across language ecosystems.
* **Cons**: Violates Phase 1 governance against speculative duplication; creates high maintenance drag before any application requires those abstractions; violates Java secondary language policy.

### Option 3: Minimal Bounded Contracts in Python + Polyglot Standards (Chosen)
* **Description**: Implement the minimum justified capability contracts in **Python** (`building-blocks/python/contracts/`) as the primary language for Phase 4 AI Foundations (Ollama integration, Pydantic validation, eval runner). Maintain clear language-neutral semantics in engineering standards.
* **Pros**: Directly prepares Phase 4 with executable, strictly typed contracts; zero unneeded boilerplate in other languages; verified with hermetic in-memory tests.
* **Cons**: Other languages (.NET, TypeScript, Java) will introduce their concrete contracts just-in-time when their respective applications are implemented.

---

## 5. Decision Outcome

**Chosen Option**: **Option 3: Minimal Bounded Contracts in Python + Polyglot Standards**

### Rationale
Python is the primary ecosystem for Phase 4 AI Foundations. Implementing bounded contracts in Python allows us to verify the contracts with hermetic in-memory tests (`FakeLlmClient`) and integrate them into the cross-platform validator (`scripts/validate.py`) without speculative polyglot bloat.

### Architectural Implementation Details
1. **Physical Monorepo Organization**:
   * `building-blocks/python/contracts/`: houses bounded capability contracts.
   * `apps/`: reserved for independent reference applications; zero cross-app dependencies allowed.
   * `platform/`: reserved for shared platform infrastructure (Ollama container setups, optional model gateway); no speculative code in Phase 2.
2. **Minimum Core Contracts Introduced**:
   * **Text Generation Capability Port**: `TextGenerationPort` (with aliases `LlmClientPort` and `ILlmClient`) in `ports.py`. Strictly bounded to text/structured generation; excludes tools, agents, memory, and embeddings.
   * **Invocation Models**: `CompletionRequest`, `CompletionResponse`, `UsageMetrics`, `ChatMessage`, `Role`, and `FinishReason` in `models.py`.
   * **AI Operation / Telemetry Context**: `AiOperationContext` in `telemetry.py`, aligned with OpenTelemetry GenAI semantic conventions (`gen_ai.*`).
   * **Evaluation Contracts**: `EvaluationStatus`, `EvaluationMetric`, `EvaluationScenarioResult`, and `EvaluationSummary` in `evaluation.py`, providing structured schemas for evaluation reporting and metric aggregation.
   * **Bounded Error Taxonomy**: Bounded hierarchy in `errors.py` rooted at `AiError`: Transient / retriable errors (`AiRateLimitError`, `AiTimeoutError`, `AiProviderUnavailableError`), Non-Transient / fatal configuration errors (`AiAuthenticationError`, `AiInvalidRequestError`, `AiModelNotFoundError`), and Semantic output errors (`AiSchemaValidationError`, `AiContentFilterError`).
   * **Structured Output Validation**: `ValidationResult[T]` generic envelope in `validation.py` to decouple raw model response parsing from schema validation.
3. **Unified Validation Entry Point**:
   * `scripts/validate.py` executes documentation link checking, repository architecture boundary assertions, and hermetic contract tests in a single command.
   * `.github/workflows/ci.yml` invokes the exact same `python3 scripts/validate.py` entry point under least-privilege permissions.

---

## 6. Explicit Deferrals

In accordance with repository governance, the following capabilities are explicitly deferred:

| Capability | Deferred Phase | Architectural Justification |
| :--- | :---: | :--- |
| **Embedding Port (`IEmbeddingClient`)** | Phase 5 | Embeddings are not required until Knowledge Intelligence / RAG; deferred to prevent unused abstractions. |
| **Guardrails Abstraction (`IGuardrail`)** | Later Phases | Guardrails represent multiple distinct concerns (input sanitization, schema validation, policy checks) that must not be prematurely unified. |
| **Tools & MCP (`ITool`, `McpClient`)** | Phase 6 | Tools and Model Context Protocol belong to Agentic Task Execution, not foundation contracts. |
| **Memory Abstractions (`IMemory`)** | Later Phases | Memory is a distinct stateful capability deferred until agent memory requirements exist. |
| **Workflow Engines (`IWorkflow`)** | Phase 7 | Multi-agent workflow orchestration is governed under Phase 7. |
| **Model Gateway Service** | Conditional | Gateways are introduced only when centralized routing, quotas, or rate limiting are required; direct ports suffice for initial reference apps. |
| **Provider Adapters (Ollama, Cloud SDKs)**| Phase 4 | Infrastructure adapters belong to AI Foundations; Phase 2 verifies ports exclusively via in-memory test doubles. |

---

## 7. Consequences

### Positive Consequences
* Phase 4 AI Foundations has ready-to-use, tested contracts without any speculative framework bloat.
* Monorepo boundaries and isolation rules are enforceable via automated validation (`scripts/validate.py`).
* Zero external third-party runtime dependencies are introduced; contracts use standard library typing.

### Negative Consequences & Trade-offs
* .NET, TypeScript, and Java do not have Phase 2 contract code; their contracts will be introduced just-in-time when their respective reference implementations are scheduled.

---

## 8. Compliance with Quality Gates

* **Gate A (Architecture & Boundaries)**: Zero vendor SDK imports in `building-blocks/python/contracts/`. Ports decouple domain logic from infrastructure.
* **Gate B (Code Quality & Type Safety)**: Strictly typed contracts with standard type annotations. Static type checker and linter execution (`mypy`, `ruff`) is explicitly deferred to later phases as runtime tooling is established.
* **Gate C (Software Testing)**: 100% of contract assertions verified using in-memory test doubles (`FakeLlmClient`).
* **Gate H (Documentation & Integrity)**: ADR-0001 documents context, drivers, outcomes, and deferrals; 100% internal links resolved cleanly.
