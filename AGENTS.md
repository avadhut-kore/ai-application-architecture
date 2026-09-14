# AGENTS.md: Operational Constitution for AI Coding Agents

> [!CRITICAL]
> **MANDATORY PRE-IMPLEMENTATION GOVERNANCE RULE**  
> **An AI coding agent must not start implementing a new application until it has read this root `AGENTS.md`, all relevant architecture standards in `docs/architecture/`, and the target application's requirements and architecture documents.**  
> Any implementation begun without completing this architectural inspection violates repository governance and will be rejected.

---

## 1. Repository Purpose & Engineering Philosophy

This repository, **`ai-application-architecture`**, is a long-term **Enterprise AI Architecture & Reference Implementation Repository**. It is NOT a playground for toy demos, quick tutorial snippets, unvalidated prompt scripts, or vendor-locked experiments.

Every implementation in this repository must stand as a production-grade benchmark for Enterprise Architects, Solution Architects, and Senior AI Engineers. As an AI coding agent working in this codebase, you must operate with the discipline, rigor, and restraint of a Principal Enterprise Architect.

---

## 2. Immutable Operational Directives

When interacting with this codebase, you must strictly uphold the following operational rules:

### Directive 1: No Premature Implementation
* Never jump directly to writing application code.
* Development must strictly follow the engineering lifecycle:
  $$\text{Requirements} \rightarrow \text{Architecture} \rightarrow \text{Design} \rightarrow \text{ADR} \rightarrow \text{Implementation} \rightarrow \text{Testing} \rightarrow \text{Evaluation} \rightarrow \text{Security} \rightarrow \text{Observability} \rightarrow \text{Performance} \rightarrow \text{Deployment} \rightarrow \text{Audit}$$
* Do not create placeholder files, empty test mocks, or skeleton scaffolding unless explicitly authorized by the current roadmap phase.

### Directive 2: Local-First Runtime Mandate
* All applications must run locally without requiring paid commercial API keys (OpenAI, Anthropic, etc.).
* The default, supported local runtime is **Ollama**.
* Code must be designed to execute against standard local open-weights models (e.g., Llama 3, Mistral, Qwen, Phi) on developer-grade hardware.

### Directive 3: Strict Provider Decoupling
* Never import vendor SDKs (`openai`, `anthropic`, `google-generativeai`) into domain business logic or application workflow coordinators.
* All model interactions must pass through the repository's **Provider Abstraction Layer** and **Model Gateway**.
* Swapping the underlying model or provider must be achievable purely via configuration changes without altering a single line of application code.

### Directive 4: Zero Mock/Fake Production Behavior
* Never commit fake sleep loops (e.g., `time.sleep(2)` pretending to do inference).
* Never return hardcoded mock strings in production code paths to simulate AI responses.
* Test doubles and in-memory mocks are permitted **strictly** within automated unit test suites (`tests/unit/`), never in `apps/` or `building-blocks/` runtime paths.

### Directive 5: Zero-Trust Model Output
* Large Language Model outputs are probabilistic and untrusted external data.
* Never feed raw model outputs into databases, downstream APIs, or shell execution contexts without strict schema parsing (Pydantic / Zod), domain invariant validation, and sanitization.
* Critical business rules, financial calculations, and access control decisions must remain strictly deterministic.

---

## 3. How Agents Must Inspect the Repository Before Modifying

Before writing code or editing existing files, you must follow this systematic inspection protocol:

1. **Verify Current Phase & Roadmap Scope**:
   * Inspect [ROADMAP.md](ROADMAP.md) to ensure the proposed work aligns with the active phase.
   * Review [SCOPE.md](SCOPE.md) to confirm the work is not explicitly excluded.
2. **Review Core Architecture Standards**:
   * Read [docs/architecture/architecture-principles.md](docs/architecture/architecture-principles.md).
   * Read [docs/architecture/reference-implementation-standard.md](docs/architecture/reference-implementation-standard.md).
   * Read [docs/architecture/four-dimension-model.md](docs/architecture/four-dimension-model.md).
   * Read [docs/architecture/anti-patterns.md](docs/architecture/anti-patterns.md) to ensure your design avoids known failure modes.
3. **Inspect Application Specifications & ADRs**:
   * If working in an application directory (`apps/<app-name>/`), read its `README.md`, architecture diagrams, and associated ADRs in `adr/`.
4. **Examine Existing Abstractions**:
   * Check `building-blocks/` before creating any new helper, client, or utility. Never duplicate an abstraction that already exists.

