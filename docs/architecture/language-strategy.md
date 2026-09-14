# Programming Language Strategy & Polyglot Boundaries

## 1. Executive Philosophy

A critical anti-pattern in enterprise reference repositories is **reckless language duplication**: attempting to build every reference application across Python, C#, TypeScript, and Java merely to demonstrate language coverage. This practice creates severe maintenance debt, diverts focus from architectural depth, and results in superficial, copy-pasted implementations.

This repository enforces a **Purpose-Driven Language Strategy**:
* **Architecture Transcends Syntax**: Sound architecture, clean boundaries, robust evaluations, and disciplined error handling are more important than multilingual syntax coverage.
* **Specialized Role Allocation**: Each language is applied where its enterprise ecosystem provides distinctive architectural value.
* **Contract-First Interoperability**: Across service boundaries, systems interact via standard network contracts (OpenAPI, JSON Schema, Protobuf, OpenTelemetry), ensuring polyglot flexibility without code duplication.

---

## 2. Language Classification: Primary vs. Secondary

The repository categorizes supported languages into **Primary Implementation Languages** and an **Approved Secondary Implementation Language**:

```
                       Language Governance Classification
                       
 ┌────────────────────────────────────────────────────────────────────────┐
 │ PRIMARY IMPLEMENTATION LANGUAGES                                       │
 │ Formally governed across core templates and Phase 1 engineering rules │
 ├────────────────────────────────────────────────────────────────────────┤
 │ • Python (3.11+)          AI-native pipelines, RAG, evals, ML tooling  │
 │ • .NET / C#               Enterprise APIs, services, saga workflows   │
 │ • TypeScript (Node 20+)   Web frontends, streaming, browser clients    │
 └────────────────────────────────────────────────────────────────────────┘
 ┌────────────────────────────────────────────────────────────────────────┐
 │ APPROVED SECONDARY IMPLEMENTATION LANGUAGE                             │
 │ Applied selectively where JVM/Spring architectural value is proven     │
 ├────────────────────────────────────────────────────────────────────────┤
 │ • Java                    Selective enterprise integrations & JVM ETL │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Primary Implementation Languages

### Python (3.11+)
* **Primary Scope**: Preferred where justified for:
  * AI-native services and agents.
  * Machine learning and model tooling.
  * Evaluation harnesses and benchmark scoring.
  * Data science, chunking algorithms, and vector mathematics.
  * AI ecosystem integration and local model adapters.

### .NET / C#
* **Runtime & Language Baseline**: **.NET using modern supported C# versions** (with .NET 8 LTS as the current enterprise baseline).
* **Primary Scope**: Preferred where justified for:
  * High-performance enterprise APIs and microservices.
  * Core business systems, transactional domain logic, and saga orchestrators.
  * Integration services and distributed systems.
  * Microsoft enterprise ecosystem integration (e.g., Semantic Kernel).
  * Enterprise architecture reference examples.

### TypeScript (Node 20+)
* **Primary Scope**: Preferred where justified for:
  * Web frontend demonstration interfaces and client UIs.
  * Node.js-based services where asynchronous event I/O is justified.
  * Browser integrations and lightweight edge proxies.
  * Real-time client applications and WebSocket audio/token streaming.

---

## 4. Java Governance (Approved Secondary Language)

**Java** is designated as an **Approved Secondary Implementation Language**.

* **Justification Requirement**: Java is used only when a reference implementation demonstrates meaningful enterprise architecture value, such as:
  * JVM enterprise ecosystem integration.
  * Spring-based enterprise architectures (e.g., Spring AI).
  * Enterprise integration patterns with legacy message backbones or ERP/ESB connectors.
  * Polyglot architectural comparison against .NET or Python baselines.
* **No Universal Java Requirement**: Java coverage is **not** required for every repository standard, reference application, or building block.
* **Just-in-Time Governance**: Detailed Java engineering standards, linting rules, and CI configs do not belong in Phase 1; they will be defined just-in-time when the first reference implementation requiring the JVM ecosystem is formally proposed via an approved ADR.

---

## 5. Policy on Multi-Language Implementations

Re-implementing a reference application in multiple programming languages is permitted **only** when all of the following conditions are met:

1. **Distinct Architectural Pattern**: The alternative implementation demonstrates a fundamentally different, widely adopted enterprise pattern or framework (e.g., demonstrating .NET Semantic Kernel with typed dependency injection alongside a Python LangGraph agent).
2. **Contract Parity**: Both implementations must conform to identical API contracts and satisfy the exact same evaluation datasets (`eval_dataset.jsonl`).
3. **Idiomatic Design**: The code must be native and idiomatic to the host language rather than a mechanical line-by-line translation.
4. **ADR Justification**: The multi-language decision must be documented in a dedicated ADR in `adr/` justifying the long-term maintenance commitment.

---

## 6. Baseline Coding Standards per Primary Language

Detailed standards are formalized in Phase 1 for the primary languages:

| Standard | Python | .NET (C#) | TypeScript |
| :--- | :--- | :--- | :--- |
| **Runtime / Version** | Python 3.11+ | .NET 8 LTS (modern supported C#) | Node 20+ / Modern ECMAScript |
| **Type Safety** | `mypy --strict` | Nullable reference types enabled | `"strict": true` |
| **Data Validation** | Pydantic v2 | Strongly typed records / FluentValidation | Zod |
| **Formatting/Lint** | `ruff` | `dotnet format` | `eslint` + `prettier` |
| **Test Framework** | `pytest` | `xUnit` + `FluentAssertions` | `vitest` |
| **Telemetry** | `opentelemetry-api` | `OpenTelemetry.Api` | `@opentelemetry/api` |
