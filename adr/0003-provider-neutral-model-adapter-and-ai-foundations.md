# ADR-0003: Provider-Neutral Model Adapter & AI Foundations

* **Status**: Accepted
* **Deciders**: Principal AI Systems Architect, Enterprise AI Architect, Senior Python Engineer, LLM Platform Engineer, Quality Governance Engineer
* **Date**: 2026-09-14
* **Technical Story**: Phase 4 — AI Foundations ([`ROADMAP.md`](../ROADMAP.md#phase-4-ai-foundations))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

Following the completion and freeze of Phase 0 (Architecture Governance), Phase 1 (Engineering Standards), Phase 2 (Repository Foundation & Minimum Contracts), and Phase 3 (Tiered Reference Implementation Templates), the `ai-application-architecture` repository is ready for its first executable AI runtime capabilities.

In production enterprise architectures, applications must leverage local and cloud-based Large Language Models (LLMs) without becoming tightly coupled to vendor-specific SDKs, proprietary protocols, or brittle, rapidly mutating third-party orchestration frameworks.

Phase 4 operationalizes the provider-neutral `TextGenerationPort` defined in Phase 2 by introducing a concrete, local-first runtime adapter for **Ollama**, an enterprise application pattern for **Structured Generation & Validation**, and an automated **AI Evaluation Harness** conforming to Gate D.

---

## 2. Problem Statement

How should the repository structure and implement its first concrete AI model execution capabilities so that:
1. Applications interact with models through clean, provider-neutral capability ports;
2. Ollama is leveraged as an implementation adapter without becoming the architecture;
3. Model outputs are treated as untrusted and validated against typed schemas before application use;
4. Transports, timeouts, cancellations, and selective retries are handled robustly;
5. The dependency footprint remains minimal, avoiding speculative AI frameworks, model gateways, vector databases, tools, or agent loops?

---

## 3. Decision Drivers

* **Provider Neutrality**: Application domain logic and use cases must have zero compile-time or runtime dependencies on provider-specific client libraries or endpoints.
* **Minimal Dependency Weight & Supply Chain Safety**: Avoid pulling in heavy third-party SDKs, unvetted wrappers, or rapid-release orchestration frameworks.
* **Untrusted Model Output Principle**: Model outputs must be rigorously validated before application ingestion; JSON-like text is never assumed valid.
* **Local-First Feasibility (Mode A)**: Default local execution must run completely offline without commercial cloud API keys.
* **Strict Phase Boundaries**: Defer RAG, embeddings, vector stores, tools, MCP, agents, memory, and model gateways to future phases.

---

## 4. Options Considered

### Option 1: Heavyweight Multi-Provider Orchestration Framework (e.g. LangChain, Semantic Kernel)
* **Description**: Adopt an established open-source framework to manage model invocations, prompt templates, and structured output parsing.
* **Pros**: Pre-built abstractions for dozens of providers.
* **Cons**: Massive transitive dependency trees; leaky abstractions; constant breaking API churn; violates repository anti-framework stance.

### Option 2: Vendor-Specific SDK (`ollama-python`)
* **Description**: Install and wrap the official `ollama` Python package.
* **Pros**: Simple high-level client method calls.
* **Cons**: Introduces unnecessary external dependencies; limits low-level transport, timeout, and cancellation control; leaks vendor error types across boundaries.

### Option 3: Pure Standard Library Direct HTTP Adapter behind `TextGenerationPort` (Chosen)
* **Description**: Implement `OllamaAdapter` using Python standard library `urllib.request` and `json` executed asynchronously via `asyncio.to_thread`.
* **Pros**:
  * Zero external runtime dependencies; 100% portable across Python 3.9+.
  * Precise control over HTTP request serialization, streaming boundaries, headers, and timeouts.
  * Native translation of HTTP status codes and connection errors into the bounded `AiError` taxonomy.
  * Direct support for `asyncio.CancelledError` and bounded exponential backoff retries on transient errors.
  * Decouples the application contract from provider packages entirely.
* **Cons**: Requires explicit handling of HTTP transport and response JSON parsing.

---

## 5. Decision Outcome

**Chosen Option**: **Option 3: Pure Standard Library Direct HTTP Adapter behind `TextGenerationPort`**

### Architectural Provisions

1. **Provider-Neutral Model Port (`TextGenerationPort`)**:
   * The application core defines and depends strictly on `TextGenerationPort` (`building-blocks/python/contracts/ports.py`).
   * Accepts `CompletionRequest` and returns `CompletionResponse` containing text, finish reason, and `UsageMetrics`.
   * Applications receive this port via Dependency Injection; they have zero imports from `platform/ollama-adapter`.

2. **Ollama Platform Component (`platform/ollama-adapter/`)**:
   * Classified as a **Tier 3 Platform Component** under Mode A (Offline Local).
   * Communicates directly with Ollama's native HTTP API (`/api/generate` and `/api/chat`).
   * Maps Ollama duration nanoseconds to `latency_ms` and prompt/eval tokens to `UsageMetrics`.
   * Maps HTTP 404 to `AiModelNotFoundError`, connection refusal to `AiProviderUnavailableError`, timeouts to `AiTimeoutError`, and bad requests to `AiInvalidRequestError`.
   * Implements selective retry with jitter only on transient errors (`AiTransientError`), with bounded attempts (max 2 retries). Fatal errors (invalid model, invalid request) fail immediately.
   * Provides non-blocking execution via `asyncio.to_thread` and honors task cancellation.

3. **Untrusted Model Output & Structured Generation (`examples/structured-generation/`)**:
   * Classified as a **Tier 2 Pattern Example** under Mode A.
   * Demonstrates an enterprise application service (`FeedbackExtractionService`) parsing unstructured input into strongly typed domain models (`CustomerFeedbackExtraction`).
   * All model output is treated as untrusted input. It is parsed through `ValidationResult[T]` enforcing schema fields, enum constraints, and numeric ranges ($0.0 \le \text{confidence} \le 1.0$).
   * Implements a bounded corrective retry (max 1 retry with error feedback prompt) on schema validation failure, gracefully returning `ValidationResult.failure` upon exhaustion.

4. **Continuous AI Evaluation Harness (`examples/ai-evaluation/`)**:
   * Classified as a **Tier 2 Pattern Example**.
   * Implements a Gate D evaluation runner executing against a versioned 30-scenario dataset (`eval_dataset.jsonl`).
   * Evaluates deterministic schema adherence ($\ge 0.98$), required field completeness, and adversarial query abstention.
   * Aggregates results into `EvaluationSummary` per `building-blocks/python/contracts/evaluation.py`.

5. **Cloud Provider Portability Decision**:
   * Per Phase 4 governance, **Option B — Defer second cloud provider** is adopted: provider portability is verified structurally through the `TextGenerationPort` protocol. Real cloud provider runtime verification remains deferred until credentials are configured in Phase 12 or an application milestone.

6. **Strict Capability Deferrals**:
   * **Embeddings & Vector Databases**: Deferred to Phase 5 (Knowledge Intelligence & RAG).
   * **Retrieval, Chunks & RAG**: Deferred to Phase 5.
   * **Tools, Functions, & MCP**: Deferred to Phase 6 (Agentic Task Execution).
   * **Agents & Loops**: Deferred to Phase 6.
   * **Memory Systems**: Deferred to Phase 6+.
   * **Workflows & Orchestration**: Deferred to Phase 7.
   * **Centralized Model Gateway & Quota Routing**: Deferred to Phase 12.

---

## 6. Consequences

### Positive Consequences
* Completely eliminates vendor SDK lock-in and protects domain logic from third-party API changes.
* Introduces zero external third-party dependencies, keeping the repository build hermetic, fast, and secure.
* Validates untrusted probabilistic model generations deterministically before application state ingestion.
* Provides clear, reproducible demonstration commands and evaluation metrics.

### Negative Consequences & Trade-offs
* Direct HTTP client requires manual JSON payload formatting and header management.
* Without a running Ollama instance, live provider execution cannot be verified; offline tests must rely on test doubles (`FakeLlmClient`).

---

## 7. Compliance with Quality Gates

* **Gate A — Architecture & Structural Boundaries**: Inward dependency direction strictly enforced. Applications depend only on contracts; zero Ollama imports in application or domain layers.
* **Gate B — Code Quality & Type Safety**: Pure Python typing with standard library dataclasses, enums, and protocols; clean linting and strict type signatures.
* **Gate C — Software Testing**: Hermetic unit test suites cover request formatting, response parsing, error mapping, bounded retry, and schema validation using in-memory test doubles without requiring network access.
* **Gate D — AI Evaluation**: Versioned 30-scenario dataset (`eval_dataset.jsonl`) and automated evaluation runner measuring schema adherence and adversarial handling.
* **Gate E — Security & Safety**: Zero committed credentials; model outputs treated strictly as untrusted data; no model generation directly executed as code or query.
* **Gate F — Observability & Telemetry**: AI operation context captures `gen_ai.*` standard attributes, latency measurements, and token usage metrics.
* **Gate G — Performance & Sizing**: Zero memory leaks; latency measurements recorded at the adapter boundary.
* **Gate H — Documentation & Architectural Integrity**: Comprehensive READMEs conforming to Tier 2 and Tier 3 templates; Mermaid architecture diagrams; all links validated via `validate-docs.py`.
* **Gate I — Demo & Operational Verification**: Single-command demonstration script runs locally in $< 1$ minute under Mode A.
* **Gate J — Production Readiness & Resilience**: Bounded timeouts on all calls; selective retry with backoff on transient errors; circuit-safe failure handling.
