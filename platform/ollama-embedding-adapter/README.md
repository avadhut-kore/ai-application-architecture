# Tier 3 Platform Component: Ollama Embedding Adapter

> **Tier Classification**: **Tier 3 — Platform Component**  
> **Component Role**: Outbound Dense Embedding Adapter  
> **Target Ecosystem**: Python 3.9+  
> **Status**: Implemented  

---

## 1. Responsibility & Bounded Scope

* **Purpose**: Provides a concrete, local-first dense embedding runtime adapter connecting to Ollama while implementing the provider-neutral `EmbeddingPort` protocol.
* **Supported Behavior**:
  * Direct HTTP communication with the Ollama daemon (`POST /api/embed` with fallback to legacy `POST /api/embeddings`).
  * Request serialization from `EmbeddingRequest` (batch text inputs, model name, metadata).
  * Response mapping into `EmbeddingResponse` including dimension checks, token `UsageMetrics`, and `latency_ms`.
  * Bounded exponential backoff retry on transient transport/server errors (`AiTransientError`).
  * HTTP status code translation into the repository `AiError` taxonomy (`AiModelNotFoundError`, `AiTimeoutError`, `AiProviderUnavailableError`, `AiInvalidRequestError`).
  * Timeout and cancellation propagation via `asyncio.CancelledError`.
  * Preflight health and installed model discovery (`check_health()`, `get_installed_models()`).
* **Unsupported Behavior (Anti-Framework Boundaries)**:
  * Does **not** implement text generation or chat completion (owned by `platform/ollama-adapter/`).
  * Does **not** implement vector indexing or similarity search (owned by knowledge index components).
  * Does **not** implement chunking, ingestion, or prompt templating.
  * Does **not** download or pull models automatically.
* **Reuse Justification**: Factor low-level Ollama embedding HTTP wire protocols, batching, retry policies, and error translation into an isolated platform component so Knowledge Intelligence and RAG services interact purely through `EmbeddingPort`.

---

## 2. Public Contracts & Interface Specification

`OllamaEmbeddingAdapter` implements the canonical `EmbeddingPort` protocol defined in `building-blocks/python/contracts/ports.py`:

```python
from contracts.models import EmbeddingRequest, EmbeddingResponse
from contracts.ports import EmbeddingPort

class OllamaEmbeddingAdapter(EmbeddingPort):
    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        default_model: str = "nomic-embed-text",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        ...

    async def embed(
        self,
        request: EmbeddingRequest,
        context: Optional[AiOperationContext] = None,
    ) -> EmbeddingResponse:
        ...
```

---

## 3. Configuration & Local Execution

Configure via constructor arguments or environment variables:

| Parameter | Environment Variable | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `endpoint` | `OLLAMA_ENDPOINT` | `http://localhost:11434` | Ollama HTTP daemon base URL |
| `default_model` | `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Default dense embedding model tag |
| `timeout_seconds` | `OLLAMA_TIMEOUT` | `30.0` | Socket and HTTP read timeout in seconds |
| `max_retries` | `OLLAMA_MAX_RETRIES` | `2` | Retry attempts for transient errors |
| `backoff_base_seconds` | `OLLAMA_BACKOFF_BASE` | `0.5` | Exponential backoff base interval |

---

## 4. Verification & Testing

### 4.1 Hermetic Unit Tests (Offline CI)
Execute unit tests using hermetic standard library mocks without requiring a live Ollama daemon:

```bash
python3 -m unittest discover -s platform/ollama-embedding-adapter/tests -t platform/ollama-embedding-adapter
```

### 4.2 Live Runtime Verification
Verify local Ollama daemon reachability and live embedding generation:

```bash
python3 platform/ollama-embedding-adapter/verify.py
```

If an embedding model is not yet installed, the verification CLI will report `NOT VERIFIED` and instruct the developer to pull a model (e.g. `ollama pull nomic-embed-text`).
