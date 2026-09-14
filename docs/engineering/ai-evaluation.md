# AI Behavioral Evaluation Standards & Methodology

This document establishes the evaluation architecture, dataset design conventions, metric scoring methodology, and regression gating for generative AI workloads across the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Normative Authority Rule**  
> In accordance with [`docs/engineering/README.md`](README.md):
> * **[`QUALITY-GATES.md`](../../QUALITY-GATES.md) (Gate D)** is the **sole authoritative source** for acceptance criteria, mandatory minimums ($\ge 30$ scenarios, Faithfulness $\ge 0.85$, Context Relevance $\ge 0.80$, Schema Adherence $\ge 0.98$), and PASS/FAIL conditions.
> * **This document (`ai-evaluation.md`)** is the authoritative source for **evaluation methodology, dataset schema conventions, evaluator strategy, regression testing, and implementation guidance**.
>
> Numerical targets in this document higher than `QUALITY-GATES.md` represent recommended engineering goals, not competing release gates.

---

## 1. AI Evaluation Architecture

Unlike deterministic software assertions that compare actual against expected values with binary precision, AI evaluation measures the quality, accuracy, grounding, and safety of probabilistic model outputs across statistical distributions.

```
┌────────────────────────┐     ┌────────────────────────┐
│  Golden Evaluation Set │     │ Target AI System Under │
│  (eval_dataset.jsonl)  │     │ Test (Pipeline / RAG)  │
└───────────┬────────────┘     └───────────┬────────────┘
            │                              │
            │ Inputs                       │ Generated Output + Context
            ▼                              ▼
┌───────────────────────────────────────────────────────┐
│               Automated Evaluation Runner             │
│   (Local Judge Model, Heuristics, or Semantic Scorer) │
└───────────────────────────┬───────────────────────────┘
                            │
                            ▼
┌───────────────────────────────────────────────────────┐
│                 Evaluation Scorecard                  │
│    • Faithfulness / Grounding  • Latency & Tokens     │
│    • Context Relevance         • Safety & Refusal     │
│    • Answer Correctness        • Regression Delta     │
└───────────────────────────────────────────────────────┘
```

---

## 2. Evaluation Dataset Conventions (`eval_dataset.jsonl`)

Every reference application implementing probabilistic capabilities must provide a versioned evaluation dataset in JSON Lines format.

### Dataset Location Conventions
To accommodate a polyglot repository (.NET, Python, TypeScript, Java), dataset locations follow standard directory conventions appropriate to the project structure:
* In Python / Node projects: `tests/eval/eval_dataset.jsonl` or `eval/eval_dataset.jsonl`.
* In .NET projects: `tests/<Project>.EvalTests/eval_dataset.jsonl` or `eval/eval_dataset.jsonl`.
* In Java projects: `src/test/resources/eval/eval_dataset.jsonl`.

### Standard JSON Schema
Each line in `eval_dataset.jsonl` must be a self-contained JSON object conforming to the following structure:

```json
{
  "id": "eval-rag-042",
  "category": "factual_extraction",
  "input": "What is the maximum allowed invoice threshold for automated approval?",
  "ground_truth_context": [
    "Section 4.2: Automated approval is permitted for invoices up to $5,000 USD with a valid PO match."
  ],
  "expected_output": "The maximum threshold for automated invoice approval is $5,000 USD when accompanied by a valid PO match.",
  "metadata": {
    "tier": "tier-1",
    "difficulty": "medium",
    "requires_reasoning": false
  },
  "constraints": {
    "must_contain": ["$5,000", "PO match"],
    "must_not_contain": ["unlimited", "$10,000"]
  }
}
```

### Dataset Composition Rules
* **Mandatory Minimum Size**: The authoritative minimum is **$\ge 30$ representative scenarios** as mandated by Gate D in [`QUALITY-GATES.md`](../../QUALITY-GATES.md).
* **Recommended Target**: For complex or high-risk Tier 1 applications, maintaining 50+ curated scenarios is strongly recommended to capture statistical variance. For Tier 2 pattern examples, $\ge 20$ curated scenarios is recommended where probabilistic features are demonstrated.
* **Golden Quality**: Ground truth values must be human-curated or domain-verified. Never commit synthetic ground truth without architectural review.
* **Adversarial & Edge Cases**: At least 15% of scenarios must test boundary cases: unanswerable questions (abstention), prompt injection attempts, out-of-domain queries, and malformed inputs.

