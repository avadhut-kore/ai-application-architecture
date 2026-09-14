"""Ollama implementation adapter for the provider-neutral EmbeddingPort."""

from __future__ import annotations

import asyncio
import json
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping, Optional, Sequence

from contracts.errors import (
    AiError,
    AiInvalidRequestError,
    AiModelNotFoundError,
    AiProviderUnavailableError,
    AiRateLimitError,
    AiTimeoutError,
    AiTransientError,
)
from contracts.models import (
    EmbeddingRequest,
    EmbeddingResponse,
    UsageMetrics,
)
from contracts.ports import EmbeddingPort
from contracts.telemetry import AiOperationContext


class OllamaEmbeddingAdapter(EmbeddingPort):
    """Concrete embedding adapter communicating with a local or remote Ollama daemon.

    Adheres strictly to the provider-neutral EmbeddingPort protocol using
    standard library HTTP client capabilities (zero external runtime dependencies).
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        default_model: str = "nomic-embed-text",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        """Initialize the Ollama embedding adapter with endpoint and execution policies."""
        self.endpoint = endpoint.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def _send_http_request(self, path: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous HTTP execution invoked inside a worker thread via asyncio.to_thread."""
        url = f"{self.endpoint}{path}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as ex:
            error_body = ""
            try:
                error_body = ex.read().decode("utf-8")
            except Exception:
                pass

            if ex.code == 404:
                # Distinguish between missing model and unsupported /api/embed endpoint
                if "model" in error_body.lower() and "not found" in error_body.lower():
                    model_name = (payload.get("model") if payload else "") or self.default_model
                    raise AiModelNotFoundError(
                        model_name=model_name,
                        details={"http_status": 404, "endpoint": url, "error_body": error_body},
                    ) from ex
                else:
                    raise AiError(
                        message=f"HTTP 404 from Ollama: {error_body or ex.reason}",
                        error_code="AI_HTTP_NOT_FOUND",
                        details={"http_status": 404, "endpoint": url, "error_body": error_body},
                    ) from ex

            elif ex.code in (400, 422):
                raise AiInvalidRequestError(
                    message=f"Ollama rejected embedding request ({ex.code}): {error_body or ex.reason}",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
            elif ex.code == 429:
                raise AiRateLimitError(
                    message="Ollama concurrency or rate limit exceeded",
                    details={"http_status": 429, "endpoint": url, "error_body": error_body},
                ) from ex
            elif ex.code in (500, 502, 503, 504):
                raise AiProviderUnavailableError(
                    message=f"Ollama daemon temporary server error ({ex.code}): {error_body or ex.reason}",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
            else:
                raise AiError(
                    message=f"HTTP {ex.code} error from Ollama: {ex.reason}",
                    error_code="AI_HTTP_ERROR",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
        except urllib.error.URLError as ex:
            if isinstance(ex.reason, (socket.timeout, TimeoutError)) or (
                isinstance(ex.reason, str) and "timed out" in ex.reason.lower()
            ):
                raise AiTimeoutError(
                    message=f"Operation timed out after {self.timeout_seconds}s waiting for Ollama embedding: {ex.reason}",
                    details={"endpoint": url, "timeout_seconds": self.timeout_seconds, "reason": str(ex.reason)},
                ) from ex
            raise AiProviderUnavailableError(
                message=f"Failed to reach Ollama endpoint at {url}: {ex.reason}",
                details={"endpoint": url, "reason": str(ex.reason)},
            ) from ex
        except (socket.timeout, TimeoutError) as ex:
            raise AiTimeoutError(
                message=f"Operation timed out after {self.timeout_seconds}s waiting for Ollama embedding",
                details={"endpoint": url, "timeout_seconds": self.timeout_seconds},
            ) from ex

    def _execute_embed_api(self, model: str, inputs: Sequence[str]) -> Dict[str, Any]:
        """Execute request against Ollama /api/embed endpoint (supports batch)."""
        payload = {
            "model": model,
            "input": list(inputs),
        }
        return self._send_http_request("/api/embed", payload)

    def _execute_legacy_embeddings_api(self, model: str, prompt: str) -> List[float]:
        """Execute single request against legacy Ollama /api/embeddings endpoint."""
        payload = {
            "model": model,
            "prompt": prompt,
        }
        res = self._send_http_request("/api/embeddings", payload)
        embedding = res.get("embedding")
        if not isinstance(embedding, list):
            raise AiInvalidRequestError(
                message="Malformed response from /api/embeddings: missing 'embedding' field",
                details={"response": res},
            )
        return [float(x) for x in embedding]

    async def embed(
        self,
        request: EmbeddingRequest,
        context: Optional[AiOperationContext] = None,
    ) -> EmbeddingResponse:
        """Execute embedding generation with retry on transient errors."""
        model = request.model or self.default_model
        attempt = 0
        last_transient_error: Optional[AiTransientError] = None

        while attempt <= self.max_retries:
            try:
                current_task = asyncio.current_task()
                if current_task and current_task.cancelled():
                    raise asyncio.CancelledError()

                start_time = time.monotonic()

                # Attempt primary /api/embed endpoint
                try:
                    raw = await asyncio.to_thread(self._execute_embed_api, model, request.inputs)
                    raw_vectors = raw.get("embeddings", [])
                    total_duration_ns = raw.get("total_duration")
                    prompt_eval_count = raw.get("prompt_eval_count", 0)
                except AiModelNotFoundError:
                    raise
                except AiError as ex:
                    # If /api/embed is not supported (404 or method not allowed), fallback to legacy /api/embeddings
                    if ex.details.get("http_status") == 404:
                        raw_vectors = []
                        for inp in request.inputs:
                            vec = await asyncio.to_thread(self._execute_legacy_embeddings_api, model, inp)
                            raw_vectors.append(vec)
                        total_duration_ns = None
                        prompt_eval_count = 0
                    else:
                        raise

                if not raw_vectors:
                    raise AiInvalidRequestError(
                        message="Ollama returned empty embeddings vector list",
                        details={"model": model, "inputs_count": len(request.inputs)},
                    )

                dimensions = len(raw_vectors[0])
                embeddings = [[float(val) for val in vec] for vec in raw_vectors]

                latency_ms = (
                    (total_duration_ns / 1_000_000.0)
                    if total_duration_ns
                    else round((time.monotonic() - start_time) * 1000.0, 2)
                )

                usage = UsageMetrics(input_tokens=prompt_eval_count) if prompt_eval_count > 0 else None

                metadata: Dict[str, Any] = {
                    "endpoint": self.endpoint,
                    "inputs_count": len(request.inputs),
                }
                if context:
                    metadata["trace_id"] = context.trace_id
                    metadata["span_id"] = context.span_id
                    metadata["operation_name"] = context.operation_name

                return EmbeddingResponse(
                    embeddings=embeddings,
                    model=model,
                    dimensions=dimensions,
                    usage=usage,
                    latency_ms=latency_ms,
                    metadata=metadata,
                )

            except AiTransientError as ex:
                last_transient_error = ex
                attempt += 1
                if attempt > self.max_retries:
                    raise

                backoff = self.backoff_base_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

            except Exception:
                raise

        if last_transient_error:
            raise last_transient_error
        raise AiProviderUnavailableError("Max retries exceeded without valid embedding response")

    async def check_health(self) -> bool:
        """Verify that the Ollama service is reachable."""
        try:
            await asyncio.to_thread(self._send_http_request, "/api/tags", None)
            return True
        except Exception:
            return False

    async def get_installed_models(self) -> List[str]:
        """Retrieve list of model names currently installed in the Ollama instance."""
        try:
            res = await asyncio.to_thread(self._send_http_request, "/api/tags", None)
            models = res.get("models", [])
            return [m.get("name", "") for m in models if m.get("name")]
        except Exception:
            return []
