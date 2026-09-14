# Architectural Decisions & Review Summaries

## 1. Domain Scope

The `docs/decisions/` directory houses high-level architectural review summaries, cross-cutting architectural position papers, phase completion audit reports, and security audit sign-offs.

Specific, numbered architectural choices regarding libraries, patterns, and frameworks are recorded as formal Architecture Decision Records in the root **[`adr/`](file:///Users/avadhutkore/Documents/code/products/ai-application-architecture/adr/README.md)** directory.

---

## 2. Directory Contents & Artifacts

* **Phase Audit Reports**: Verifiable evidence dossiers compiled at the conclusion of major roadmap phases (e.g., Phase 13 Architecture Hardening Audit).
* **Cross-Cutting Position Papers**: Long-form evaluations of emerging architectural paradigms (e.g., *"Comparative Analysis of Dedicated Vector Stores vs. Relational Vector Extensions"*).
* **Vendor & Framework Audits**: Formal security assessments and threat boundary reviews of external runtime dependencies.

---

## 3. Relationship to ADRs

```
┌────────────────────────────────────────────────────────┐
│ adr/                                                   │
│ Discrete, numbered architectural decisions             │
│ (e.g., ADR-0002: Adopt Ollama as Local AI Runtime)     │
└───────────────────────────┬────────────────────────────┘
                            │ Referenced by
┌───────────────────────────▼────────────────────────────┐
│ docs/decisions/                                        │
│ Comprehensive review summaries, audit reports,         │
│ and multi-phase architectural assessments              │
└────────────────────────────────────────────────────────┘
```
