# Observability & Telemetry Standards

This document establishes the distributed tracing, structured logging, performance metrics, and OpenTelemetry standards for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Telemetry controls in this document satisfy Gate G6 and Gate G5 in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). In AI workloads, observability must encompass not only system health (CPU, RAM, latency) but also AI-specific operational metrics (token counts, prompt lengths, model identifiers, and finish reasons).

---

## 1. The Three Observability Pillars in AI Systems

Enterprise AI applications require unified instrumentation across three complementary pillars:

```
┌────────────────────────────────────────────────────────┐
│ 1. Distributed Tracing (OpenTelemetry GenAI Spans)     │
│    • Prompt construction  • Vector similarity search   │
│    • LLM inference call   • Response parsing & guard   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. Structured JSON Logging (Context-Rich & Redacted)   │
│    • Correlated trace_id  • Model name & parameters    │
│    • Error details        • PII-sanitized message      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. Operational Metrics & SLIs                          │
│    • P50 / P95 / P99 Latency • Input / Output Tokens   │
│    • Error rate & HTTP status • Rate-limit throttle count│
└────────────────────────────────────────────────────────┘
```

---

## 2. OpenTelemetry GenAI Semantic Conventions

Applications instrumenting LLM operations must conform to the **OpenTelemetry Semantic Conventions for Generative AI Systems**:

| Span Attribute Key | Type | Description & Example |
| :--- | :--- | :--- |
| `gen_ai.system` | string | Target AI provider or runtime (`ollama`, `openai`, `anthropic`, `onnx`). |
| `gen_ai.request.model` | string | Requested model name (`llama3.2:3b`, `gpt-4o-mini`). |
| `gen_ai.response.model` | string | Actual model name returned by provider. |
| `gen_ai.request.temperature` | double | Sampling temperature (`0.0`, `0.7`). |
| `gen_ai.request.max_tokens` | int | Maximum tokens allocated for completion. |
| `gen_ai.usage.input_tokens` | int | Number of prompt / input tokens consumed. |
| `gen_ai.usage.output_tokens` | int | Number of completion / output tokens generated. |
| `gen_ai.response.finish_reasons` | string[] | Termination reason (`["stop"]`, `["length"]`, `["content_filter"]`). |

### Trace Hierarchy Example
```
[HTTP POST /api/v1/documents/summarize] (Root Span)
  └── [rag.retrieve_chunks] (Retrieval Span - 45ms)
  │     ├── vector_db.query (15ms)
  │     └── rerank.cross_encoder (30ms)
  └── [gen_ai.chat] (Model Span - 1,250ms)
        ├── gen_ai.system: "ollama"
        ├── gen_ai.request.model: "llama3.2:3b"
        ├── gen_ai.usage.input_tokens: 842
        └── gen_ai.usage.output_tokens: 180
```

---

## 3. Distributed Correlation & Request Context

Every interaction must carry an end-to-end correlation identifier:

* **W3C Trace Context**: Use `traceparent` and `tracestate` HTTP headers for standard distributed trace propagation.
* **Correlation Header**: Support `X-Correlation-ID` header across incoming HTTP requests. If absent at edge gateway, generate a cryptographically secure UUIDv4 and attach it to the request context.
* **Log Correlation**: All log entries generated during the handling of a request must include the active `trace_id`, `span_id`, and `correlation_id`.

---

## 4. Structured JSON Logging Specification

Applications must output logs formatted as single-line JSON objects to standard output (`stdout`):

```json
{
  "timestamp": "2026-09-14T12:00:00.123Z",
  "level": "INFO",
  "service": "document-intelligence-service",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "correlation_id": "c1e67a5b-9f6b-4e8b-8a22-44df0e123456",
  "event": "llm_completion_finished",
  "model": "llama3.2:3b",
  "duration_ms": 1250,
  "tokens": {
    "prompt": 842,
    "completion": 180,
    "total": 1022
  },
  "message": "LLM inference completed successfully."
}
```

---

## 5. PII Redaction & Data Protection in Telemetry

> [!CAUTION]
> **Zero PII in Unencrypted Telemetry**  
> Under no circumstances may raw customer passwords, national identification numbers, credit cards, or unredacted personal prompts be broadcast to central logging aggregators or APM dashboards.

* **Prompt Redaction Rules**:
  * In production environments, log prompt metadata (length in characters, token count, template identifier) rather than raw prompt text.
  * If prompt logging is explicitly enabled for debugging, run an automated regex/NER scrubber to mask email addresses, phone numbers, and names before export.
* **Bounded Buffering**:
  * Telemetry exporters must use asynchronous, non-blocking batch processors with bounded internal queues. If the telemetry collector becomes unreachable, log events must be dropped rather than crashing or hanging the main application.
