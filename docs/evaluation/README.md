# Continuous AI Evaluation & Quality Assurance

## 1. Domain Scope

The `docs/evaluation/` directory defines the methodology, scoring algorithms, benchmark dataset standards, and automated pipelines used to evaluate the output quality, groundedness, and reliability of probabilistic foundation models across the repository.

---

## 2. Core Evaluation Metrics

Every reference application must implement automated evaluation scoring against four primary metrics:

```
┌───────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ Evaluation Metric                     │ Objective Measurement Target                           │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ **1. Groundedness / Faithfulness**    │ Measures whether every factual claim in the generated  │
│                                       │ answer can be mathematically derived from the context. │
│                                       │ Target: $\ge 0.85$                                     │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ **2. Context Relevance**              │ Measures whether retrieved chunks are relevant to the  │
│                                       │ user's query and free from distracting noise.          │
│                                       │ Target: $\ge 0.80$                                     │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ **3. Answer Relevance**               │ Measures whether the response directly answers the     │
│                                       │ user's original query without tangential drift.        │
│                                       │ Target: $\ge 0.85$                                     │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ **4. Schema Adherence Rate**          │ Measures the percentage of model outputs that conform  │
│                                       │ strictly to the target JSON schema without errors.     │
│                                       │ Target: $\ge 0.98$                                     │
└───────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Evaluation Dataset Standard (`eval_dataset.jsonl`)

Every application in `apps/` must maintain an evaluation dataset formatted as JSON Lines (`.jsonl`). Each record must contain:

```json
{
  "scenario_id": "RAG-001",
  "domain": "customer_policy",
  "query": "What is the return window for defective hardware?",
  "reference_context": "Defective hardware may be returned within 45 days of receipt with original invoice.",
  "ground_truth_answer": "Defective hardware must be returned within 45 days of delivery along with the original purchase invoice.",
  "expected_citation_ids": ["doc_hw_policy_v2_p4"],
  "test_type": "positive"
}
```

### Negative Scenarios
Evaluation datasets must include **adversarial and negative test cases**:
* **Out-of-domain questions**: Model must decline to answer or state lack of context.
* **Malicious injection prompts**: Model must refuse the injection while remaining helpful.
* **Ambiguous queries**: Model must request clarification rather than fabricate facts.

---

## 4. Evaluation Execution & CI Integration

* Evaluations execute locally against **Ollama** using the application's `eval/eval_runner.py`.
* Results are recorded in `eval/results/eval_report_<timestamp>.json` tracking historical score trends.
* Pull requests that cause score regressions below configured thresholds fail **[Quality Gate D (AI Evaluation)](file:///Users/avadhutkore/Documents/code/products/ai-application-architecture/QUALITY-GATES.md#gate-d-ai-evaluation)**.
