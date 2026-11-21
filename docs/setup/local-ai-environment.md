# Local AI Environment Setup Guide

This guide describes how to configure a local development environment for running and verifying local-first foundation models in `ai-application-architecture`.

---

## 1. Scope & Execution Principles

This repository enforces an evidence-based, local-first policy defined in [`docs/architecture/local-first.md`](../architecture/local-first.md). Before configuring any local AI tools, understand this fundamental distinction:

```text
┌────────────────────────────────────────────────────────────────────────┐
│ 1. Deterministic Repository Work (No AI Runtime Required)              │
│    - Running static analysis, linters, doc checkers, and validators    │
│    - Running repository-discovered tests across all active examples │
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
* **Lightweight Profile**: 8GB RAM, CPU-only. Suitable for 1B–3B parameter models (e.g. `qwen2.5:7b`, `phi3:mini`).

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

Models are pulled manually by the developer. The recommended development model for Phase 4 reference implementations is **`qwen2.5:7b`** (compact, fast inference, strong structured JSON compliance).

### 4.1 Installing the Recommended Models

```bash
# Pull the 3B parameter Llama 3.2 text generation model (~2.0 GB)
ollama pull qwen2.5:7b

# Create an alias tag for convenience (optional)
ollama cp qwen2.5:7b qwen2.5:7b

# Pull the recommended dense embedding model for Phase 5 Knowledge Intelligence (~274 MB)
ollama pull nomic-embed-text
```

### 4.2 Verifying Installed Models

Inspect locally stored model weights:

```bash
ollama list
```

Expected output:
```text
NAME                     ID              SIZE      MODIFIED
qwen2.5:7b:latest          a80c4f17acd5    2.0 GB    ...
qwen2.5:7b              a80c4f17acd5    2.0 GB    ...
nomic-embed-text:latest  0a109f422b47    274 MB    ...
```

---

## 5. Running Phase 4 & Phase 5 Live Verification

Once the daemon is active and models are pulled, execute the live verification paths provided in the repository:

### 5.1 Platform Adapter Smoke Verification (Phase 4)
Verifies connection health, installed model discovery, and prompt execution with real token latency telemetry:
```bash
python3 platform/ollama-adapter/verify.py
```
*Expected Result*: Exits with code `0`, displays model latency and token counts (`prompt`, `completion`).

### 5.2 Structured Generation Live Extraction (Phase 4)
Extracts unstructured feedback into strongly typed `CustomerFeedbackExtraction` domain entities using the local model:
```bash
python3 examples/structured-generation/demo.py --mode live
```
*Expected Result*: Exits with code `0`, validates JSON schema without syntax or boundary errors.

### 5.3 Gate D AI Evaluation Runner (Phase 4)
Evaluates all 30 scenarios in `examples/ai-evaluation/eval_dataset.jsonl` against authoritative Gate D thresholds:
```bash
python3 examples/ai-evaluation/runner.py --mode live
```
*Expected Result*: Exits with code `0`, reporting schema adherence rate ($\ge 98.0\%$), category accuracy, and latency distribution.

### 5.4 Embedding Adapter Smoke Verification (Phase 5)
Verifies connection health, installed embedding model availability, and dense vector generation:
```bash
python3 platform/ollama-embedding-adapter/verify.py
```
*Expected Result*: Exits with code `0`, reporting embedding dimensions (e.g. 768 for `nomic-embed-text`) and latency.

### 5.5 Knowledge Intelligence & RAG Interactive Demo (Phase 5)
Runs end-to-end local knowledge retrieval, context budgeting, and grounded generation with validated citations:
```bash
python3 examples/rag/demo.py --mode live
```
*Expected Result*: Exits with code `0`, displays retrieved chunks, grounded answer, and verified citation identifiers.

### 5.6 Gate D RAG Evaluation Runner (Phase 5)
Evaluates all 32 scenarios in `examples/rag/eval_dataset.jsonl` measuring retrieval and grounded generation against Gate D:
```bash
python3 examples/rag/eval_runner.py --mode live
```
*Expected Result*: Exits with code `0`, reporting Hit Rate, Recall@K, MRR, Context Relevance ($\ge 80\%$), Groundedness ($\ge 85\%$), and Schema Adherence ($\ge 98\%$).


---

## 6. Troubleshooting Common Issues

| Symptom | Root Cause | Remediation |
| :--- | :--- | :--- |
| `AiProviderUnavailableError` or connection refused on `11434` | Ollama daemon is not running | Run `ollama serve` in a dedicated terminal or launch Ollama.app. |
| `AiModelNotFoundError` (HTTP 404) | Requested model tag is not downloaded | Run `ollama pull <model-tag>` (e.g. `ollama pull qwen2.5:7b`). |
| `AiTimeoutError` | Model loading or generation exceeded timeout | Increase timeout via `--timeout` argument or verify workstation memory pressure. |
| Live commands exit with code `1` | Strict exit contract prevents false passes | Check terminal output for the specific failure reason and verify daemon health. |

## Windows Docker storage and local inference

Move Docker Desktop disk storage using Settings → Resources → Advanced before
pulling images. On the remediation workstation, Docker data is already configured
under `D:\DockerDesktop\DockerDesktopWSL`. Ollama model files are bind-mounted
from `D:\ai-models\ollama`; they are separate from image layers. The container
publishes only `127.0.0.1:11434`. Models are explicitly installed by the developer,
never by tests or CI.

Use the locked root environment (`uv sync --frozen`) for Python commands. A local
Ollama Docker endpoint works with the existing adapters; no cloud credentials are
needed. Runtime examples default to live inference. A deterministic harness pass
is not evidence of live model quality.

For the pinned container configuration, copy `.env.example` to `.env`, create
the `OLLAMA_MODEL_DIR` directory, and run `docker compose up --build -d`. Compose
builds the [same-release security patch](../../platform/ollama-adapter/Dockerfile.security)
from pinned upstream inputs; the initial build requires network access and extra
Docker disk space. It updates the three HIGH package findings recorded in the
[evidence report](../engineering/phase1-7-remediation.md). Initial image/build/model
installation is separate from the measured interactive CLI demonstration.
Install model
weights explicitly with `docker compose exec ollama ollama pull qwen2.5:7b`
and `docker compose exec ollama ollama pull nomic-embed-text`. The workflow CLI
defaults to the same Qwen tag. An existing
Ollama container already publishing port 11434 must be stopped before starting
this Compose service. Model downloads need network access once; subsequent
local inference needs no paid API key.

## Local trace export

Python CLIs use process environment variables; Compose's `.env` interpolation
does not export those variables into a separate Python terminal. To record
metadata-only OpenTelemetry JSON spans on Windows:

```powershell
$env:AI_TRACE_FILE = ".quality/traces/local.jsonl"
uv run --frozen python examples/agentic-workflow/demo.py start --customer cust-001 --inquiry "Check account status"
```

On Linux or macOS, prefix the command with
`AI_TRACE_FILE=.quality/traces/local.jsonl`. The exporter records operation names,
model names, timing, usage and status, with parent/child correlation. It does not
export prompts, answers, retrieved text or exception messages. An application
that already configures an SDK tracer provider keeps ownership of that provider.
