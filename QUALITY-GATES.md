# Enterprise Quality Gates (Gates A through J)

To ensure that contributions and reference implementations meet objective engineering standards, all repository deliverables must satisfy the criteria defined in these ten **Quality Gates**.

Applicability varies by the [Reference Implementation Tier](docs/architecture/reference-standard.md):
* **Tier 1 (Reference Application)**: Subject to **all** Quality Gates (Gates A–J).
* **Tier 2 (Pattern Example)**: Subject to Gates B, C, H, and I.
* **Tier 3 (Platform Component)**: Subject to Gates A, B, C, F, and H.
* **Tier 4 (Template)**: Subject to Gates B and H.

---

## Gate A — Architecture & Structural Boundaries

* **Requirement**: Domain business logic, state machines, and workflow coordinators must have zero direct compile-time or runtime dependencies on external AI provider SDKs (`openai`, `anthropic`, `google-generativeai`) or web frameworks. All model interactions must pass through architectural ports.
* **Applicability**: Tier 1 (Reference Applications) and Tier 3 (Platform Components).
* **Verification Method**: Static import analysis, dependency linter check, and code review.
* **Evidence Expected**: Automated import scan report proving absence of vendor SDK imports in `domain/` and `application/` source paths; approved Architecture Decision Record in `adr/` for pattern selection.

---

## Gate B — Code Quality & Type Safety

* **Requirement**: Source code must be strictly typed, adhere to configured linters without warnings, and parse all external/model inputs into validated schemas.
* **Applicability**: All Tiers (Tiers 1, 2, 3, and 4).
* **Verification Method**: Execution of language-specific static type checkers and linters:
  * Python: `mypy --strict` and `ruff check`.
  * .NET: `dotnet build --warnaserror` and `dotnet format --verify-no-changes`.
  * TypeScript: `tsc --noEmit` with `"strict": true` and `eslint`.
* **Evidence Expected**: Clean terminal execution logs with zero errors and zero warnings in CI/CD pipeline.

---

## Gate C — Software Testing

* **Requirement**: Deterministic domain logic, workflow state machines, and data mappers must achieve a minimum of **85% statement coverage** using hermetic unit tests. Unit tests must execute in isolation using in-memory test doubles without requiring live network access or running models. Integration tests must verify end-to-end component wiring against local containers.
* **Applicability**: Tiers 1, 2, and 3.
* **Verification Method**: Automated execution of test runners (`pytest --cov`, `dotnet test /p:CollectCoverage=true`, `vitest run`).
* **Evidence Expected**: Test execution report showing $\ge 85\%$ coverage for domain modules and 100% passing test assertions without skipped failures.

---

## Gate D — AI Evaluation

* **Requirement**: Every probabilistic capability must include an automated evaluation harness and a versioned evaluation dataset (`eval_dataset.jsonl`) containing at least 30 representative test scenarios. Evaluation runs must achieve:
  * **Groundedness / Faithfulness**: $\ge 0.85$ (factual claims supported by retrieved context).
  * **Context Relevance**: $\ge 0.80$ (retrieved context chunks pertinent to query).
  * **Schema Adherence**: $\ge 0.98$ (valid output parsing without syntax errors).
  * **Adversarial Handling**: Explicit test cases where the model abstains or flags unanswerable queries.
* **Applicability**: Tier 1 (Reference Applications).
* **Verification Method**: Execution of the application's evaluation runner script (`python eval/eval_runner.py`).
* **Evidence Expected**: Generated evaluation report (`eval/results/eval_report_<timestamp>.json`) containing quantitative metric scores meeting or exceeding required thresholds.

---

## Gate E — Security & Safety

* **Requirement**: Systems must prevent secret leakage, mitigate prompt injection risks, enforce least-privilege tool execution, and maintain zero high-severity dependencies:
  * Zero committed API keys, tokens, or plaintext credentials.
  * Inputs and retrieved contexts sanitized before model submission.
  * State-mutating tools enforce authorization checks and audit logging.
  * Zero `Critical` or `High` CVEs in application dependencies.
