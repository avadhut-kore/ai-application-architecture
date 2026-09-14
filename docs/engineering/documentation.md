# Documentation Standards & Quality Governance

This document establishes the documentation standards, tier-graduated requirements, Markdown quality rules, and link validation disciplines for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Documentation standards defined in this document satisfy [`Gate H (Documentation & Architectural Integrity)`](../../QUALITY-GATES.md#gate-h--documentation--architectural-integrity) and [`Gate A (Architecture & Structural Boundaries)`](../../QUALITY-GATES.md#gate-a--architecture--structural-boundaries) in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). In an enterprise architecture repository, documentation is an executable engineering artifact, not an afterthought.

---

## 1. Tier-Graduated Documentation Requirements

Documentation scope is strictly governed by the reference implementation tier to ensure proportional engineering rigor:

| Documentation Artifact | Tier 1: Reference App | Tier 2: Pattern Example | Tier 3: Platform Component | Tier 4: Enterprise Template |
| :--- | :--- | :--- | :--- | :--- |
| **README.md** | Mandatory (Comprehensive) | Mandatory (Focused) | Mandatory (Contract-focused) | Mandatory (Scaffold Guide) |
| **Problem Statement & Scope** | Mandatory (`README.md` / `SCOPE.md`) | Mandatory in README | Mandatory in README | Mandatory in README |
| **Architecture Document & C4** | Mandatory (`docs/architecture.md`) | Optional (Lightweight) | Mandatory | Recommended |
| **API Contract & Schemas** | Mandatory (OpenAPI 3.1) | Recommended | Mandatory | Recommended |
| **Setup & Local Execution Guide** | Mandatory (Mode A & B) | Mandatory (Mode A & B) | Mandatory | Mandatory |
| **Evaluation Report** | Mandatory (`latest_results.json`) | Mandatory (Curated) | Recommended | N/A |
| **Architecture Decision Records** | Mandatory (for key choices) | Optional | Mandatory (for API/wire) | Optional |

---

## 2. Anti-Sprawl & Single Authoritative Source Policy

To maintain long-term repository maintainability and prevent documentation divergence:

1. **One Authoritative Source Per Topic**:
   * Quality gate thresholds belong exclusively in [`QUALITY-GATES.md`](../../QUALITY-GATES.md).
   * Core architectural tenets belong exclusively in [`docs/architecture/principles.md`](../architecture/principles.md).
   * Local-first execution policies belong exclusively in [`docs/architecture/local-first.md`](../architecture/local-first.md).
2. **Mandatory Cross-Referencing**:
   * Application-specific documentation must cross-reference root architecture documents rather than duplicating text.
   * If a standard evolves, only the authoritative document must be updated.

---

## 3. Executable Markdown Quality Rules

All documentation files (`*.md`) must adhere to strict structural rules validated continuously in CI:

* **Strict Heading Hierarchy**:
  * Exactly one `#` (H1) title per document.
  * Never skip heading levels (e.g., jumping from `##` to `####` is prohibited; use `###`).
* **Closed Code Fences & Language Tags**:
  * Every triple-backtick fence must be properly closed.
  * Every code block must declare an explicit language identifier (`csharp`, `python`, `typescript`, `java`, `json`, `bash`, `yaml`, `mermaid`).
* **Zero Trailing Whitespace**:
  * Lines must not have trailing whitespace unless explicitly formatting a Markdown line break (two trailing spaces `  \n`).
* **Valid Relative Links**:
  * Every relative file link (such as links between documentation files) must resolve to an existing file in the repository.

---

## 4. Automated Documentation Validation

Documentation quality is mechanically verified via [`scripts/validate-docs.py`](../../scripts/validate-docs.py):

```bash
# Execute local documentation quality and link verification
python3 scripts/validate-docs.py
```

* **Zero Tolerance**: The validation script must exit with status `0` before any pull request is merged.
* **Checks Executed**:
  1. Internal markdown file link resolution (`.md` targets).
  2. Heading hierarchy continuity.
  3. Closed code block validation.
  4. Trailing whitespace detection.