---

## 4. Coding & Architecture Standards

* **Architecture Style**: Use Clean / Hexagonal Architecture. Domain entities and business workflows must remain isolated from frameworks, databases, and LLM providers.
* **Type Safety & Contracts**: All code must be strictly typed.
  * Python: Full type hints, `pydantic` schemas for I/O, strict `mypy` compliance.
  * .NET: C# nullable reference types enabled, strongly typed record contracts.
  * TypeScript: Strict TypeScript (`"strict": true`), `zod` validation for external schemas.
  * Java: Modern Java (LTS), record classes, immutable domain objects.
* **Error Handling**: No bare exceptions. Implement dedicated domain exception hierarchies. All external provider calls must implement explicit timeouts, retries with exponential backoff, and circuit breakers.
* **Documentation Integrity**: Maintain docstrings, typing explanations, and architectural decision references in all code files.

---

## 5. Testing & Evaluation Requirements

No application or component may be considered complete without satisfying both classic software testing and AI evaluation:

### 5.1 Software Testing
* **Unit Tests**: Test all deterministic domain logic, state machines, parsers, and guardrails using deterministic unit tests with in-memory test doubles. Target > 85% line coverage.
* **Integration Tests**: Verify end-to-end integration between application services and the local Ollama provider or local database.

### 5.2 AI Evaluation Harness
* Every AI application must include an evaluation suite located in `eval/` or `tests/eval/`.
* Must contain an explicit, versioned dataset (`eval_dataset.jsonl`).
* Must automatically score outputs using defined metrics:
  * **Groundedness**: Did the answer rely strictly on retrieved context?
  * **Context Relevance**: Was the retrieved context relevant to the query?
  * **Answer Faithfulness**: Is the response factually consistent with the prompt constraints?
  * **Schema Adherence**: Did the output strictly match the expected JSON schema?

---

## 6. Security & Safety Standards

* **OWASP Top 10 for LLMs Compliance**: Every application must implement mitigations for prompt injection (LLM01), insecure output handling (LLM02), and excessive agency (LLM08).
* **Secrets Management**: Never commit API keys, tokens, passwords, or connection strings. Use environment variable injection (`.env.example` templates only).
* **Tool Authorization**: Agents with tool-calling capabilities must have strict whitelists, explicit authorization checks, and human-in-the-loop gates for state-mutating operations.

---

## 7. Observability Requirements

* Implement distributed tracing using **OpenTelemetry GenAI Semantic Conventions**.
* Every model interaction must log:
  * Prompt tokens, completion tokens, and total tokens.
  * Provider name, model name, temperature, and request duration (latency).
  * Span attributes capturing tool call signatures and retrieval chunk metadata.
* Never log raw PII or unredacted confidential data in telemetry spans.

---

## 8. Step-by-Step Agent Workflow & Verification Protocol

When assigned a task, follow this exact workflow:

```
┌────────────────────────────────────────────────────────┐
│ 1. ARCHITECTURAL RESEARCH                              │
│    Inspect AGENTS.md, ROADMAP.md, and docs/            │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. FORMULATE & APPROVE PLAN                            │
│    Create implementation plan; obtain explicit review  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. IMPLEMENT CONTRACTS & ADAPTERS                      │
│    Domain logic first, ports & adapters second         │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 4. WRITE DETERMINISTIC & EVALUATION TESTS              │
│    Unit tests + eval_dataset.jsonl + eval runner       │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 5. VALIDATE AGAINST QUALITY GATES                      │
│    Run linting, tests, evaluations, security audit     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 6. GENERATE COMPLETION REPORT                          │
│    Produce verifiable report mapped to Quality Gates   │
└────────────────────────────────────────────────────────┘
```

---

## 9. Required Completion Report Format

Upon concluding any task, the AI coding agent must output a structured completion report containing:

1. **Files Created & Modified**: Full relative paths and brief description of purpose.
2. **Architecture Decisions**: Summary of key patterns adopted and corresponding ADR links.
3. **Quality Gates Verification**: Line-by-line verification against [QUALITY-GATES.md](QUALITY-GATES.md) (Gates A through J).
4. **Local Execution Verification**: Proof that the code runs on local Ollama / Docker without external API keys.
5. **Known Limitations & Trade-offs**: Explicitly documented assumptions and technical compromises.
6. **Next Steps & Follow-Up Gaps**: What remains for subsequent roadmap phases.
