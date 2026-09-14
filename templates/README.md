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
  "application_domains": ["horizontal-enterprise"],
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

Authoritative quality gates are defined in [`QUALITY-GATES.md`](../QUALITY-GATES.md) (Gates A through J). The tier classification defines the expected scope and applicability of evidence:

| Quality Gate | Tier 1 (Reference App) | Tier 2 (Pattern Example) | Tier 3 (Platform Component) | Tier 4 (Template Artifact) |
| :--- | :---: | :---: | :---: | :---: |
| **Gate A: Architecture & Design Integrity** | **Mandatory** | Recommended / Scaled | **Mandatory** | **Mandatory** (Structure) |
| **Gate B: Local-First Execution Integrity** | **Mandatory** (Mode A or B) | **Mandatory** (Mode A or B) | **Mandatory** (Zero cloud locks) | **Mandatory** (Safe defaults) |
| **Gate C: Deterministic Software Quality** | **Mandatory** ($\ge 85\%$ coverage) | **Mandatory** (Focused tests) | **Mandatory** (Contracts/doubles) | Recommended (Syntax/lint) |
| **Gate D: AI Quality & Evaluation** | **Mandatory if AI behavior exists** | **Applicable if AI demonstrated** | **Applicable if AI present**; else N/A | **Not Applicable** |
| **Gate E: Security, Trust & Safety** | **Mandatory** (Threat model + controls) | Risk-based / Scaled | **Mandatory** (Boundary isolation) | **Mandatory** (Zero secrets) |
| **Gate F: Observability & Telemetry** | **Mandatory** (OTel GenAI conventions) | Optional / Scaled | **Mandatory** if runtime middleware | **Not Applicable** |
| **Gate G: Data Management & Hygiene** | **Mandatory if persistence exists** | Optional / Scaled | Applicable if managing storage | **Not Applicable** |
| **Gate H: API Design & Interoperability** | **Mandatory** (REST/Streaming) | Recommended | **Mandatory** (Ports/protocols) | Optional |
| **Gate I: Operational Excellence & Runbooks** | **Mandatory** (Demo $< 5$ min) | **Mandatory** (Runnable script) | **Mandatory** (Integration sample) | **Not Applicable** |
| **Gate J: Governance & Acceptance Discipline**| **Mandatory** (Evidence record) | **Mandatory** (Evidence record) | **Mandatory** (Evidence record) | **Mandatory** (Evidence record) |

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
