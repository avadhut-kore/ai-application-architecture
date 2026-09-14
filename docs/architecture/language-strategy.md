# Programming Language Strategy & Polyglot Boundaries

## 1. Executive Philosophy

A critical anti-pattern in enterprise reference repositories is **reckless language duplication**: attempting to build every reference application across Python, C#, TypeScript, and Java merely to demonstrate language coverage. This practice creates severe maintenance debt, diverts focus from architectural depth, and results in superficial, copy-pasted implementations.

This repository enforces a **Purpose-Driven Language Strategy**:
* **Architecture Transcends Syntax**: Sound architecture, clean boundaries, robust evaluations, and disciplined error handling are more important than multilingual syntax coverage.
* **Specialized Role Allocation**: Each language is applied where its enterprise ecosystem provides distinctive architectural value.
* **Contract-First Interoperability**: Across service boundaries, systems interact via standard network contracts (OpenAPI, JSON Schema, Protobuf, OpenTelemetry), ensuring polyglot flexibility without code duplication.

---

## 2. Language Role Allocation

```
                            Language Role Allocation Matrix
                            
 ┌───────────────────────────┬────────────────────────────────────────────────────────┐
 │ Programming Language      │ Designated Enterprise Role & Architectural Scope       │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **Python (3.11+)**        │ Primary AI-Native Language                             │
 │                           │ • RAG pipelines, chunking, and vector index operations │
 │                           │ • Autonomous agent execution loops and tool sandboxes  │
 │                           │ • AI evaluation harnesses and benchmark scoring        │
 │                           │ • Machine learning model integration and data science  │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **.NET (C# 8.0+)**        │ Enterprise Services & Mission-Critical APIs            │
 │                           │ • High-throughput enterprise REST and gRPC gateways    │
 │                           │ • Transactional domain services and saga orchestrators │
 │                           │ • Microsoft enterprise ecosystem (Semantic Kernel)     │
 │                           │ • Strongly typed enterprise messaging and domain events│
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **TypeScript (Node 20+)** │ Frontend & Real-Time Streaming                         │
 │                           │ • Interactive web demonstration interfaces and UIs     │
 │                           │ • Real-time WebSocket streaming (Voice & token stream) │
 │                           │ • Browser-based and edge proxy integrations            │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **Java (21 LTS)**         │ Selective Enterprise Integration                       │
 │                           │ • Applied only where it demonstrates meaningful enterprise│
 │                           │   architecture value (e.g., Spring AI enterprise ETL   │
 │                           │   or legacy enterprise backbone integration).          │
 └───────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Policy on Multi-Language Implementations

Re-implementing a reference application in multiple programming languages is permitted **only** when all of the following conditions are met:

1. **Distinct Architectural Pattern**: The alternative implementation demonstrates a fundamentally different, widely adopted enterprise pattern or framework (e.g., demonstrating .NET Semantic Kernel with typed dependency injection alongside a Python LangGraph agent).
2. **Contract Parity**: Both implementations must conform to identical API contracts and satisfy the exact same evaluation datasets (`eval_dataset.jsonl`).
3. **Idiomatic Design**: The code must be native and idiomatic to the host language rather than a mechanical line-by-line translation.
4. **ADR Justification**: The multi-language decision must be documented in a dedicated ADR in `adr/` justifying the long-term maintenance commitment.

---

## 4. Coding & Tooling Standards per Language

| Standard | Python | .NET (C#) | TypeScript | Java |
| :--- | :--- | :--- | :--- | :--- |
| **Type Safety** | `mypy --strict` | Nullable reference types enabled | `"strict": true` | Strict compiler flags |
| **Data Validation**| Pydantic v2 | System.ComponentModel / FluentValidation | Zod | Jakarta Bean Validation |
| **Formatting/Lint**| `ruff` | `dotnet format` | `eslint` + `prettier` | `spotless` / Checkstyle |
| **Test Framework** | `pytest` | `xUnit` + `FluentAssertions` | `vitest` | `JUnit 5` + `AssertJ` |
| **Telemetry** | `opentelemetry-api` | `OpenTelemetry.Api` | `@opentelemetry/api` | `opentelemetry-api` |
