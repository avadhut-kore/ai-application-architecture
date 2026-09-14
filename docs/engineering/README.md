# Engineering Standards & Governance

## 1. Executive Mission

While [Phase 0](../../ROADMAP.md#phase-0-vision-scope--architecture-governance-current) established the **architecture constitution** for `ai-application-architecture`, Phase 1 establishes the **engineering constitution**.

These standards define how future code, tests, AI behavior, security controls, configuration, telemetry, APIs, data persistence, and Git workflows must be engineered and verified across the repository.

---

## 2. Governance Hierarchy & Precedence

All contributors and AI coding agents operate under a strict governance hierarchy:

```
┌────────────────────────────────────────────────────────┐
│ 1. AGENTS.md (Operational Constitution)                │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. Architecture Constitution (docs/architecture/*)     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. General Engineering Standards (docs/engineering/*)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 4. Technology-Specific Standards (dotnet, python, etc.)│
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 5. Application Architecture & ADRs                     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 6. Implementation Source Code                          │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 7. Quality Gates (QUALITY-GATES.md)                    │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 8. Objective Verification Evidence                     │
└────────────────────────────────────────────────────────┘
```

### Conflict Resolution Principle
> **More specific standards may refine general standards, but they must never silently violate higher-level architecture principles.**  
> When a specific implementation requires a justified deviation from an architectural standard, that deviation must be explicitly authorized and recorded in an approved Architecture Decision Record in [`adr/`](../../adr/README.md).

### Normative Governance & Authoritative Ownership

To prevent competing requirements and documentation divergence, each concern in this repository has exactly one authoritative source:

| Concern | Authoritative Source | Normative Role & Ownership |
| :--- | :--- | :--- |
| **Architecture Principles** | [`docs/architecture/*`](../architecture/principles.md) | Foundational architectural tenets, taxonomies, local-first policies, reference tiers, and anti-patterns. |
| **Quality Gates & Acceptance Criteria** | [`QUALITY-GATES.md`](../../QUALITY-GATES.md) | Mandatory repository release gates (Gates A through J), minimum thresholds, and PASS/FAIL criteria. |
| **Engineering Standards** | [`docs/engineering/*`](README.md) | Concrete implementation standards, language idioms, security controls, telemetry schemas, and testing guidelines. |
| **Definition of Done** | [`definition-of-done.md`](definition-of-done.md) | Implementation and readiness checklists derived from and mapped directly to the authoritative Quality Gates. |
| **AI Evaluation Methodology** | [`ai-evaluation.md`](ai-evaluation.md) | Statistical evaluation architecture, metric scoring guidelines, dataset design, and regression testing methods. |
| **Roadmap & Phase Sequencing** | [`ROADMAP.md`](../../ROADMAP.md) | Phase scope boundaries, entry/exit criteria, and roadmap milestones. |
| **Agent Behavior & Protocol** | [`AGENTS.md`](../../AGENTS.md) | Operational rules, mandatory workflow steps, verification mandates, and self-assessment policies for AI coding agents. |
| **Architecture Decisions** | [`adr/*`](../../adr/README.md) | Immutable records of architectural choices, trade-offs, evaluated alternatives, and consequences. |

> [!CRITICAL]
> **Normative Authority Rule**  
> [`QUALITY-GATES.md`](../../QUALITY-GATES.md) is the **sole authoritative source** for Quality Gates A through J, acceptance criteria, gate thresholds, and PASS/FAIL conditions. A specialized engineering standard may explain how to satisfy a gate or recommend stronger engineering practices, but it must **never** silently redefine, rename, or compete with an authoritative quality gate.

---

## 3. Engineering Standards Catalog

| Standard Document | Focus Area | Primary Topics |
| :--- | :--- | :--- |
| **[`general.md`](general.md)** | Core Principles | Simplicity before abstraction, Architecture Complexity Rule, explicit boundaries. |
| **[`dotnet.md`](dotnet.md)** | .NET / C# | .NET 8 LTS baseline, modern C#, async/cancellation, DI, options, analyzers. |
| **[`python.md`](python.md)** | Python | Python 3.11+, `mypy --strict`, `ruff`, `pytest`, `uv`/`pyproject.toml`, Pydantic v2. |
| **[`typescript.md`](typescript.md)** | TypeScript | Node 20+, strict TypeScript, no unsafe `any`, Zod, Vitest, streaming clients. |
| **[`java.md`](java.md)** | Java / Spring Boot | Java 21 LTS, Spring Boot conventions, JPA/transactions, JUnit 5, secondary role. |
| **[`testing.md`](testing.md)** | Software Testing | Risk-based portfolio, deterministic vs. eval separation, test doubles, coverage. |
| **[`ai-evaluation.md`](ai-evaluation.md)** | AI Evaluation | Probabilistic metrics, `eval_dataset.jsonl`, golden benchmarks, regression gating. |
| **[`security.md`](security.md)** | Security Engineering | OWASP Top 10 for LLMs, untrusted AI boundaries, prompt injection, least privilege. |
| **[`configuration.md`](configuration.md)** | Config & Secrets | 12-factor configuration, secret zero-tolerance, startup validation, fail-fast. |
| **[`dependencies.md`](dependencies.md)** | Dependency Governance | Minimizing packages, evaluation criteria, lockfiles, vulnerability audits. |
| **[`reliability.md`](reliability.md)** | Resilience & Errors | Error classification, conditional retries with backoff & jitter, circuit breaking. |
| **[`observability.md`](observability.md)** | Telemetry & Tracing | OpenTelemetry GenAI semantic spans, token metrics, request correlation. |
| **[`api-design.md`](api-design.md)** | API Engineering | Resource-oriented REST, streaming (SSE/WS), RFC 7807/9457 errors, OpenAPI 3.1. |
| **[`data.md`](data.md)** | Data Persistence | Persistence boundaries, schema migrations, tenant data, AI provenance tracking. |
| **[`documentation.md`](documentation.md)** | Documentation Quality| Tier-based documentation, executable Markdown linting, link validation. |
| **[`git-workflow.md`](git-workflow.md)** | Git & PR Workflows | Conventional Commits rationale, PR evidence checklists, protected main. |
| **[`definition-of-done.md`](definition-of-done.md)** | Definition of Done | Tier-aware DoD (Tiers 1–4), evidence record standards, independent review. |

---

## 4. Tier-Aware Governance

Engineering standards must be applied proportionally to the artifact's [Reference Implementation Tier](../architecture/reference-standard.md):

* **Tier 1 (Reference Application)**: Subject to **all** Quality Gates (Gates A–J). Full production rigor across architecture, types, tests, evals, security, telemetry, performance, documentation, local demo, and resilience.
* **Tier 2 (Pattern Example)**: Subject to Gates B, C, H, and I. Focused standards: clean types, deterministic unit/boundary tests, clean documentation, and local execution demo.
* **Tier 3 (Platform Component)**: Subject to Gates A, B, C, F, and H. Strict architectural boundary isolation, type safety, hermetic test doubles, OpenTelemetry spans, and contract documentation.
* **Tier 4 (Enterprise Template)**: Subject to Gates B and H. Validated scaffolding baseline, strict type safety, and scaffold usage documentation.
