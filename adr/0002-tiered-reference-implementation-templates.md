# ADR-0002: Tiered Reference Implementation Templates

* **Status**: Accepted
* **Deciders**: Principal Software Architect, Enterprise AI Architect, Developer Experience Architect, Quality Engineering Architect
* **Date**: 2026-09-14
* **Technical Story**: Phase 3 — Tiered Reference Implementation Templates ([`ROADMAP.md`](../ROADMAP.md#phase-3-tiered-reference-implementation-templates))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

Following the completion of Phase 0 (Architecture Governance), Phase 1 (Engineering Standards), and Phase 2 (Repository Foundation & Minimum Contracts), the `ai-application-architecture` repository requires establishing canonical templates and an evidence-driven governance system for future reference implementations.

A recurring failure mode in enterprise reference repositories is **asymmetric ceremony**: either forcing every small pattern example to satisfy an exhausting 15-document bureaucracy, or permitting reference applications to cut corners and omit production-critical architecture, evaluation, and security rigor.

To resolve this, Phase 0 established the four reference tiers in [`docs/architecture/reference-standard.md`](../docs/architecture/reference-standard.md). Phase 3 operationalizes this standard by providing canonical templates, machine-readable manifests, an automated tier validator, and a quality gate applicability matrix.

---

## 2. Problem Statement

How should reference implementation archetypes be structured, documented, validated, and classified across the four reference tiers without creating ceremonial boilerplate, introducing fake application code, or prematurely implementing AI capabilities?

---

## 3. Decision Drivers

* **Proportional Ceremony**: Documentation and testing rigor must be proportional to artifact complexity and risk.
* **Anti-Framework Stance**: Templates must encode architectural expectations, not hypothetical framework code or empty directories.
* **Deterministic Automated Validation**: Tier structure, mandatory documents, and metadata must be machine-verifiable in CI without brittle heuristic regex scraping.
* **Single Authoritative Quality Gates**: Compliance must map strictly to Gates A through J in [`QUALITY-GATES.md`](../QUALITY-GATES.md); no competing gate systems (`T1-G1`, `RefGate`) are permitted.
* **Technology & AI Framework Neutrality**: Templates must not prescribe specific web frameworks (FastAPI, ASP.NET Core) or AI orchestration frameworks (LangChain, Semantic Kernel).

---

## 4. Options Considered

### Option 1: Monolithic Universal Standard (One Size Fits All)
* **Description**: Require every artifact in the repository to produce an identical, exhaustive set of 12 separate documentation files regardless of whether it is an end-to-end application or a 200-line pattern demonstration.
* **Pros**: Single uniform checklist for all components.
* **Cons**: Crushes developer velocity; causes shallow "compliance-only" boilerplate in small examples; blurs the distinction between focused patterns and enterprise reference apps.

### Option 2: Heavyweight Multi-Document Skeletons with Hundreds of Empty Files
* **Description**: Scaffold hundreds of empty placeholder files across `apps/_template/` anticipating every possible future capability (e.g., `vector_store.py`, `agent_loop.py`, `tool_registry.py`).
* **Pros**: Superficial completeness.
* **Cons**: Directly violates Directive 6 (`Avoid Speculative Implementation`) of [`AGENTS.md`](../AGENTS.md); generates massive repository noise; difficult to maintain.

### Option 3: Minimal Tiered Templates with Consolidated Docs, Machine-Readable Manifests, and Applicability-Driven Gating (Chosen)
* **Description**: Establish four lean template archetypes in a dedicated `templates/` directory:
  * **Tier 1 (Reference Application)**: Consolidated into `README.md` + 3 focused documents (`docs/requirements.md`, `docs/architecture.md`, `docs/quality.md`) + `artifact.json`.
  * **Tier 2 (Pattern Example)**: Self-contained structured `README.md` + `artifact.json`.
  * **Tier 3 (Platform Component)**: Self-contained contract/integration `README.md` + `artifact.json`.
  * **Tier 4 (Template Artifact)**: Archetype instructions & non-production notice `README.md` + `artifact.json`.
* **Pros**: Zero ceremonial bloat; teaches architectural thinking; machine-verifiable via lightweight standard library JSON manifest; maps proportionally to Quality Gates A–J.
* **Cons**: Requires authors to exercise engineering judgment when determining whether optional sections (e.g. AI evaluation for non-AI components) apply.

---

## 5. Decision Outcome

**Chosen Option**: **Option 3: Minimal Tiered Templates with Consolidated Docs, Machine-Readable Manifests, and Applicability-Driven Gating**

### Key Architectural Provisions

1. **Dedicated Template Root (`templates/`)**:
   * Scaffolding archetypes are maintained in `templates/` rather than cluttering `apps/` or `building-blocks/` before real implementations exist.
   * Four archetypes: `templates/reference-application/`, `templates/pattern-example/`, `templates/platform-component/`, and `templates/template-artifact/`.

2. **Reference Artifact Manifest (`artifact.json`)**:
   * Every future artifact declares its architectural metadata in a standard JSON manifest:
     * `name`: Unique kebab-case artifact identifier.
     * `tier`: Integer `1`, `2`, `3`, or `4`.
     * `status`: `"planned"`, `"experimental"`, `"implemented"`, `"validated"`, `"accepted"`, or `"deprecated"`.
     * `languages`: Array of programming languages (e.g. `["python"]`).
     * `local_first_mode`: `"A"` (Offline Local), `"B"` (Local-First), `"C"` (Cloud-Comparable), or `null`.
     * Taxonomy references: `application_domains`, `intelligence_patterns`, `architecture_patterns` referencing Phase 0 taxonomy.
   * Evaluated and verified via Python standard library `json` (zero external dependencies).

3. **Consolidated Documentation Strategy**:
   * Rather than spawning dozens of single-topic markdown files, Tier 1 consolidates concerns logically:
     * `docs/requirements.md`: Combines problem statement, actors, FRs, measurable NFRs, constraints, and acceptance criteria.
     * `docs/architecture.md`: Combines system context, components, data flow, trust boundaries/security, AI architecture (model boundary, prompt path, structured output validation), and ADR references.
     * `docs/quality.md`: Combines test strategy, AI evaluation plan (if probabilistic behavior exists), Gate A–J assessment, and structured evidence record.
   * Tiers 2, 3, and 4 use a single, rich `README.md`.

4. **Quality Gate Applicability & Tier Semantics**:
   * Gates A through J from [`QUALITY-GATES.md`](../QUALITY-GATES.md) remain the sole authoritative quality gates.
   * Artifact tier describes the artifact's purpose, scope, and expected architectural evidence/rigor; it is **not** a maturity, quality, or production-readiness ranking. A Tier 3 platform component may be highly mature and production-grade; a Tier 1 reference application does not automatically satisfy Gate J.
   * Roadmap phases describe *when* capabilities are introduced, whereas artifact tiers describe *what kind* of artifact is produced.
   * Gate D (AI Evaluation) is marked **NOT APPLICABLE** for deterministic components.
   * Gate F (Observability & Telemetry) is scaled to runnable services; static templates mark it **NOT APPLICABLE**.
   * Gate G (Performance & Sizing) is scaled to applications with runtime serving constraints.
   * Gate J (Production Readiness & Resilience) is evaluated strictly from evidence; Tier 1 does NOT imply automatic production readiness.

5. **Strict Deferrals**:
   * All AI capabilities (Ollama, cloud SDKs, RAG, agents, MCP, tools, workflows) are deferred to Phase 4+.
   * Scaffolding CLI generators (`create-reference-app.py`) are deferred; copy-based templating is sufficient.

---

## 6. Consequences

### Positive Consequences
* Provides future engineers and AI agents with clear, unambiguous templates for any new artifact.
* Enables deterministic automated repository validation (`scripts/validate.py`) of declared tiers and required files.
* Eliminates boilerplate bureaucracy while ensuring enterprise architectural rigor for Tier 1 systems.
* Maintains 100% technology and AI framework neutrality.

### Negative Consequences & Trade-offs
* Requires template copyists to manually rename identifiers and resolve instructional prompts.
* Authors must understand the applicability matrix to properly designate `NOT APPLICABLE` gates without guessing.

---

## 7. Compliance with Quality Gates

* **Gate A — Architecture & Structural Boundaries**: Formalizes the four-tier reference architecture, enforces clear component boundaries, and establishes the manifest schema.
* **Gate B — Code Quality & Type Safety**: Source code of validators, templates, and tests adheres strictly to Python type safety and linting standards.
* **Gate C — Software Testing**: Validated via automated unit tests in `building-blocks/python/tests/test_templates.py` with hermetic test fixtures.
* **Gate H — Documentation & Architectural Integrity**: ADR-0002 documents drivers, decisions, consequences, and deferrals; verified via `scripts/validate-docs.py`.
