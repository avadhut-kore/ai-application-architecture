# AI Behavioral Evaluation Standards

This document establishes the evaluation architecture, dataset standards, metric definitions, and regression gating for generative AI workloads across the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> AI evaluation provides objective verification for Gate G4 in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). No AI reference application may be certified as production-ready without passing automated evaluation against an authoritative golden dataset.

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

## 2. Evaluation Dataset Specification (`eval_dataset.jsonl`)

Every reference application implementing generative features must provide a versioned evaluation dataset in JSON Lines format located at `tests/eval/eval_dataset.jsonl`.

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
* **Minimum Size**: Tier 1 reference applications must maintain a minimum of 50 curated golden evaluation samples; Tier 2 applications require at least 20 samples.
* **Golden Quality**: Ground truth values must be human-curated or mathematically verifiable. Never generate synthetic ground truth without manual architectural review.
* **Adversarial & Edge Cases**: At least 15% of the evaluation dataset must include adversarial inputs: prompt injections, out-of-domain queries, malformed contexts, and ambiguity edge cases.

---

## 3. Evaluation Metric Portfolio

Reference applications must evaluate performance across seven core dimensions:

| Metric | Target Boundary | Evaluation Method | Primary Failure Mode |
| :--- | :--- | :--- | :--- |
| **Faithfulness / Grounding** | ≥ 0.90 (0 to 1.0) | Claim verification against retrieved context using local LLM judge or deterministic citation matching. | Hallucination, unsupported claims. |
| **Context Relevance** | ≥ 0.85 (0 to 1.0) | Sentence relevance of retrieved chunks to input query. | Noise in context, irrelevant retrieval. |
| **Answer Relevance** | ≥ 0.85 (0 to 1.0) | Semantic similarity of generated answer to the original intent. | Vagueness, evasion, topic drifting. |
| **Deterministic Constraints** | 100% Pass | RegEx, string boundary checks, and schema validation (`must_contain`, `must_not_contain`). | Formatting breaches, leaked instructions. |
| **Safety & Refusal Rate** | 100% Refusal on Adversarial | Evaluates proper refusal on prompt injection, jailbreak attempts, or data exfiltration prompts. | System prompt leaking, safety bypass. |
| **Latency SLA (P95)** | ≤ 3,500 ms (local) | Measured execution time per sample from request dispatch to complete generation. | Inefficient retrieval, unoptimized prompts. |
| **Token Efficiency** | Under defined budget | Total input + output tokens consumed per evaluation run. | Verbose system prompts, duplicate context. |

---

## 4. Local-First Evaluation Runner

In compliance with [`docs/architecture/local-first.md`](../architecture/local-first.md), evaluation harnesses must execute locally without requiring paid third-party API subscriptions:

1. **Local Judge Execution (Mode A / Mode B)**:
   * Evaluation runners must support local models (e.g., `llama3.2:3b` or `phi3:mini` via Ollama) or deterministic Python/C# heuristics (cosine similarity via local ONNX embeddings, BLEU/ROUGE, token overlap).
2. **Deterministic Fallback Scoring**:
   * For continuous integration (CI) environments without GPU acceleration, the evaluation suite must provide a deterministic heuristic scoring mode (testing structural constraints, keywords, and exact matches) that executes in under 60 seconds.
3. **Reproducibility**:
   * Evaluation runs must log model temperature (`temperature = 0.0`), top_p, seed, model tag, and execution timestamp into an evaluation report (`tests/eval/latest_results.json`).

---

## 5. Continuous Integration & Regression Gating

AI evaluation must run as an automated step in the validation pipeline:

* **Zero Regression Rule**:
  * A pull request or change must not decrease the overall faithfulness score or answer relevance score by more than 2% compared to the main baseline.
  * Deterministic constraints and safety refusal tests must have zero regressions (100% pass rate).
* **Automated Evidence Generation**:
  * The evaluation runner must generate a human-readable and machine-verifiable summary markdown table:
    ```markdown
    | Metric | Baseline | Current Run | Delta | Status |
    | :--- | :--- | :--- | :--- | :--- |
    | Faithfulness | 0.932 | 0.935 | +0.003 | PASS |
    | Context Relevance | 0.880 | 0.884 | +0.004 | PASS |
    | Answer Relevance | 0.895 | 0.891 | -0.004 | PASS |
    | Safety Refusals | 100% | 100% | 0.000 | PASS |
    | P95 Latency | 2,120 ms | 2,050 ms | -70 ms | PASS |
    ```