* **Applicability**: Tier 1 (Reference Applications) and Tier 3 (Platform Components).
* **Verification Method**: Execution of automated security scanners (`gitleaks`, `bandit`, `pip-audit` / `trivy`) and review of the application's `threat-model.md`.
* **Evidence Expected**: Clean security scanner output logs and documented STRIDE/OWASP LLM threat model in application documentation.

---

## Gate F — Observability & Telemetry

* **Requirement**: External model interactions, retrieval queries, and tool executions must emit structured OpenTelemetry trace spans. Telemetry spans must capture:
  * `gen_ai.system` (provider identifier).
  * `gen_ai.request.model` and `gen_ai.response.model`.
  * Request latency / duration.
  * Token consumption (`usage.input_tokens`, `usage.output_tokens`) where provided.
  * Success, error, or fallback state.
  * Raw customer PII must be redacted before export.
* **Applicability**: Tier 1 (Reference Applications) and Tier 3 (Platform Components).
* **Verification Method**: Trace emission verification in automated integration tests or trace inspection using OpenTelemetry Collector mock exporter.
* **Evidence Expected**: JSON trace span dump or integration test log asserting presence of required `gen_ai.*` semantic attributes.

---

## Gate G — Performance & Sizing

* **Requirement**: Applications must document explicit hardware sizing requirements and demonstrate stable memory and latency behavior:
  * Time-to-First-Token (TTFT) $\le 2.0\text{s}$ on standard developer workstations (Apple Silicon M-series or 16GB RAM x86 with local Ollama 8B model).
  * Interactive endpoints must implement chunked streaming.
  * Zero memory leaks across 500 consecutive test requests.
* **Applicability**: Tier 1 (Reference Applications).
* **Verification Method**: Local benchmark script execution measuring TTFT, total latency, and process RSS memory.
* **Evidence Expected**: Benchmark results table in the application's `README.md` or architecture document documenting measured latencies and workstation specifications.

---

## Gate H — Documentation & Architectural Integrity

* **Requirement**: Implementations must provide comprehensive documentation conforming to their tier contract:
  * Clear problem statement and business context.
  * Renderable Mermaid.js architecture and sequence diagrams.
  * Documented trade-offs, architectural compromises, and known limitations.
  * All markdown links and cross-references must resolve cleanly without broken links.
* **Applicability**: All Tiers (Tiers 1, 2, 3, and 4).
* **Verification Method**: Automated markdown link checker and peer architectural review.
* **Evidence Expected**: Clean link checker execution log and completed documentation checklist.

---

## Gate I — Demo & Operational Verification

* **Requirement**: The application must be runnable by a new developer on a clean workstation following a documented, single-command bootstrapping procedure:
  * Executes locally without requiring commercial cloud API keys (under Mode A or Mode B).
  * Interactive demonstration script or CLI executable in $< 5$ minutes.
  * Clean shutdown and teardown with zero orphaned processes or resources.
* **Applicability**: Tier 1 (Reference Applications) and Tier 2 (Pattern Examples).
* **Verification Method**: Clean workstation trial run executing documented commands (`docker compose up`, `task demo`).
* **Evidence Expected**: Step-by-step verification log demonstrating successful execution from cold clone to completion.

---

## Gate J — Production Readiness & Resilience

* **Requirement**: Systems must demonstrate resilience under downstream model or network failure:
  * Configurable timeouts on all external provider calls.
  * Exponential backoff retries on transient errors (HTTP 429, 503).
  * Circuit breaking preventing cascading failure during provider outages.
  * Graceful degradation returning cached data or user notification when models are unavailable.
  * Health probes (`/health/live`, `/health/ready`) reporting downstream readiness.
* **Applicability**: Tier 1 (Reference Applications).
* **Verification Method**: Automated fault injection test (e.g., simulating HTTP 503 from provider and verifying fallback or error response).
* **Evidence Expected**: Passing resilience test logs demonstrating circuit tripping and graceful degradation handling.
