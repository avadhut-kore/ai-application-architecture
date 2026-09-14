# Reference Artifact Templates (`templates/`)

## 1. Executive Purpose

This directory contains the canonical reference artifact templates for the `ai-application-architecture` repository.

To prevent both shallow documentation on complex systems and excessive ceremony on simple mechanisms, this repository classifies all reference implementations into **Four Reference Tiers**:

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ TIER 1: REFERENCE APPLICATION                                          │
 │ Full end-to-end production architecture with complete enterprise rigor │
 ├────────────────────────────────────────────────────────────────────────┤
 │ TIER 2: PATTERN EXAMPLE                                                │
 │ Focused, runnable demonstration of a single pattern or mechanism       │
 ├────────────────────────────────────────────────────────────────────────┤
 │ TIER 3: PLATFORM COMPONENT                                             │
 │ Reusable capability, adapter, middleware, or infrastructure building block
 ├────────────────────────────────────────────────────────────────────────┤
 │ TIER 4: TEMPLATE ARTIFACT                                              │
 │ Scaffolding archetype accelerating development; non-production          │
 └────────────────────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Template System vs. Tier 4 Clarification**  
> * **Reference Artifact Templates**: The overall governance and archetype system defined in this `templates/` directory used to bootstrap Tier 1, 2, 3, or 4 implementations.  
> * **Tier 4 — Template Artifact**: The specific artifact classification for a reusable project skeleton, archetype, or starter kit that does not itself represent a runnable production application.

> [!NOTE]
> **Artifact Tier vs. Maturity & Production Readiness**  
> Artifact tier describes the artifact's purpose, scope, and expected architectural evidence/rigor. It is **not** a maturity, quality, or production-readiness ranking.  
> * A **Tier 3 Platform Component** may be highly mature, hardened, and production-grade.  
> * A **Tier 1 Reference Application** does not automatically satisfy Gate J (Production Readiness & Resilience).  
> * **Roadmap Phase** describes *when* capabilities are introduced. **Artifact Tier** describes *what kind* of artifact is being produced. Roadmap phases do not map directly to artifact tiers.

---

## 2. Directory Structure

```text
templates/
├── README.md                      # This governance and usage document
├── reference-application/         # Tier 1 — Reference Application template
│   ├── artifact.json              # Machine-readable architectural manifest
│   ├── README.md                  # Executive summary & quick-start entry point
│   └── docs/
│       ├── requirements.md        # Problem statement, actors, FRs, measurable NFRs
│       ├── architecture.md        # Components, data flow, trust boundaries, AI arch, ADRs
│       └── quality.md             # Testing, AI evaluation, Gate A–J assessment, evidence
├── pattern-example/               # Tier 2 — Pattern Example template
│   ├── artifact.json              # Machine-readable architectural manifest
│   └── README.md                  # Self-contained pattern guide, run steps, trade-offs
├── platform-component/            # Tier 3 — Platform Component template
│   ├── artifact.json              # Machine-readable architectural manifest
│   └── README.md                  # Responsibilities, ports, integration, failure modes
└── template-artifact/             # Tier 4 — Template Artifact template
    ├── artifact.json              # Machine-readable architectural manifest
    └── README.md                  # Archetype guide, usage instructions, non-production notice
```

---

## 3. Reference Artifact Manifest (`artifact.json`)

Every reference artifact in the repository must include a root `artifact.json` file. This manifest allows the repository validator (`scripts/validate.py`) to deterministically verify structural completeness, taxonomy compliance, and applicable quality gates without brittle regex parsing.

