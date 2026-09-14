# Programming Language Strategy & Polyglot Boundaries

## 1. Executive Philosophy

A common mistake in enterprise reference repositories is **reckless duplication**: attempting to re-implement every application in Python, C#, TypeScript, Go, and Java merely for the sake of language coverage. This leads to maintenance collapse, inconsistent feature sets, and diluted architectural focus.

This repository enforces a **Purpose-Driven Language Strategy**:
* Each programming language is assigned a designated architectural role based on industry ecosystem strength.
* Duplication of identical application logic across multiple languages is **strictly prohibited** unless explicitly justified by distinct enterprise architectural patterns.
* Applications interact across language boundaries using standard, contract-first protocols (REST, gRPC, Protobuf, OpenTelemetry).

---

## 2. Language Role Allocation Matrix

```
                             Language Role Allocation
                             
 ┌───────────────────────────┬────────────────────────────────────────────────────────┐
 │ Language & Runtime        │ Primary Enterprise Role & Architectural Scope          │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **Python (3.11+)**        │ Primary AI-Native Language                             │
 │                           │ • Complex RAG pipelines & chunking algorithms          │
 │                           │ • Agent loops, tool execution sandboxes, ReAct flows   │
 │                           │ • Evaluation harnesses, red-teaming, benchmark runners │
 │                           │ • Data science, vector math, and ML model integration  │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **.NET 8.0+ (C#)**        │ Enterprise Services & Core Business Architecture       │
 │                           │ • High-performance API gateways & microservices        │
 │                           │ • Transactional domain modeling & saga orchestrators   │
 │                           │ • Microsoft enterprise ecosystem & Semantic Kernel     │
 │                           │ • Strongly typed enterprise domain events & messaging  │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **TypeScript (Node 20+)** │ Full-Stack, Streaming & Client Applications            │
 │                           │ • Real-time WebSocket streaming (Voice & token stream) │
 │                           │ • Modern web frontend demonstration interfaces         │
 │                           │ • Lightweight edge proxies & JSON-schema UI validators │
 ├───────────────────────────┼────────────────────────────────────────────────────────┤
 │ **Java (21 LTS)**         │ Legacy Enterprise Integration                          │
 │                           │ • Spring AI enterprise integration blueprints          │
 │                           │ • High-throughput batch document ETL processing        │
 │                           │ • Legacy ERP/ESB connectivity patterns                 │
 └───────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. When Multiple Implementations Are Justified

Re-implementing a reference application or pattern in a second language is permitted **only** when all of the following criteria are satisfied:

1. **Unique Architectural Ecosystem Value**: The alternative language introduces a fundamentally different, widely adopted enterprise framework pattern (e.g., demonstrating .NET Semantic Kernel alongside Python LangGraph).
2. **Contract Consistency**: Both implementations must satisfy the exact same [Reference Implementation Contract](reference-implementation-standard.md) and pass identical evaluation datasets (`eval_dataset.jsonl`).
3. **No Copy-Paste Translating**: The implementation must be idiomatic to its host runtime (e.g., utilizing C# async streams, dependency injection, and record types rather than blindly copying Python idioms into C#).
4. **Formal ADR Approval**: The decision must be formally documented and approved in `adr/` justifying the ongoing maintenance overhead.

---

## 4. Cross-Language Communication & Avoiding Duplication

To prevent duplicate reimplementation of core platform services:

### 4.1 Shared Platform Services via Containers
Cross-cutting infrastructure—such as the Model Gateway, Ollama orchestration, PostgreSQL/pgvector, Redis, and OpenTelemetry collectors—lives in `platform/` as containerized microservices. Applications written in Python, .NET, or TypeScript consume these shared services via standard HTTP/gRPC contracts without reimplementing them.

### 4.2 Standardized Schema Contracts
All data interchange formats, tool schemas, and evaluation datasets are defined using language-agnostic formats:
* **API Contracts**: OpenAPI 3.1 specifications.
* **Tool Calling Schemas**: JSON Schema (Draft 2020-12).
* **Evaluation Scenarios**: JSON Lines (`.jsonl`).
* **High-Throughput IPC**: Protocol Buffers (`.proto`) where gRPC is required.

---

## 5. Coding Standards per Language

| Standard | Python | .NET (C#) | TypeScript | Java |
| :--- | :--- | :--- | :--- | :--- |
| **Type Safety** | `mypy --strict` | Nullable reference types | `"strict": true` | Strict compiler flags |
| **Validation** | Pydantic v2 | System.ComponentModel | Zod | Jakarta Bean Validation |
| **Lint / Format** | `ruff` | `dotnet format` | `eslint` + `prettier` | `spotless` / Checkstyle |
| **Testing** | `pytest` | `xUnit` + `FluentAssertions` | `vitest` | `JUnit 5` + `AssertJ` |
| **Telemetry** | `opentelemetry-api` | `OpenTelemetry.Api` | `@opentelemetry/api` | `opentelemetry-api` |
