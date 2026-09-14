# AI Observability, Tracing & Telemetry Architecture

## 1. Domain Scope

The `docs/observability/` directory establishes the telemetry standards, distributed tracing conventions, token metrics, and operational dashboards required for monitoring enterprise AI applications.

All applications in this repository must implement the **OpenTelemetry GenAI Semantic Conventions** to provide complete transparency into stochastic model interactions.

---

## 2. OpenTelemetry GenAI Semantic Conventions

Every AI interaction (LLM completion, chat turn, embedding calculation, tool execution, and vector search) must emit an OpenTelemetry span populated with standardized semantic attributes:

```
┌───────────────────────────────────────┬────────────────────────────────────────────────────────┐
│ Standard OTel Span Attribute          │ Example Value / Description                            │
├───────────────────────────────────────┼────────────────────────────────────────────────────────┤
│ `gen_ai.system`                       │ `"ollama"` | `"openai"` | `"azure_openai"`             │
│ `gen_ai.request.model`                │ `"llama3:8b-instruct-q4_K_M"`                         │
│ `gen_ai.response.model`               │ `"llama3:8b-instruct-q4_K_M"`                         │
│ `gen_ai.request.temperature`          │ `0.2`                                                  │
│ `gen_ai.request.top_p`                │ `0.95`                                                 │
│ `gen_ai.usage.input_tokens`           │ `142`                                                  │
│ `gen_ai.usage.output_tokens`          │ `68`                                                   │
│ `gen_ai.usage.total_tokens`           │ `210`                                                  │
│ `gen_ai.client.token_cost_usd`        │ `0.000` (Local Ollama) | `$0.00042`                    │
│ `gen_ai.response.finish_reasons`      │ `["stop"]` | `["length"]` | `["tool_calls"]`           │
└───────────────────────────────────────┴────────────────────────────────────────────────────────┘
```

---

## 3. Core Operational Metrics

Applications must export the following metrics to Prometheus / OpenTelemetry Collector:

1. **Time-to-First-Token (TTFT)**: Histogram measuring the latency from initial request dispatch until the first token chunk is received (crucial for interactive UX).
2. **Total Request Duration**: End-to-end execution latency per model provider.
3. **Token Throughput**: Tokens generated per second ($T/s$).
4. **Token Consumption Rate**: Cumulative input and output tokens grouped by tenant, model, and application.
5. **Provider Error & Fallback Rate**: Counter tracking HTTP 429, timeouts, and circuit breaker trip events.

---

## 4. Privacy & Telemetry Redaction

To prevent sensitive data leakage:
* **PII & Raw Prompts**: Raw user prompts and completions must have confidential customer identifiers redacted before exporting to non-ephemeral telemetry collectors.
* **Audit Logging**: Production audit logs must store trace correlation IDs (`trace_id`, `span_id`) to allow auditing without exposing plain text in operational dashboards.

Must pass **[Quality Gate F (Observability)](file:///Users/avadhutkore/Documents/code/products/ai-application-architecture/QUALITY-GATES.md#gate-f-observability--telemetry)**.