---

## 3. Evaluation Metric Portfolio & Thresholds

Evaluation metrics combine mandatory gate criteria from Gate D with recommended engineering targets:

| Metric | Authoritative Acceptance Gate ([Gate D](../../QUALITY-GATES.md#gate-d--ai-evaluation)) | Recommended Engineering Target | Evaluation Method & Description |
| :--- | :--- | :--- | :--- |
| **Groundedness / Faithfulness** | **$\ge 0.85$** (Mandatory Gate) | $\ge 0.90$ (Stronger Target) | Factual claims supported by retrieved context. Scored via local LLM judge or citation overlap. |
| **Context Relevance** | **$\ge 0.80$** (Mandatory Gate) | $\ge 0.85$ (Stronger Target) | Pertinence of retrieved chunks to input query. Filters retrieval noise. |
| **Schema Adherence** | **$\ge 0.98$** (Mandatory Gate) | $1.00$ (Zero parse errors) | Structured output parsing into validated schemas (Pydantic / Zod / C# records). |
| **Adversarial Handling** | **Explicit Abstention** (Mandatory Gate) | 100% Refusal on Jailbreaks | Model properly abstains, flags unanswerable queries, and refuses prompt injections. |
| **Answer Relevance** | N/A (Methodology Target) | $\ge 0.85$ (Recommended Target)| Semantic alignment of generated answer to query intent. |
| **Latency SLA (P95)** | Documented in Gate G | $\le 3,500\text{ ms}$ (Local 8B) | Request dispatch to complete generation time on local workstation. |
| **Token Efficiency** | Monitored in Gate F | Within defined budget | Prompt tokens + completion tokens consumed per evaluation run. |

---

## 4. Local-First Evaluation Runner & Polyglot Execution

In compliance with [`docs/architecture/local-first.md`](../architecture/local-first.md), evaluation harnesses must execute locally without requiring paid third-party API subscriptions:

### Gate Requirement vs. Implementation Tooling
* **Gate Requirement**: AI evaluation must be automated, executable by a single command, and produce verifiable structured evidence (e.g., JSON report).
* **Polyglot Tooling**: Teams use runner tooling appropriate to the application's ecosystem:
  * In Python: `python eval/eval_runner.py` or `pytest tests/eval`.
  * In .NET: `dotnet test tests/<Project>.EvalTests`.
  * In TypeScript: `npm run test:eval` or `vitest run tests/eval`.
  * In Java: `./gradlew test --tests "*EvalTest*"`.

### Local Execution Modes
* **Mode A (Offline Local)**: The evaluation runner executes against a fully local model runtime (e.g., Ollama with `llama3.2:3b` or `phi3:mini`) with zero external network connectivity.
* **Mode B (Local-First)**: The runner executes against local models while allowing designated external APIs (e.g. web search or enterprise fixtures) where part of the architecture under test.
* **Deterministic Fallback Scoring**: For CI environments without GPU acceleration, the evaluation runner must support a deterministic heuristic scoring mode (testing string constraints, regex patterns, and exact schema parsing) that completes in under 60 seconds.

---

## 5. Continuous Integration & Regression Gating

AI evaluation must run as an automated verification step in the pipeline:

* **Zero Regression Rule**:
  * A pull request must not decrease the overall faithfulness score or context relevance score below the authoritative Gate D thresholds ($\ge 0.85$ and $\ge 0.80$ respectively), nor decrease them by more than 2% compared to the main baseline.
  * Schema adherence and safety refusal tests must maintain 100% pass on deterministic constraints.
* **Automated Evidence Output**:
  * The evaluation runner must generate a machine-readable JSON report (`eval_report_<timestamp>.json`) and a summary table for verification:
    ```markdown
    | Metric | Gate D Requirement | Baseline | Current Run | Delta | Status |
    | :--- | :--- | :--- | :--- | :--- | :--- |
    | Faithfulness | ≥ 0.85 | 0.912 | 0.918 | +0.006 | PASS |
    | Context Relevance | ≥ 0.80 | 0.840 | 0.844 | +0.004 | PASS |
    | Schema Adherence | ≥ 0.98 | 1.000 | 1.000 | 0.000 | PASS |
    | Adversarial Refusal | Explicit Abstention | 100% | 100% | 0.000 | PASS |
    ```
