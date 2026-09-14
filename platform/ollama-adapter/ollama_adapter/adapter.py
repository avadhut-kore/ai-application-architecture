"""Ollama implementation adapter for the provider-neutral TextGenerationPort."""

from __future__ import annotations

import asyncio
import json
import socket
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Mapping, Optional

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
    CompletionRequest,
    CompletionResponse,
    FinishReason,
    UsageMetrics,
)
from contracts.ports import TextGenerationPort
from contracts.telemetry import AiOperationContext


class OllamaAdapter(TextGenerationPort):
    """Concrete model adapter communicating with a local or remote Ollama daemon.

    Adheres strictly to the provider-neutral TextGenerationPort protocol using
    standard library HTTP client capabilities (zero external runtime dependencies).
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        default_model: str = "llama3.2",
        timeout_seconds: float = 30.0,
        max_retries: int = 2,
        backoff_base_seconds: float = 0.5,
    ) -> None:
        """Initialize the Ollama adapter with endpoint and execution policies."""
        self.endpoint = endpoint.rstrip("/")
        self.default_model = default_model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.backoff_base_seconds = backoff_base_seconds

    def _build_payload(self, request: CompletionRequest) -> Dict[str, Any]:
        """Transform a provider-neutral CompletionRequest into an Ollama API payload."""
        model = request.model if request.model else self.default_model
        options: Dict[str, Any] = {
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            options["num_predict"] = request.max_tokens
        if request.stop_sequences:
            options["stop"] = list(request.stop_sequences)

        payload: Dict[str, Any] = {
            "model": model,
            "stream": False,
            "options": options,
        }

        # If conversational messages are provided, route to /api/chat payload structure
        if request.messages:
            payload["messages"] = [
                {"role": msg.role.value, "content": msg.content}
                for msg in request.messages
            ]
        else:
            payload["prompt"] = request.prompt
            if request.system_prompt:
                payload["system"] = request.system_prompt

        # Support JSON format output constraint if specified in metadata
        if request.metadata and request.metadata.get("format") == "json":
            payload["format"] = "json"

        return payload

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
                model_name = (payload.get("model") if payload else "") or self.default_model
                raise AiModelNotFoundError(
                    model_name=model_name,
                    details={"http_status": 404, "endpoint": url, "error_body": error_body},
                ) from ex
            elif ex.code in (400, 422):
                raise AiInvalidRequestError(
                    message=f"Ollama rejected request ({ex.code}): {error_body or ex.reason}",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
            elif ex.code == 429:
                raise AiRateLimitError(
                    message="Ollama concurrency or rate limit exceeded",
                    details={"http_status": 429, "endpoint": url, "error_body": error_body},
                ) from ex
            elif ex.code in (500, 502, 503, 504):
                raise AiProviderUnavailableError(
                    message=f"Ollama daemon temporary server error ({ex.code}): {ex.reason}",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
            else:
                raise AiError(
                    message=f"HTTP {ex.code} error from Ollama: {ex.reason}",
                    error_code="AI_HTTP_ERROR",
                    details={"http_status": ex.code, "endpoint": url, "error_body": error_body},
                ) from ex
        except urllib.error.URLError as ex:
            raise AiProviderUnavailableError(
                message=f"Failed to reach Ollama endpoint at {url}: {ex.reason}",
                details={"endpoint": url, "reason": str(ex.reason)},
            ) from ex
        except (socket.timeout, TimeoutError) as ex:
            raise AiTimeoutError(
                message=f"Operation timed out after {self.timeout_seconds}s waiting for Ollama",
                details={"endpoint": url, "timeout_seconds": self.timeout_seconds},
            ) from ex

    def _map_response(self, raw: Dict[str, Any], requested_model: str) -> CompletionResponse:
        """Map raw Ollama JSON response to the provider-neutral CompletionResponse."""
        text = ""
        if "response" in raw:
            text = raw["response"]
        elif "message" in raw and isinstance(raw["message"], dict):
            text = raw["message"].get("content", "")

        model = raw.get("model", requested_model)
        done_reason = raw.get("done_reason", "stop")
        finish_reason = FinishReason.LENGTH if done_reason == "length" else FinishReason.STOP

        # Extract usage metrics
        prompt_tokens = raw.get("prompt_eval_count", 0)
        output_tokens = raw.get("eval_count", 0)
        usage: Optional[UsageMetrics] = None
        if prompt_tokens > 0 or output_tokens > 0:
            usage = UsageMetrics(input_tokens=prompt_tokens, output_tokens=output_tokens)

        # Extract latency in milliseconds from Ollama's nanosecond duration
        total_duration_ns = raw.get("total_duration")
        latency_ms = (total_duration_ns / 1_000_000.0) if total_duration_ns else None

        metadata: Dict[str, Any] = {
            "created_at": raw.get("created_at"),
            "eval_duration_ns": raw.get("eval_duration"),
            "load_duration_ns": raw.get("load_duration"),
        }

        return CompletionResponse(
            text=text,
            model=model,
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=latency_ms,
            metadata=metadata,
        )

    async def generate(
        self,
        request: CompletionRequest,
        context: Optional[AiOperationContext] = None,
    ) -> CompletionResponse:
        """Execute text generation with selective retry on transient errors."""
        payload = self._build_payload(request)
        path = "/api/chat" if request.messages else "/api/generate"
        requested_model = request.model if request.model else self.default_model

        attempt = 0
        last_transient_error: Optional[AiTransientError] = None

        while attempt <= self.max_retries:
            try:
                # Check for cancellation before executing HTTP call
                current_task = asyncio.current_task()
                if current_task and current_task.cancelled():
                    raise asyncio.CancelledError()

                start_time = time.monotonic()
                raw_response = await asyncio.to_thread(self._send_http_request, path, payload)
                response = self._map_response(raw_response, requested_model)

                # Fallback latency calculation if Ollama did not provide total_duration
                if response.latency_ms is None:
                    calc_latency = (time.monotonic() - start_time) * 1000.0
                    object.__setattr__(response, "latency_ms", round(calc_latency, 2))

                return response

            except AiTransientError as ex:
                last_transient_error = ex
                attempt += 1
                if attempt > self.max_retries:
                    raise

                backoff = self.backoff_base_seconds * (2 ** (attempt - 1))
                await asyncio.sleep(backoff)

            except Exception:
                # Fatal errors (AiNonTransientError, asyncio.CancelledError) fail immediately
                raise

        if last_transient_error:
            raise last_transient_error
        raise AiProviderUnavailableError("Max retries exceeded without valid response")

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
