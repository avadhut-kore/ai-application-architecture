# Quality & Verification Specification: [Application Name]

> **Tier**: Tier 1 Reference Application  
> **Authoritative Standards**: Maps directly to [QUALITY-GATES.md](../../../QUALITY-GATES.md) (Gates A through J)  

---

## 1. Testing Strategy & Portfolio

The testing portfolio adheres to the testing pyramid defined in [`docs/engineering/testing.md`](../../../docs/engineering/testing.md):

| Test Level | Scope & Technique | Target / Gate | Command |
| :--- | :--- | :---: | :--- |
| **Unit Tests** | Fast, deterministic domain & use case tests using in-memory test doubles (`FakeLlmClient`). | Statement coverage $\ge 85\%$ (Gate C) | `[unit-test-command]` |
| **Integration Tests** | Serialization and wire verification against local inference engine (Ollama) and local DB. | 100% pass (Gate C) | `[integration-test-command]` |
| **E2E / Demo Test** | Automated script running full end-to-end scenario from client to local inference. | Executable in $< 5$ min (Gate I) | `[e2e-test-command]` |

---

## 2. Continuous AI Evaluation (Gate D)

*Where the application implements probabilistic or generative AI behavior:*

* **Evaluation Dataset**: `eval/eval_dataset.jsonl` containing $\ge 30$ curated scenario benchmarks.
* **Evaluation Runner**: Automated evaluation script (`eval/eval_runner.py`) executing against local model.
* **Mandatory Acceptance Criteria**:
  * **Schema Adherence**: $\ge 0.98$ (structural compliance of output).
  * **Faithfulness**: $\ge 0.85$ (factual consistency with context).
  * **Context Relevance**: $\ge 0.80$ (relevance of extracted chunks, if RAG).
  * **Failure Analysis**: Documented failure modes for non-passing scenarios.

---

## 3. Quality Gate Assessment (Gates A through J)

| Quality Gate | Applicability | Verification Method | Status | Verifiable Evidence |
| :--- | :---: | :--- | :---: | :--- |
| **Gate A: Architecture & Design Integrity** | Mandatory | Architecture review & diagram inspection | PASS / FAIL | Mermaid diagrams verified; hexagonal boundaries enforced; zero circular imports. |
| **Gate B: Local-First Execution Integrity** | Mandatory | Air-gapped test execution | PASS / FAIL | Verified execution under Mode A/B with zero cloud API keys. |
| **Gate C: Deterministic Software Quality** | Mandatory | Automated unit & integration test runner | PASS / FAIL | [Test command output; coverage percentage]. |
| **Gate D: AI Quality & Evaluation** | Mandatory if AI exists; else N/A | Automated evaluation runner | PASS / N/A | [Eval runner output; metric scores]. |
| **Gate E: Security, Trust & Safety** | Mandatory | Static analysis & threat model review | PASS / FAIL | Zero secrets in repo; input sanitization verified. |
| **Gate F: Observability & Telemetry** | Mandatory | Trace log inspection | PASS / FAIL | OpenTelemetry GenAI semantic attributes verified in trace logs. |
| **Gate G: Data Management & Hygiene** | Mandatory if DB exists; else N/A | Schema migration check | PASS / N/A | Migrations reversible; zero raw unhashed PII in DB. |
| **Gate H: API Design & Interoperability** | Mandatory | Schema validation | PASS / FAIL | OpenAPI spec generated; structured errors returned. |
| **Gate I: Operational Excellence** | Mandatory | Automated demo script | PASS / FAIL | Interactive demo runs cleanly in $< 5$ minutes. |
| **Gate J: Governance & Acceptance** | Mandatory | Independent audit review | PENDING | Evidence record compiled for independent reviewer. |

---

## 4. Definition of Done (DoD) Checklist

- [ ] All code strictly adheres to repository language standards (`mypy --strict`, `ruff`, or `dotnet format`).
- [ ] No fake `time.sleep()` loops or hardcoded mock strings in production execution paths.
- [ ] Automated unit test suite passes with $\ge 85\%$ statement coverage.
- [ ] AI evaluation suite passes with documented scores meeting Gate D thresholds.
- [ ] Interactive demo script runs locally in $< 5$ minutes under Mode A or B.
- [ ] Completed evidence record submitted for independent review.
