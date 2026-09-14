# Testing Strategy & Engineering Standards

This document establishes the testing architecture, standards, test double policies, and quality metrics across all implementations in the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Separation of Concerns: Software Testing vs. AI Evaluation**  
> In enterprise AI engineering, traditional software testing and AI behavioral evaluation are distinct disciplines:
> * **Software Testing (this document)**: Verifies deterministic behavior, error handling, invariants, contracts, schemas, security boundaries, and persistence logic using classical test assertions.
> * **AI Evaluation ([`ai-evaluation.md`](ai-evaluation.md))**: Assesses probabilistic model behavior, accuracy, relevance, hallucinations, and safety using golden datasets and automated scoring algorithms.
>
> Both disciplines are mandatory and complementary. Neither substitutes for the other.

---

## 1. Testing Portfolio & Pyramid

The repository enforces a risk-based testing pyramid that maximizes deterministic verification while controlling execution cost and execution time:

```
        ▲
       / \       End-to-End Tests (Smoke / Cross-Service Journeys)
      /   \      -------------------------------------------------
     /  ▲  \     Integration Tests (Testcontainers, Databases, HTTP)
    /  / \  \    -------------------------------------------------
   /  /   \  \   Contract & Boundary Tests (OpenAPI, Schemas, WireMock)
  /  /     \  \  -------------------------------------------------
 /  /       \  \ Unit Tests (Domain Logic, State Machines, Validators)
/────────────────\
```

| Test Layer | Purpose | Execution Speed | Dependencies | Required Tiers |
| :--- | :--- | :--- | :--- | :--- |
| **Unit** | Verify domain invariants, business rules, prompt templates, and schema parsing in isolation. | Fast (< 10ms per test) | Zero external I/O; in-memory test doubles only. | Tiers 1, 2, 3, 4 |
| **Contract** | Verify adherence to OpenAPI 3.1, JSON Schemas, and external API wire contracts. | Fast (< 50ms per test) | Schema validators, mock servers. | Tiers 1, 3 |
| **Integration** | Verify persistence adapters, caches, messaging queues, and real local model adapters. | Moderate (< 2s per test) | Testcontainers (PostgreSQL, Redis, local Ollama). | Tiers 1, 3 (Optional Tier 2) |
| **End-to-End** | Validate critical user journeys and API workflows from request entry to final response. | Slower (< 10s per test) | Full application stack running in Mode A or Mode B. | Tier 1 (Mandatory), Tier 3 |

---

## 2. Deterministic Testing vs. Probabilistic AI

1. **Deterministic Execution**:
   * Unit and integration test suites must yield identical results across repeated runs on any machine (`flaky = 0`).
   * Never execute live, unpinned probabilistic LLM calls inside unit tests.
   * Prompts, serialization, token limits, and response transformations must be asserted using deterministic test doubles.
2. **Deterministic Golden Tests**:
   * When testing LLM parsing adapters, pass fixed fixture responses (valid JSON, malformed JSON, markdown fences, empty strings) into the parser to verify deterministic resilience.

---

## 3. Test Doubles Policy (Fakes, Mocks, and Stubs)

Over-mocking produces brittle tests that pass while systems fail in production. This repository enforces strict boundaries for test doubles:

* **Use Fakes for In-Memory Infrastructure**:
  * Implement lightweight in-memory implementations of storage ports (`InMemoryDocumentStore`, `InMemoryVectorIndex`) for fast unit tests.
  * Keep fakes verified against the same contract tests as their real infrastructure counterparts.
* **Mocks Restricted to External Boundaries**:
  * Mocks or stubs are permitted **only** at external integration boundaries (e.g., remote HTTP API calls, third-party auth providers, billing endpoints).
  * Never mock internal domain entities, value objects, pure functions, or local database adapters where in-memory or containerized alternatives exist.
* **No Speculative or Fake AI Delays**:
  * Never simulate AI processing using `time.sleep()` or `Thread.sleep()` in test doubles. Return pre-canned, realistic fixtures immediately.

---

## 4. Code Coverage Policy (Coverage as a Risk Indicator)

> [!NOTE]
> **Coverage Philosophy**  
> High test coverage does not guarantee correctness, but low coverage guarantees unverified risk. Coverage metrics serve as a defect-prevention baseline, not an architectural vanity metric.

In accordance with [`QUALITY-GATES.md`](../../QUALITY-GATES.md) (Gate G3), minimum coverage thresholds are graduated by reference implementation tier:

| Reference Implementation Tier | Line Coverage | Branch Coverage | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Tier 1: Enterprise Reference App** | ≥ 80% | ≥ 75% | Automated CI gate (`pytest-cov`, `coverlet`, `jacoco`). |
| **Tier 2: Pattern Example** | ≥ 70% | ≥ 65% | Automated CI gate. |
| **Tier 3: Platform Component** | ≥ 85% | ≥ 80% | Automated CI gate (strictly audited). |
| **Tier 4: Enterprise Template** | ≥ 60% | ≥ 50% | Automated CI gate on scaffolded baseline. |

### Exclusion Rules
Coverage exclusions must be minimal and justified in writing:
* Auto-generated database migrations and client SDK stubs.
* Entry point bootstrapping code (`Program.cs` top-level statements, `main.py` CLI parser wiring).
* Pure DTO records with no behavior.

---

## 5. Test Organization & Naming Conventions

* **Colocation vs. Separate Test Trees**:
  * In Python: `tests/unit/`, `tests/integration/`, `tests/contract/`, and `tests/eval/`.
  * In .NET: `tests/Project.UnitTests/`, `tests/Project.IntegrationTests/`.
  * In TypeScript: `tests/unit/`, `tests/integration/`.
  * In Java: `src/test/java/` with subpackages matching production modules.
* **Standard Naming Convention**:
  * Tests must follow the `Method_Condition_ExpectedResult` or `should_ExpectedResult_when_Condition` pattern:
    * `CompleteAsync_WhenRateLimitExceeded_ThrowsTransientFailureException`
    * `should_ExtractStructuredEntities_when_PayloadIsValidJson`
* **Test Isolation & Independent Execution**:
  * Every test must be completely isolated and executable in any order or in parallel.
  * Shared global state or shared mutable database tables between tests is prohibited. Use transactional rollbacks or unique test run identifiers.
