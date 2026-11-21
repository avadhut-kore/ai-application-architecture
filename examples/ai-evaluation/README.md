# Tier 2 Pattern Example: AI Evaluation Harness

> **Tier Classification**: **Tier 2 — Pattern Example**  
> **Demonstrated Pattern**: Gate D Evaluation Harness & Benchmark Runner  
> **Operational Mode**: Mode A — Offline Local (with Mode B — Local-First optional)  
> **Status**: Implemented; acceptance requires current execution evidence.

Gate D is mandatory for Tier 1 applications. This Tier 2 example voluntarily
demonstrates its scoring mechanics and thresholds. The historical `gate_d_passed`
field describes that benchmark result; it does not independently accept an
application or require all Gate D criteria for Tier 2.

---

## 1. Pattern Overview & Intent

* **Intent**: Establish an automated, repeatable, evidence-based evaluation harness for probabilistic AI behaviors in compliance with authoritative Gate D requirements.
* **Demonstrated Technique**: Transforms qualitative AI generation assessments into quantitative metrics (schema adherence, enum classification accuracy, latency distribution, and adversarial robustness) evaluated against predetermined numerical thresholds.

---

## 2. Applicability Guide

### When to Use This Pattern
* When verifying that an LLM-powered service reliably adheres to downstream operational contracts across varied input distributions.
* When continuous integration (CI) requires automated regression testing of model prompts, versions, or quantized weights without manual spot-checking.
* When evaluating resilience against adversarial prompt injections and malformed inputs.

### When NOT to Use This Pattern
* For purely deterministic software components where traditional unit testing with mock inputs and assertions is sufficient.
* For arbitrary conversational benchmarks where ground truth cannot be objectively labeled or evaluated.

---

## 3. Mechanism & Interaction Flow

```mermaid
graph TD
    Dataset["eval_dataset.jsonl (30 Scenarios)"] --> Runner["Evaluation Runner (runner.py)"]
    Runner --> Service["FeedbackExtractionService"]
    Service --> Port["TextGenerationPort (OllamaAdapter or Stub)"]
    Port --> Service
    Service --> Validator["Untrusted Output Validation"]
    Validator --> Scorer["Metrics Collector"]
    Scorer --> Summary["EvaluationSummary (Adherence %, Accuracy %, Latency)"]
    Summary --> GateCheck{"Meets Authoritative Gate D Threshold?\n(>=30 cases, >=98.0% schema adherence)"}
    GateCheck -->|Yes| Pass["Gate D PASSED (exit code 0)"]
    GateCheck -->|No| Fail["Gate D FAILED (exit code 1)"]
```

### Dataset Taxonomy (30 Scenarios)
The evaluation suite (`eval_dataset.jsonl`) contains 30 versioned scenarios categorized into four distinct test types:
1. **Normal (10 scenarios)**: Standard customer feedback across all supported categories (`bug`, `feature_request`, `inquiry`, `billing`), sentiments, and urgencies.
2. **Boundary (5 scenarios)**: Extreme edge cases including single-word messages, stack traces, and multi-paragraph disputes.
3. **Ambiguous (7 scenarios)**: Subtle phrasing including sarcasm, implied bugs, passive inquiries, and borderline urgency.
4. **Adversarial (8 scenarios)**: Injection attempts, system prompt override commands, unauthorized enums, code delimiters, and multi-task confusion.

---

## 4. Local Execution & Verification

### Prerequisites
* Python 3.11+ installed.
* Optional (for live evaluation): Local Ollama daemon with `qwen2.5:7b` model.

### Run Offline Evaluation Harness Check (Mode A — $< 1$s)
```bash
python3 examples/ai-evaluation/runner.py --mode fake
```
*Note: Validates scenario parsing, scoring mechanics, and threshold evaluation. Outputs `EVALUATION HARNESS VALIDATION: PASS` and `Gate D Real-Model Evaluation: NOT VERIFIED`.*

### Run Live Evaluation (Mode B — Local Ollama)
```bash
python3 examples/ai-evaluation/runner.py --mode live --model qwen2.5:7b
```
*Note: Executes all 30 scenarios against the local model. Returns exit code 0 when the reference schema threshold is met ($\ge 98.0\%$ schema adherence) or exit code 1 if unverified or failed.*

### Run Deterministic Unit Tests
```bash
python3 -m unittest discover -s examples/ai-evaluation/tests -t examples/ai-evaluation -v
```

---

## 5. Architectural Trade-offs & Limitations

* **Trade-off (Ground-Truth Ambiguity vs. Deterministic Grading)**: Natural language is nuanced; some inputs (e.g. sarcastic bug reports) could plausibly be labeled differently by human annotators. The evaluation harness establishes strict expected labels for consistency while tracking category, sentiment, and urgency accuracies independently.
* **Trade-off (Evaluation Cost/Time vs. Sample Size)**: Execution time depends on model, quantization and hardware; the CPU live run can take many minutes. See the evidence report for measured latency. Expanding to thousands of scenarios increases statistical power but slows down local developer inner-loop testing.
* **Known Limitation**: Live evaluation depends on the specific model weights loaded into Ollama. A smaller quantized model (e.g. 1B or 3B parameters) may exhibit lower classification accuracy on ambiguous or adversarial scenarios than larger foundation models.

---

## 6. Quality gate evidence

This Tier 2 example is subject to Gates B, C, H and I. Gate D is a voluntary
reference benchmark, not a Tier 2 acceptance certificate. Strict typing, lint,
unit coverage, live commands and remaining acceptance limitations are recorded
in the [Phases 1–7 evidence report](../../docs/engineering/phase1-7-remediation.md).
CI now enforces the deterministic checks; remote CI execution must be verified
on the reviewed revision.
