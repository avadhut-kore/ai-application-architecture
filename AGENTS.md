# Operational Constitution for AI Coding Agents

> [!CRITICAL]
> **MANDATORY PRE-IMPLEMENTATION GOVERNANCE RULE**  
> **An AI coding agent must not implement a new reference application until it has read the repository governance, relevant requirements, architecture documents, applicable quality gates, and local-first policy.**  
> Any implementation begun without completing this architectural inspection violates repository governance and will be rejected.

---

## 1. Repository Purpose & Engineering Philosophy

This repository, **`ai-application-architecture`**, is an **Enterprise AI Architecture & Reference Implementation Repository**. It is not a playground for toy demos, quick tutorial snippets, unvalidated prompt scripts, vendor-locked experiments, or generated boilerplate.

Every implementation in this repository must stand as a production-grade benchmark for Solution Architects, Enterprise Architects, and Senior AI Engineers. As an AI coding agent operating in this codebase, you must exercise the rigor, restraint, and discipline of a Principal Enterprise Architect.

---

## 2. Twelve Non-Negotiable Operational Directives

When interacting with this codebase, you must strictly uphold the following twelve directives:

### 1. Inspect the Repository Before Modifying It
Always check the current filesystem state, directory structure, and existing building blocks before proposing changes or writing code. Never assume files exist without verifying.

### 2. Read Root Governance
Inspect and understand [`README.md`](README.md), [`VISION.md`](VISION.md), [`SCOPE.md`](SCOPE.md), [`ROADMAP.md`](ROADMAP.md), and [`QUALITY-GATES.md`](QUALITY-GATES.md) before planning or executing tasks.

### 3. Read Relevant Requirements
Before modifying an application or component, read its problem statement, functional requirements (FRs), and non-functional requirements (NFRs).

### 4. Read Relevant Architecture
Review [`docs/architecture/principles.md`](docs/architecture/principles.md), [`docs/architecture/taxonomy.md`](docs/architecture/taxonomy.md), [`docs/architecture/local-first.md`](docs/architecture/local-first.md), and application-specific architecture documents and ADRs.

### 5. Respect Phase Boundaries
Do not implement capabilities, services, or applications assigned to future roadmap phases. If assigned to Phase 0, do not implement Phase 1 tooling or Phase 4 models.

### 6. Avoid Speculative Implementation
Do not create empty placeholder files, speculative interface hierarchies (`IAgentLoop`, `IMemoryStore`), or unneeded infrastructure before a concrete application requires them.

### 7. Avoid Duplicate Documentation
Maintain one authoritative source per topic. Do not duplicate principles, taxonomy descriptions, or standards across multiple markdown files. Use cross-references.

### 8. Avoid Fake Data & Fake AI Behavior
Never commit fake sleep loops (e.g., `time.sleep(2)`) or hardcoded static strings in production execution paths to mimic AI inference. Real local models (Ollama) or live adapters must execute. Test doubles belong strictly in automated unit tests (`tests/unit/`).

### 9. Validate Your Work
Run static analysis, type checking (`mypy --strict`, `dotnet build`), unit test suites, evaluation harnesses, and link checkers after making changes.

### 10. Report Actual Evidence
Every claim in your completion report must be accompanied by verifiable evidence (terminal execution logs, test outputs, file paths, or score results). Never fabricate completed work.

### 11. Never Claim Tests Passed Unless They Were Executed
Do not state "tests passed" or "quality gates satisfied" unless you actually ran the corresponding command and received exit code 0 with passing assertions.

### 12. Never Claim Production Readiness Without Satisfying Applicable Gates
Do not label an implementation as "production-ready" unless it has been objectively verified against all applicable criteria in [QUALITY-GATES.md](QUALITY-GATES.md).

---

## 3. Mandatory Agent Workflow Protocol

When assigned an engineering task, follow this exact linear sequence:

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

## 4. Completion Report Structure

Upon completing any task, produce a structured completion report covering:
1. **Executive Summary**: High-level summary of accomplished work.
2. **Files Created & Modified**: Explicit list of files with relative paths.
3. **Architecture Decisions**: Key patterns adopted and ADR references.
4. **Decisions Deliberately Deferred**: Explicit statement of what was not built and why.
5. **Quality Gate Verification**: Line-by-line verification against applicable gates in [QUALITY-GATES.md](QUALITY-GATES.md).
6. **Local Execution Verification**: Proof that the system runs under Mode A or Mode B without paid API keys.
7. **Known Risks & Limitations**: Objective documentation of technical trade-offs.
8. **Next Steps**: What remains for subsequent roadmap phases.
