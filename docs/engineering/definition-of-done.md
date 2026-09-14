# Definition of Done & Quality Gate Mapping

This document establishes the Definition of Done (DoD) implementation checklists, tier-graduated readiness criteria, evidence reporting standards, and self-assessment policies for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Normative Role: Implementation Checklist, Not a Competing Gate System**  
> As defined in [`docs/engineering/README.md`](README.md), [`QUALITY-GATES.md`](../../QUALITY-GATES.md) is the **sole authoritative source** for Quality Gates (Gates A through J), mandatory release thresholds, and PASS/FAIL conditions.
>
> The **Definition of Done is an implementation and readiness checklist derived from and mapped directly to those authoritative quality gates**. It does not define new gates, rename existing gates, or override gate thresholds.

---

## 1. Tier-Aware Definition of Done Matrix

Every deliverable must satisfy the readiness checklist items corresponding to its [Reference Implementation Tier](../architecture/reference-standard.md), mapped to the authoritative Quality Gates:

| Quality Dimension & Authoritative Gate | Tier 1: Reference App | Tier 2: Pattern Example | Tier 3: Platform Component | Tier 4: Enterprise Template |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture & Structural Boundaries ([Gate A](../../QUALITY-GATES.md#gate-a--architecture--structural-boundaries))** | Architecture doc + C4 diagrams + ADRs; zero vendor SDKs in domain. | Architecture section in README + design trade-offs. | Component API spec + architectural ADR; strict port isolation. | Architecture overview + customization guide. |
| **Code Quality & Type Safety ([Gate B](../../QUALITY-GATES.md#gate-b--code-quality--type-safety))** | Strict typing (`mypy --strict`, `dotnet build --warnaserror`, `tsc --strict`); clean lint. | Strict typing and clean lint on pattern code. | Strict typing, clean lint, zero compiler warnings. | Scaffold passes type checker and linter out-of-the-box. |
| **Software Testing ([Gate C](../../QUALITY-GATES.md#gate-c--software-testing))** | $\ge 85\%$ statement coverage on domain modules; unit tests with in-memory doubles + integration tests. | $\ge 85\%$ domain coverage; unit + boundary tests. | $\ge 85\%$ domain coverage; hermetic test doubles + integration tests. | Scaffold includes passing unit test baseline ($\ge 60\%$). |
| **AI Evaluation ([Gate D](../../QUALITY-GATES.md#gate-d--ai-evaluation))** | Versioned `eval_dataset.jsonl` ($\ge 30$ scenarios; 50+ recommended); Faithfulness $\ge 0.85$; Context Relevance $\ge 0.80$; Schema Adherence $\ge 0.98$. | Curated eval set ($\ge 20$ scenarios if AI-bearing); schema validation. | Recommended (if probabilistic capabilities exposed). | N/A |
| **Security & Safety ([Gate E](../../QUALITY-GATES.md#gate-e--security--safety))** | Threat model documented; zero secret leaks; least-privilege tools; 0 High/Critical CVEs. | Threat modeled in README; zero secret leaks; safe output parsing. | Strict boundary validation; zero secrets; 0 High/Critical CVEs. | Safe defaults; `.env.example` template; 0 High/Critical CVEs. |
| **Observability & Telemetry ([Gate F](../../QUALITY-GATES.md#gate-f--observability--telemetry))** | OpenTelemetry GenAI semantic spans (`gen_ai.*`); token/duration metrics; PII redacted. | Basic metrics & structured JSON logs; error logging. | Full OTel GenAI instrumentation; trace propagation verified. | Pre-configured telemetry hooks. |
| **Performance & Sizing ([Gate G](../../QUALITY-GATES.md#gate-g--performance--sizing))** | TTFT $\le 2.0\text{s}$ with local 8B model; streaming token output; zero leaks across 500 requests. | Documented resource requirements in README. | Low-overhead benchmark verified (< 5% latency overhead). | Baseline sizing guidance documented. |
| **Documentation & Integrity ([Gate H](../../QUALITY-GATES.md#gate-h--documentation--architectural-integrity))** | Problem statement; C4 diagrams; trade-offs; `validate-docs.py` exit code 0. | Focused README; trade-offs; `validate-docs.py` exit code 0. | Comprehensive API docs; integration guide; `validate-docs.py` exit code 0. | Scaffold documentation; quickstart; `validate-docs.py` exit code 0. |
| **Demo & Operational Verification ([Gate I](../../QUALITY-GATES.md#gate-i--demo--operational-verification))** | Single-command local bootstrapping under Mode A (Offline Local) or Mode B (Local-First); $< 5$ min demo. | Runnable locally under Mode A or Mode B; $< 5$ min interactive demo. | Runnable integration test suite against local container. | Clean scaffold initialization script functional. |
| **Production Readiness & Resilience ([Gate J](../../QUALITY-GATES.md#gate-j--production-readiness--resilience))** | Timeouts on all calls; backoff retries with jitter; circuit breaking; graceful degradation; `/health` probes. | Basic timeout and error handling. | Fault injection verified; circuit breaker / fallback support. | Safe default timeouts configured. |

---

## 2. Mandatory Evidence Reporting Format

Every engineering completion report or pull request must provide verifiable evidence for each applicable gate. Claims without evidence are invalid:

### Evidence Categorization
* **Automated Evidence**: Command outputs, test run reports, linter logs, and validation scripts with explicit exit codes.
* **Manual Evidence**: Documented code inspection findings, architectural walk-throughs, and threat model reviews.
* **Not Applicable (N/A)**: Explicitly justified exclusions based on tier boundaries in [`QUALITY-GATES.md`](../../QUALITY-GATES.md).

### Standard Verification Table Schema
```markdown
| Quality Gate | Requirement | Verification Method | Status | Verifiable Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **Gate A: Architecture** | Modular decoupling; no vendor SDKs in domain | Static dependency analysis | PASS | Clean architectural boundary check log |
| **Gate B: Code Quality** | Strict type safety and linting | `mypy --strict` / `dotnet build` | PASS | Terminal execution output: 0 errors, 0 warnings |
| **Gate C: Testing** | $\ge 85\%$ domain statement coverage | `pytest --cov` / `dotnet test` | PASS | Coverage summary report (e.g. 88.4%) |
| **Gate D: Evaluation** | Faithfulness $\ge 0.85$, $\ge 30$ scenarios | Application eval runner | PASS | Eval report output (e.g. Faithfulness: 0.92) |
| **Gate E: Security** | Zero secret leaks, 0 High/Critical CVEs | `git-secrets` / `pip-audit` | PASS | Secret scanner and audit exit code 0 |
| **Gate F: Telemetry** | OpenTelemetry GenAI spans emitted | Mock exporter trace assert | PASS | JSON trace span dump with `gen_ai.*` attributes |
| **Gate G: Performance** | TTFT $\le 2.0\text{s}$ on local 8B model | Local benchmark execution | PASS | Latency report table in application README |
| **Gate H: Documentation**| Zero broken links, valid structure | `python3 scripts/validate-docs.py`| PASS | Script exit code 0; 0 broken links |
| **Gate I: Demo** | Runnable locally under Mode A or Mode B | Cold workstation trial | PASS | Terminal log from clone to demo execution |
| **Gate J: Resilience** | Backoff retry, circuit breaking, fallback | Automated fault injection test| PASS | Passing resilience test log showing graceful fallback |
```

---

## 3. Self-Assessment Policy & Separation of Acceptance

In compliance with repository governance ([`AGENTS.md`](../../AGENTS.md)):

1. **Mandatory Labeling**:
   * Any self-assessment score, readiness evaluation, or completion verdict produced by an author or AI agent must be explicitly labeled:
     > `> **Internal Self-Assessment — Not Independent Certification**`
2. **Conservative Scoring**:
   * Self-scores must be conservative and grounded entirely in empirical evidence. Unverified criteria must never be scored as a full pass.
3. **Separation of Assessment from Acceptance**:
   * The implementing engineer or agent performs the **Implementation Assessment**.
   * An independent reviewer, human architect, or distinct verification agent performs **Independent Acceptance**.
   * An implementing agent must **never** declare its own deliverable "independently accepted" or "certified."