### Standard Schema & Fields

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "name": "artifact-name",
  "tier": 1,
  "status": "planned",
  "languages": ["python"],
  "local_first_mode": "B",
  "application_domains": ["structured-extraction"],
  "intelligence_patterns": ["structured-generation"],
  "architecture_patterns": ["hexagonal"]
}
```

| Field | Type | Allowed Values | Description |
| :--- | :---: | :--- | :--- |
| `name` | `string` | Lowercase alphanumeric + hyphens (`kebab-case`) | Unique identifier for the artifact. |
| `tier` | `integer` | `1`, `2`, `3`, `4` | Declared reference implementation tier. |
| `status` | `string` | `"planned"`, `"experimental"`, `"implemented"`, `"validated"`, `"accepted"`, `"deprecated"` | Current lifecycle status of the artifact. |
| `languages` | `array[string]`| Supported languages (e.g. `["python"]`, `[".net"]`, `["typescript"]`, `["java"]`) | Programming language(s) utilized. |
| `local_first_mode` | `string` or `null` | `"A"` (Offline Local), `"B"` (Local-First), `"C"` (Cloud-Comparable), or `null` | Operational mode under [`docs/architecture/local-first.md`](../docs/architecture/local-first.md). |
| `application_domains` | `array[string]`| Phase 0 taxonomy identifiers | Target business domain(s) from [`docs/architecture/taxonomy.md`](../docs/architecture/taxonomy.md). |
| `intelligence_patterns` | `array[string]`| Phase 0 taxonomy identifiers | Demonstrated intelligence pattern(s) from [`docs/architecture/taxonomy.md`](../docs/architecture/taxonomy.md). |
| `architecture_patterns` | `array[string]`| Phase 0 taxonomy identifiers | Architectural design pattern(s) from [`docs/architecture/taxonomy.md`](../docs/architecture/taxonomy.md). |

---

## 4. Quality Gate Applicability Matrix

Authoritative quality gate names and definitions are defined exclusively in [`QUALITY-GATES.md`](../QUALITY-GATES.md) (Gates A through J). Templates interpret how each gate applies across the four reference implementation tiers:

| Authoritative Quality Gate | Tier 1 (Reference App) | Tier 2 (Pattern Example) | Tier 3 (Platform Component) | Tier 4 (Template Artifact) |
| :--- | :---: | :---: | :---: | :---: |
| **Gate A — Architecture & Structural Boundaries** | **Mandatory** | Recommended / Scaled | **Mandatory** | **Mandatory** (Structure) |
| **Gate B — Code Quality & Type Safety** | **Mandatory** (Strict typing & lint) | **Mandatory** (Strict typing & lint) | **Mandatory** (Strict typing & lint) | **Mandatory** (Clean scaffold) |
| **Gate C — Software Testing** | **Mandatory** ($\ge 85\%$ coverage) | **Mandatory** (Hermetic unit tests) | **Mandatory** ($\ge 85\%$ coverage) | Recommended baseline |
| **Gate D — AI Evaluation** | **Mandatory** (if AI behavior exists) | Scaled (if AI demonstrated) | Recommended (if probabilistic) | **Not Applicable** |
| **Gate E — Security & Safety** | **Mandatory** (Threat model + audit) | Scaled / Risk-based | **Mandatory** (Boundary validation) | **Mandatory** (Zero secrets) |
| **Gate F — Observability & Telemetry** | **Mandatory** (OTel GenAI spans) | Optional / Scaled | **Mandatory** (if runtime middleware) | **Not Applicable** |
| **Gate G — Performance & Sizing** | **Mandatory** (TTFT, streaming, sizing)| Optional / Scaled | Recommended (Low overhead) | **Not Applicable** |
| **Gate H — Documentation & Architectural Integrity** | **Mandatory** (Docs, C4, link check)| **Mandatory** (README, diagrams) | **Mandatory** (API docs, contracts) | **Mandatory** (Usage, non-prod notice) |
| **Gate I — Demo & Operational Verification** | **Mandatory** (Mode A/B, demo $< 5$ min)| **Mandatory** (Mode A/B demo script) | Recommended (Integration sample) | **Not Applicable** |
| **Gate J — Production Readiness & Resilience** | **Mandatory** (Resilience & fault injection)| Scaled (Basic error handling) | Recommended (Resilience support) | **Not Applicable** |

---

## 5. How to Create a New Reference Artifact

Follow this standard workflow when bootstrapping a new reference implementation:

```text
1. Select Target Tier (1, 2, 3, or 4) based on scope and architectural purpose
                           ↓
2. Copy the corresponding template from templates/<archetype>/ to target directory:
   - Tier 1: apps/<app-name>/
   - Tier 2: apps/patterns/<pattern-name>/ or examples/<pattern-name>/
   - Tier 3: building-blocks/<language>/<component-name>/ or platform/<component-name>/
   - Tier 4: templates/<archetype-name>/
                           ↓
3. Customize artifact.json: Set name, tier, status ("planned"), languages, mode, and taxonomy
                           ↓
4. Resolve Instructional Prompts: Replace guidance prompts with concrete system specifications
                           ↓
5. Implement Domain, Application, and Ports/Adapters (Domain logic first, ports second)
                           ↓
6. Write Deterministic Tests & AI Evaluation Suites (Unit tests + eval_dataset.jsonl where applicable)
                           ↓
7. Run Repository Validation: python3 scripts/validate.py
                           ↓
8. Produce Evidence Record & Submit for Independent Architectural Review
```
