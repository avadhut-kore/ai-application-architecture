# Reference Implementation Standards & Tiered Contract

## 1. Executive Purpose

Not every implementation in this repository serves the same purpose or requires the same level of architectural ceremony. Forcing a monolithic standard on every component leads to either shallow documentation for complex systems or excessive overhead for simple examples.

This document establishes **Four Reference Implementation Tiers**:

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
 │ TIER 4: TEMPLATE                                                       │
 │ Scaffolding archetype accelerating development; non-production          │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Tier Specifications

### Tier 1 — Reference Application
* **Intent**: A comprehensive, production-grade reference architecture demonstrating how an enterprise AI capability is designed, implemented, tested, evaluated, secured, observed, and operated.
* **Scope**: Located in `apps/<app-name>/`.
* **Expected Deliverables**:
  * `README.md` containing executive summary, business problem statement, and quick-start instructions.
  * Formal Functional Requirements (FR) and Non-Functional Requirements (NFR).
  * Architecture specification with renderable Mermaid component and sequence diagrams.
  * Hexagonal / Clean Architecture code structure (Domain, Application, Infrastructure).
  * Architecture Decision Records (ADRs) for significant architectural choices.
  * Deterministic unit tests with in-memory doubles ($\ge 85\%$ statement coverage).
  * Integration tests verifying local container and provider wiring.
  * Automated AI evaluation suite with versioned `eval_dataset.jsonl`.
  * Security threat model evaluating relevant OWASP Top 10 for LLMs vectors.
  * OpenTelemetry GenAI semantic tracing and metric instrumentation.
  * Resilience patterns (timeouts, retries, circuit breaking, fallbacks where applicable).
  * Single-command local execution via `docker-compose.yml`.
  * Verified interactive demo script executable in $< 5$ minutes.
  * Explicit documentation of architectural trade-offs and known limitations.

### Tier 2 — Pattern Example
* **Intent**: A focused, lightweight, and runnable implementation demonstrating a single intelligence pattern (e.g., Cross-Encoder Re-ranking) or architectural pattern (e.g., Asynchronous Worker queue).
* **Scope**: Located in `apps/patterns/<pattern-name>/` or `examples/<pattern-name>/`.
* **Expected Deliverables**:
  * Concise `README.md` explaining the pattern, problem statement, and execution instructions.
  * Clean, idiomatic source code demonstrating the pattern without extraneous enterprise plumbing.
  * Deterministic unit tests demonstrating expected behavior and edge cases.
  * Local execution instructions (e.g., standalone script or minimal container).
  * Does **not** require full ADR suites, extensive threat models, or complex multi-tier deployment manifests.

### Tier 3 — Platform Component
* **Intent**: A reusable architectural building block, provider adapter, middleware, or shared infrastructure service.
* **Scope**: Located in `building-blocks/` or `platform/<component-name>/`.
* **Expected Deliverables**:
  * Explicit interface and contract specifications (ports).
  * Documented responsibilities and clear boundary definitions.
  * Explicit failure modes, exception hierarchies, and recovery behaviors.
  * Integration guidelines and code examples showing consumption by applications.
  * Unit tests covering normal, boundary, and failure conditions.
  * Telemetry integration documentation where the component manages cross-cutting concerns.

### Tier 4 — Template
* **Intent**: Canonical scaffolding, archetype directories, and governance skeletons designed to accelerate the creation of new reference applications or components.
* **Scope**: Located in `apps/_template/` or `platform/_template/`.
* **Expected Deliverables**:
  * Annotated directory layout demonstrating recommended layer structure.
  * Standard configuration templates (`.env.example`).
  * Scaffolding scripts and baseline test harnesses.
  * Clear notice stating that templates are **scaffolding archetypes** and must not be cited as production implementations until completed.

---

## 3. Tier Deliverables Matrix

| Deliverable | Tier 1 (Reference App) | Tier 2 (Pattern Example) | Tier 3 (Platform Component) | Tier 4 (Template) |
| :--- | :---: | :---: | :---: | :---: |
| **Problem Statement & Scope** | Mandatory | Mandatory | Mandatory | Mandatory |
| **Architecture Specification & Diagram** | Mandatory | Recommended | Recommended | Optional |
| **Source Code** | Mandatory | Mandatory | Mandatory | Scaffolding |
| **Deterministic Unit Tests** | Mandatory ($\ge 85\%$) | Mandatory | Mandatory | Example Stub |
| **AI Evaluation Suite & Dataset** | Mandatory | Optional | Conditional | Example Stub |
| **OpenTelemetry Instrumentation** | Mandatory | Optional | Mandatory | Example Stub |
| **Security & Threat Model** | Mandatory | Optional | Recommended | Optional |
| **Local Docker Execution** | Mandatory | Optional / Script | Mandatory | Mandatory |
| **ADR Documentation** | Mandatory | Optional | Recommended | Optional |
| **Documented Trade-offs & Limits** | Mandatory | Mandatory | Mandatory | Optional |

---

## 4. Quality Gate Applicability by Tier

Compliance with [QUALITY-GATES.md](../../QUALITY-GATES.md) is scaled to the respective tier:
* **Tier 1 (Reference Application)**: Must pass **all** Quality Gates (Gates A through J).
* **Tier 2 (Pattern Example)**: Must pass Gates B (Code), C (Testing), H (Documentation), and I (Local Execution).
* **Tier 3 (Platform Component)**: Must pass Gates A (Architecture), B (Code), C (Testing), F (Observability), and H (Documentation).
* **Tier 4 (Template)**: Must pass Gate B (Code Quality / Linting) and Gate H (Documentation).
