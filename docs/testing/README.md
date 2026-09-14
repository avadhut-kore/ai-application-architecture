# Software Testing Standards for AI Systems

## 1. Domain Scope

The `docs/testing/` directory defines the deterministic software testing strategy for AI applications in this repository. 

A disciplined separation is maintained between **Deterministic Software Testing** (verifying code, state machines, parsers, and error paths) and **Probabilistic AI Evaluation** (scoring model output quality).

---

## 2. The AI Testing Pyramid

```
                                  ▲
                                 / \
                                /   \
                               /     \
                              /  EVAL \       Probabilistic AI Evaluation
                             / HARNESS \      (eval_dataset.jsonl, Ollama)
                            /───────────\
                           / INTEGRATION \    Integration Testing
                          /     TESTS     \   (Local Ollama, PostgreSQL, Redis)
                         /─────────────────\
                        /    UNIT TESTS     \ Deterministic Unit Testing
                       /─────────────────────\(Mocks, Fakes, In-Memory Doubles)
```

### 2.1 Deterministic Unit Testing (`tests/unit/`)
* **Focus**: Domain invariants, business logic, JSON schema parsers, guardrail filters, and workflow state machines.
* **Execution Time**: Sub-second execution for hundreds of tests.
* **Hermetic Guarantee**: Must run completely offline with zero active LLM or database dependencies using test doubles.
* **Coverage Target**: Minimum **85% statement coverage**.

### 2.2 Integration Testing (`tests/integration/`)
* **Focus**: Component wiring, repository persistence against real databases, HTTP client communication with local Ollama runtime.
* **Execution Time**: Fast local container execution ($< 30$ seconds).
* **Guarantees**: Verifies serialization, SQL query syntax, and connection pooling.

---

## 3. Mocking & Test Double Policies

* **Production Code**: Zero mock strings or fake sleep loops in `apps/` or `building-blocks/`.
* **Unit Tests**: Mock `ILlmProvider` to return predefined test fixtures representing:
  * Perfectly formatted structured responses.
  * Malformed / corrupted JSON responses (verifying parser resilience).
  * Rate-limit errors (HTTP 429) (verifying retry logic).
  * Timeout errors (verifying circuit breaker triggering).

---

## 4. Compliance Verification

All test suites are executed via automated CI pipelines and must satisfy **[Quality Gate C (Software Testing)](file:///Users/avadhutkore/Documents/code/products/ai-application-architecture/QUALITY-GATES.md#gate-c-software-testing)**.
