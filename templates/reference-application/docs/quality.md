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
| **Gate A — Architecture & Structural Boundaries** | Mandatory | Static dependency analysis & architectural review | PASS / FAIL | Automated import scan proving zero vendor SDKs in `domain/` and `application/`; approved ADRs. |
| **Gate B — Code Quality & Type Safety** | Mandatory | Static type checking & linter (`mypy --strict`, `ruff`) | PASS / FAIL | Clean CI/CD terminal execution logs: 0 errors, 0 warnings. |
| **Gate C — Software Testing** | Mandatory | Automated unit & integration test runner | PASS / FAIL | Test execution log showing $\ge 85\%$ statement coverage for domain modules; 100% passing tests. |
| **Gate D — AI Evaluation** | Mandatory if AI exists; else N/A | Automated evaluation harness (`eval_dataset.jsonl`) | PASS / N/A | Evaluation report (`eval_report.json`) meeting Gate D metric thresholds ($\ge 30$ scenarios). |
| **Gate E — Security & Safety** | Mandatory | Security scanners (`gitleaks`, `pip-audit`) & threat model | PASS / FAIL | Clean security scan logs (0 secrets, 0 High/Critical CVEs); documented STRIDE/OWASP threat model. |
| **Gate F — Observability & Telemetry** | Mandatory | OpenTelemetry trace span inspection | PASS / FAIL | JSON trace span dump asserting presence of required `gen_ai.*` semantic attributes. |
| **Gate G — Performance & Sizing** | Mandatory | Local benchmark script execution | PASS / FAIL | Benchmark report demonstrating TTFT $\le 2.0\text{s}$, chunked streaming, and zero memory leaks. |
| **Gate H — Documentation & Architectural Integrity** | Mandatory | Automated link checker & review | PASS / FAIL | `python3 scripts/validate-docs.py` exit code 0; renderable Mermaid diagrams; documented trade-offs. |
| **Gate I — Demo & Operational Verification** | Mandatory | Clean workstation single-command trial | PASS / FAIL | Execution log demonstrating local cold-bootstrap under Mode A or B without cloud API keys ($< 5$ min). |
| **Gate J — Production Readiness & Resilience** | Mandatory | Automated fault injection & resilience tests | PASS / FAIL | Passing resilience test logs demonstrating timeouts, backoff retries, circuit breaking, and fallback. |

---

## 4. Definition of Done (DoD) Checklist

- [ ] All code strictly adheres to repository language standards (`mypy --strict`, `ruff`, or `dotnet format`).
- [ ] No fake `time.sleep()` loops or hardcoded mock strings in production execution paths.
- [ ] Automated unit test suite passes with $\ge 85\%$ statement coverage.
- [ ] AI evaluation suite passes with documented scores meeting Gate D thresholds.
- [ ] Interactive demo script runs locally in $< 5$ minutes under Mode A or B.
- [ ] Completed evidence record submitted for independent review.
