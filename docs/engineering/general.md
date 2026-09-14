# General Engineering Principles & Architecture Complexity Rule

## 1. Executive Purpose

This document defines the core software engineering principles that apply across all programming languages, reference applications, and platform components in this repository.

Our primary goal is **clarity, testability, and engineering credibility**. We prioritize robust, readable software over architectural ceremony.

---

## 2. The Architecture Complexity Rule

> [!CRITICAL]
> **THE ARCHITECTURE COMPLEXITY RULE**  
> **Use the simplest architecture that satisfies the application's functional requirements, non-functional requirements (NFRs), quality tier, security boundaries, and expected evolution.**  
> Do not reward architectural ceremony for its own sake.

Architectural complexity introduces maintenance overhead, operational failure modes, and cognitive friction. Simpler alternatives must always be the default baseline.

### Justification Matrix for Architectural Patterns

The following patterns require explicit architectural justification (via an approved Architecture Decision Record in `adr/` or documented NFR in the application's architecture specification):

| Complex Pattern | Simpler Default Baseline | Required Justification Criteria |
| :--- | :--- | :--- |
| **Microservices Sprawl** | Modular Monolith | Independent deployment cadence, distinct polyglot runtime boundaries, or disparate scaling bottlenecks. |
| **Distributed Message Brokers (Kafka, RabbitMQ)** | In-process queue / database polling / async tasks | High-throughput decoupled event streams exceeding database write limits or multi-consumer broadcast. |
| **Model Gateway Service** | Direct port adapter | Multi-provider routing, centralized rate limiting, tenant token quotas, or enterprise cost control. |
| **Event Sourcing / CQRS** | Relational state model + audit log | Formal immutable audit requirements, temporal state reconstruction, or extreme read/write divergence. |
| **Distributed Sagas** | Local ACID database transaction | Transactions spanning multiple autonomous, decoupled service boundaries. |
| **Distributed Cache (Redis cluster)** | In-memory cache with eviction | Multi-instance cache sharing, distributed session memory, or persistent embedding caching. |
| **Kubernetes Clusters** | Docker Compose / single container runtime | Multi-node autoscaling on GPU queue depth or enterprise cloud deployment tier (Tier 1 Phase 12+). |

---

## 3. Core Software Engineering Principles

### 3.1 Simplicity Before Abstraction
* Do not introduce abstraction layers, factories, or indirection before there is concrete proof of necessity.
* Three concrete implementations justify an abstraction; two implementations warrant observation; one implementation requires only clean, direct code.
* Do not mandate Clean / Hexagonal Architecture ceremony for small, 200-line pattern examples (Tier 2). Reserve multi-layer ceremony for complex Reference Applications (Tier 1).

### 3.2 Explicit Boundaries & Separation of Concerns
* Domain logic must remain cleanly decoupled from external frameworks, databases, and third-party SDKs.
* Business workflows orchestrate domain entities; persistence adapters store domain entities; controllers translate external payloads into domain commands.
* Each module must have a single, cohesive responsibility.

### 3.3 Composition Over Inheritance
* Favor object composition, dependency injection, and interface implementation over deep class inheritance hierarchies.
* Avoid speculative abstract base classes that attempt to anticipate future framework behavior.

### 3.4 Defensive Handling of External Data
* All external data—HTTP request payloads, database query outputs, webhooks, and **especially AI model completions**—must be treated as untrusted.
* Validate external payloads at the boundary using strict schemas (Pydantic, Zod, strongly typed records). Once inside the domain boundary, trust the validated domain entities.

### 3.5 Deterministic Logic for Deterministic Rules
* Never delegate deterministic business rules, arithmetic, sorting, filtering, or authorization checks to probabilistic foundation models.
* Use AI models for unstructured natural language interpretation, contextual synthesis, and semantic extraction; use deterministic code for business invariants.

### 3.6 Explicit Side Effects & Immutability
* Prefer immutable data structures (e.g., Python frozen dataclasses, C# `record` types, TypeScript `readonly` types) for value objects and data transfer objects.
* Functions should avoid hidden side effects. State-mutating operations must be named explicitly (`update_status()`, `record_transaction()`).

### 3.7 Dependency Injection Where Justified
* Use constructor dependency injection to pass ports and infrastructure adapters into application use cases.
* Avoid global service locators or hidden singletons that make automated unit testing impossible without monkey-patching.

### 3.8 Secure & Observable by Default
* Secure defaults: Fail closed, enforce least privilege, redact sensitive data from logs, and validate inputs before processing.
* Observable defaults: Emit structured context, correlate requests via trace IDs, and record operation latency and token consumption.
