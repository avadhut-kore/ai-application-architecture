# Definition of Done & Quality Gate Governance

This document establishes the comprehensive Definition of Done (DoD), tier-graduated completion criteria, evidence reporting standards, and self-assessment policies for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> This standard translates the quality gates in [`QUALITY-GATES.md`](../../QUALITY-GATES.md) into concrete, tier-aware completion requirements that must be satisfied before any implementation is considered complete.

---

## 1. Tier-Aware Definition of Done Matrix

Every deliverable in this repository must satisfy the Definition of Done corresponding to its reference implementation tier:

| Quality Dimension | Tier 1: Reference App | Tier 2: Pattern Example | Tier 3: Platform Component | Tier 4: Enterprise Template |
| :--- | :--- | :--- | :--- | :--- |
| **Architecture & ADRs (Gate G1)** | Full architecture doc + C4 + ADRs for key decisions. | Architecture section in README + rationale. | Full architecture doc + component API ADR. | Architecture overview + customization guide. |
| **Local-First Execution (Gate G2)** | Mode A (Ollama) & Mode B (in-memory) fully verified. | Mode A & Mode B verified. | Mode A or Mode B verified. | Scaffold runs in Mode B out-of-the-box. |
| **Test Quality & Coverage (Gate G3)** | ≥ 80% line, ≥ 75% branch; unit + integration + contract. | ≥ 70% line; unit + boundary tests. | ≥ 85% line, ≥ 80% branch; full test suite. | ≥ 60% line on template skeleton. |
| **AI Evaluation (Gate G4)** | Golden set (≥ 50 samples); faithfulness ≥ 0.90; zero regressions. | Curated set (≥ 20 samples); eval runner. | Recommended (if AI-bearing). | N/A |
| **Security & Privacy (Gate G5)** | OWASP LLM Top 10 audited; zero secret leaks; PII sanitized. | Threat-modeled; zero secrets; safe parsing. | Security audited; strict boundary validation. | Safe defaults; `.env.example` template. |
| **Reliability & Telemetry (Gate G6)** | OpenTelemetry GenAI spans; retries with jitter; circuit breaking. | Basic metrics & structured logs; retries. | Full OTel instrumentation; fault injection verified. | OTel hooks pre-configured. |
| **Documentation & CI (Gate G7)** | Full documentation; CI passing; `validate-docs.py` exit code 0. | Focused documentation; CI passing; `validate-docs.py` 0. | Comprehensive API docs; CI passing; `validate-docs.py` 0. | Scaffold docs; CI passing; `validate-docs.py` 0. |

---

## 2. Mandatory Evidence Reporting Format

Every engineering completion report or pull request must provide verifiable evidence for each claim made. Claims without evidence are invalid:

### Evidence Categorization
* **Automated Evidence**: Concrete command outputs, test run reports, linter logs, and validation scripts with explicit exit codes.
* **Manual Evidence**: Documented code inspection findings, architectural walk-throughs, and threat model reviews.
* **Not Applicable (N/A)**: Explicitly justified exclusions based on tier boundaries or architectural scope.

### Standard Verification Table Schema
```markdown
| Quality Gate | Requirement | Verification Method | Status | Verifiable Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **G1: Architecture** | Modular decoupling | Static dependency analysis | PASS | Clean architectural boundary check log |
| **G2: Local-First** | Mode A execution | `curl` / local runner output | PASS | Terminal execution log against Ollama |
| **G3: Testing** | ≥ 80% line coverage | `pytest --cov` / `coverlet` | PASS | Coverage summary report (e.g. 84.2%) |
| **G4: Evaluation** | Faithfulness ≥ 0.90 | `python tests/eval/run.py` | PASS | Eval scorecard output (e.g. 0.925) |
| **G5: Security** | Zero secret leaks | `git-secrets` / pre-commit | PASS | Secret scanner terminal exit code 0 |
| **G6: Reliability** | Structured JSON logs | Application stdout capture | PASS | Formatted JSON log sample with trace_id |
| **G7: Documentation** | Zero broken links | `python3 scripts/validate-docs.py`| PASS | Script exit code 0; 0 broken links |
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
