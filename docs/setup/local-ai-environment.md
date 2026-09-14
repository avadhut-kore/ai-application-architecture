# Local AI Environment Setup Guide

This guide describes how to configure a local development environment for running and verifying local-first foundation models in `ai-application-architecture`.

---

## 1. Scope & Execution Principles

This repository enforces an evidence-based, local-first policy defined in [`docs/architecture/local-first.md`](../architecture/local-first.md). Before configuring any local AI tools, understand this fundamental distinction:

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Deterministic Repository Work (No AI Runtime Required)              │
│    - Running static analysis, linters, doc checkers, and validators    │
│    - Running all 63 unit tests across contracts, adapters, and examples │
│    - Requires only Python 3.11+ and standard repository dependencies    │
├────────────────────────────────────────────────────────────────────────┤
│ 2. Live Runtime Verification (Mode A: Offline Local)                   │
│    - Executing live inference against a running local model            │
│    - Running provider smoke verification (`verify.py`)                 │
│    - Running live structured generation demo (`demo.py --mode live`)   │
│    - Running live Gate D AI evaluation (`runner.py --mode live`)       │
│    - Requires local Ollama daemon and an installed local model         │
└────────────────────────────────────────────────────────────────────────┘
```

> [!CRITICAL]
> **MODEL MANAGEMENT GOVERNANCE PRINCIPLES**
> 1. **CI DOES NOT DOWNLOAD MODELS**: Continuous integration runners execute hermetic unit tests in $< 0.1$s using in-memory test doubles (`FakeLlmClient`).
> 2. **TEST SUITES DO NOT DOWNLOAD MODELS**: Automated test commands never invoke network operations or model downloads.
> 3. **MODEL INSTALLATION IS A LOCAL DEVELOPER ACTION**: Developers explicitly manage model weights on their own workstations.
> 4. **MODELS ARE RECOMMENDATIONS, NOT ARCHITECTURAL REQUIREMENTS**: Reference implementations interface with generic protocols (`TextGenerationPort`). Specific model tags are development recommendations, not hardcoded constraints.

---

## 2. Prerequisites & Sizing Guidelines

Hardware requirements follow the sizing profiles in [`docs/architecture/local-first.md`](../architecture/local-first.md):

* **Standard Profile (Recommended)**: Apple Silicon (M1/M2/M3/M4) with $\ge 16\text{GB}$ unified memory, or x86_64 workstation with $\ge 16\text{GB}$ RAM and optional NVIDIA GPU ($\ge 8\text{GB}$ VRAM). Suitable for 3B and 8B parameter models.
* **Lightweight Profile**: 8GB RAM, CPU-only. Suitable for 1B–3B parameter models (e.g. `llama3.2:3b`, `phi3:mini`).

---

## 3. Ollama Installation & Verification (macOS / Local)

[Ollama](https://ollama.com) serves as the primary local inference runtime for Mode A and Mode B execution.

### 3.1 Installation on macOS

Install Ollama using the official installer or Homebrew:

```bash
# Option A: Homebrew (macOS)
brew install ollama

# Option B: Direct download from official site
# Download and install Ollama from https://ollama.com/download
```

### 3.2 Starting the Daemon

Verify installation and start the background daemon:

```bash
# Check CLI version
ollama --version

# Start daemon if not running as a system service
ollama serve
```

By default, the Ollama HTTP API binds to `http://localhost:11434`.

### 3.3 Verifying Endpoint Connectivity

Confirm the REST API responds cleanly:

```bash
# Verify API availability via HTTP
curl -s http://localhost:11434/api/tags
```

Expected response: a JSON object containing a `"models"` array.

---

## 4. Model Installation & Management

Models are pulled manually by the developer. The recommended development model for Phase 4 reference implementations is **`llama3.2:3b`** (compact, fast inference, strong structured JSON compliance).

### 4.1 Installing the Recommended Model

```bash
# Pull the 3B parameter Llama 3.2 model (~2.0 GB)
ollama pull llama3.2:3b

# Create an alias tag for convenience (optional)
ollama cp llama3.2:3b llama3.2
```

### 4.2 Verifying Installed Models

Inspect locally stored model weights:

```bash
ollama list
```

Expected output:
```text
NAME              ID              SIZE      MODIFIED
llama3.2:latest   a80c4f17acd5    2.0 GB    ...
llama3.2:3b       a80c4f17acd5    2.0 GB    ...
```

---

## 5. Running Phase 4 Live Verification

Once the daemon is active and a model is pulled, execute the three live verification paths provided in the repository:

### 5.1 Platform Adapter Smoke Verification
Verifies connection health, installed model discovery, and prompt execution with real token latency telemetry:
```bash
python3 platform/ollama-adapter/verify.py
```
*Expected Result*: Exits with code `0`, displays model latency and token counts (`prompt`, `completion`).

### 5.2 Structured Generation Live Extraction
Extracts unstructured feedback into strongly typed `CustomerFeedbackExtraction` domain entities using the local model:
```bash
python3 examples/structured-generation/demo.py --mode live
```
*Expected Result*: Exits with code `0`, validates JSON schema without syntax or boundary errors.

### 5.3 Gate D AI Evaluation Runner
Evaluates all 30 scenarios in `eval_dataset.jsonl` against authoritative Gate D thresholds:
```bash
python3 examples/ai-evaluation/runner.py --mode live
```
*Expected Result*: Exits with code `0`, reporting schema adherence rate ($\ge 98.0\%$), category accuracy, and latency distribution.

---

## 6. Troubleshooting Common Issues

| Symptom | Root Cause | Remediation |
| :--- | :--- | :--- |
| `AiProviderUnavailableError` or connection refused on `11434` | Ollama daemon is not running | Run `ollama serve` in a dedicated terminal or launch Ollama.app. |
| `AiModelNotFoundError` (HTTP 404) | Requested model tag is not downloaded | Run `ollama pull <model-tag>` (e.g. `ollama pull llama3.2:3b`). |
| `AiTimeoutError` | Model loading or generation exceeded timeout | Increase timeout via `--timeout` argument or verify workstation memory pressure. |
| Live commands exit with code `1` | Strict exit contract prevents false passes | Check terminal output for the specific failure reason and verify daemon health. |
