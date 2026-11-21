"""Runtime OpenTelemetry instrumentation; contracts remain dependency-free."""

from __future__ import annotations

from functools import wraps
import atexit
import os
import hashlib
from pathlib import Path
from typing import Any, Awaitable, Callable, Coroutine, ParamSpec, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

P = ParamSpec("P")
T = TypeVar("T")


def configure_local_tracing() -> None:
    """Opt in to metadata-only local JSON spans through AI_TRACE_FILE."""
    destination = os.environ.get("AI_TRACE_FILE")
    if not destination:
        return
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

    if isinstance(trace.get_tracer_provider(), TracerProvider):
        return
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    stream = path.open("a", encoding="utf-8")
    provider = TracerProvider()
    provider.add_span_processor(
        SimpleSpanProcessor(
            ConsoleSpanExporter(out=stream, formatter=lambda span: span.to_json(indent=None) + "\n")
        )
    )
    trace.set_tracer_provider(provider)

    def shutdown() -> None:
        provider.shutdown()
        stream.close()

    atexit.register(shutdown)


def traced(
    name: str, provider: str
) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Coroutine[Any, Any, T]]]:
    """Emit metadata-only spans, including errors without exporting exception payloads."""

    def decorate(fn: Callable[P, Awaitable[T]]) -> Callable[P, Coroutine[Any, Any, T]]:
        @wraps(fn)
        async def wrapped(*args: P.args, **kwargs: P.kwargs) -> T:
            request: Any = kwargs.get("request") or (args[1] if len(args) > 1 else None)
            with trace.get_tracer("ai-application-architecture").start_as_current_span(
                name,
                record_exception=False,
                set_status_on_exception=False,
            ) as span:
                span.set_attribute("gen_ai.system", provider)
                if name.startswith("workflow."):
                    workflow_id = kwargs.get("workflow_id") or (args[1] if len(args) > 1 else None)
                    if isinstance(workflow_id, str):
                        span.set_attribute(
                            "workflow.id_sha256",
                            hashlib.sha256(workflow_id.encode("utf-8")).hexdigest(),
                        )
                model = getattr(request, "model", None)
                if model:
                    span.set_attribute("gen_ai.request.model", model)
                try:
                    response = await fn(*args, **kwargs)
                except BaseException as exc:
                    span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                    span.set_attribute("error.type", type(exc).__name__)
                    raise
                response_model = getattr(response, "model", None)
                if response_model:
                    span.set_attribute("gen_ai.response.model", response_model)
                usage = getattr(response, "usage", None)
                if usage:
                    span.set_attribute("gen_ai.usage.input_tokens", usage.input_tokens)
                    span.set_attribute("gen_ai.usage.output_tokens", usage.output_tokens)
                metadata = getattr(response, "metadata", {})
                if isinstance(metadata, dict) and "fallback_used" in metadata:
                    span.set_attribute("gen_ai.fallback_used", bool(metadata["fallback_used"]))
                receipt = response[0] if isinstance(response, tuple) and response else response
                operation_status = getattr(receipt, "status", "")
                if isinstance(operation_status, str) and operation_status:
                    span.set_attribute("operation.status", operation_status.lower())
                failed = isinstance(operation_status, str) and operation_status.lower() in {
                    "failed",
                    "ambiguous",
                    "denied",
                    "max_steps_reached",
                }
                failed = failed or (isinstance(response, dict) and response.get("error") is True)
                failed = failed or getattr(response, "schema_valid", True) is False
                if failed or getattr(response, "is_error", False):
                    span.set_status(Status(StatusCode.ERROR, "operation_failed"))
                else:
                    span.set_status(Status(StatusCode.OK))
                return response

        return wrapped

    return decorate
