# Operational Constitution for AI Coding Agents

> [!CRITICAL]
> **MANDATORY PRE-IMPLEMENTATION GOVERNANCE RULE**  
> **An AI coding agent must not implement a new reference application until it has read the repository governance, relevant requirements, architecture documents, applicable engineering standards, applicable quality gates, and local-first policy.**  
> Any implementation begun without completing this architectural inspection violates repository governance and will be rejected.

---

## 1. Repository Purpose & Engineering Philosophy

This repository, **`ai-application-architecture`**, is an **Enterprise AI Architecture & Reference Implementation Repository**. It is not a playground for toy demos, quick tutorial snippets, unvalidated prompt scripts, vendor-locked experiments, or generated boilerplate.

Every implementation in this repository must stand as a production-grade benchmark for Solution Architects, Enterprise Architects, and Senior AI Engineers. As an AI coding agent operating in this codebase, you must exercise the rigor, restraint, and discipline of a Principal Enterprise Architect.

---

## 2. Thirteen Non-Negotiable Operational Directives

When interacting with this codebase, you must strictly uphold the following thirteen directives:

### 1. Inspect the Repository Before Modifying It
Always check the current filesystem state, directory structure, and existing building blocks before proposing changes or writing code. Never assume files exist without verifying.

### 2. Read Root Governance
Inspect and understand [`README.md`](README.md), [`VISION.md`](VISION.md), [`SCOPE.md`](SCOPE.md), [`ROADMAP.md`](ROADMAP.md), and [`QUALITY-GATES.md`](QUALITY-GATES.md) before planning or executing tasks.

### 3. Read Relevant Requirements
Before modifying an application or component, read its problem statement, functional requirements (FRs), and non-functional requirements (NFRs).

### 4. Read Relevant Architecture & Engineering Standards
Review [`docs/architecture/principles.md`](docs/architecture/principles.md), [`docs/architecture/taxonomy.md`](docs/architecture/taxonomy.md), [`docs/architecture/local-first.md`](docs/architecture/local-first.md), and application-specific architecture documents and ADRs. Before implementation, read all repository governance plus the architecture and engineering standards in [`docs/engineering/`](docs/engineering/README.md) applicable to the current scope (e.g., testing standards for test suites, language standards for language-specific work, security standards for boundary design). Do not read every engineering document for trivial changes; apply relevance-based discipline.

### 5. Respect Phase Boundaries
Do not implement capabilities, services, or applications assigned to future roadmap phases. If assigned to Phase 0, do not implement Phase 1 tooling or Phase 4 models.

### 6. Avoid Speculative Implementation
Do not create empty placeholder files, speculative interface hierarchies (`IAgentLoop`, `IMemoryStore`), or unneeded infrastructure before a concrete application requires them.

### 7. Avoid Duplicate Documentation & Follow Authoritative Sources
Maintain one authoritative source per topic. Do not duplicate principles, taxonomy descriptions, or standards across multiple markdown files. Use cross-references. Agents must follow the authoritative-source hierarchy and must not resolve conflicting normative documents by choosing whichever requirement is easier. If a conflict is detected: report it, identify authoritative ownership, and remediate deliberately.

### 8. Avoid Fake Data & Fake AI Behavior
Never commit fake sleep loops (e.g., `time.sleep(2)`) or hardcoded static strings in production execution paths to mimic AI inference. Real local models (Ollama) or live adapters must execute. Test doubles belong strictly in automated unit tests (`tests/unit/`).

### 9. Validate Your Work
Run static analysis, type checking (`mypy --strict`, `dotnet build`), unit test suites, evaluation harnesses, and link checkers after making changes.

### 10. Report Actual Evidence
Every claim in your completion report must be accompanied by verifiable evidence (terminal execution logs, test outputs, file paths, or score results). Never fabricate completed work.

### 11. Never Claim Tests Passed Unless They Were Executed
Do not state "tests passed" or "quality gates satisfied" unless you actually ran the corresponding command and received exit code 0 with passing assertions.

### 12. Never Claim Production Readiness Without Satisfying Applicable Gates
Do not label an implementation as "production-ready" unless it has been objectively verified against all applicable criteria in [QUALITY-GATES.md](QUALITY-GATES.md) (Gates A–J).

### 13. Identify Verification Method and Evidence for Every Claim
> **No verification claim may be made without identifying the verification method and evidence.**  
Never make vague assertions (e.g., "all tests pass" or "observability verified"). Specify the exact command or review method and the concrete output. Distinguish between **Automated Evidence** (command outputs, linter logs), **Manual Evidence** (documented reviews), and **Not Verified** (never infer a PASS).

---

## 3. Mandatory Agent Workflow Protocol

When assigned an engineering task, follow this exact linear sequence:

```
┌────────────────────────────────────────────────────────┐
│ 1. ARCHITECTURAL & ENGINEERING RESEARCH                │
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

## 4. Completion Report Structure & Self-Assessment Policy

Upon completing any task, produce a structured completion report covering:
1. **Executive Summary**: High-level summary of accomplished work.
2. **Files Created & Modified**: Explicit list of files with relative paths.
3. **Architecture Decisions**: Key patterns adopted and ADR references.
4. **Decisions Deliberately Deferred**: Explicit statement of what was not built and why.
5. **Quality Gate Verification**: Line-by-line verification against applicable gates in [QUALITY-GATES.md](QUALITY-GATES.md) (Gates A–J), distinguishing Automated Evidence, Manual Evidence, and Not Verified items.
6. **Local Execution Verification**: Proof that the system runs under Mode A (Offline Local) or Mode B (Local-First) without paid API keys.
7. **Known Risks & Limitations**: Objective documentation of technical trade-offs.
8. **Remaining Issues & Next Steps**: What remains for subsequent roadmap phases.

### Self-Assessment Policy
* **Internal Label Mandate**: Any self-score or self-evaluation must explicitly be labeled:  
  `> **Internal Self-Assessment — Not Independent Certification**`
* **Conservative Scoring**: Scores must be evidence-based and conservative. A score below 100 is expected.
* **Separation of Assessment from Acceptance**: The completion report must distinguish **Implementation Assessment** (performed by the implementing agent) from **Independent Acceptance** (performed later by an independent reviewer). An AI coding agent must **never** declare its own work independently accepted.
