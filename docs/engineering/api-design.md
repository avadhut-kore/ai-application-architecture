# API Design & Contract Standards

This document establishes the RESTful conventions, streaming protocols, error schemas, versioning rules, and OpenAPI specification standards for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> API standards defined in this document satisfy [`Gate A (Architecture & Structural Boundaries)`](../../QUALITY-GATES.md#gate-a--architecture--structural-boundaries) and [`Gate J (Production Readiness & Resilience)`](../../QUALITY-GATES.md#gate-j--production-readiness--resilience) in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). All external and inter-service interfaces must be explicitly documented, strongly typed, and resilient against client desynchronization.

---

## 1. Resource-Oriented RESTful Architecture

APIs must adhere to resource-oriented HTTP conventions:

* **Resource Naming**: Use lowercase, hyphenated plural nouns for resource paths (`/api/v1/document-analyses`, `/api/v1/chat-sessions`).
* **HTTP Verbs**:
  * `GET`: Retrieve representations without mutating state (safe and idempotent).
  * `POST`: Create new resources or dispatch complex generative inference jobs.
  * `PUT`: Replace or update complete existing resources (idempotent).
  * `PATCH`: Partially update existing resources.
  * `DELETE`: Remove resources (idempotent).
* **HTTP Status Codes**:
  * `200 OK`: Successful synchronous execution returning a payload.
  * `201 Created`: Successful resource creation (include `Location` header).
  * `202 Accepted`: Asynchronous or long-running AI job queued for background execution.
  * `204 No Content`: Successful execution returning no body.
  * `400 Bad Request`: Malformed syntax or schema validation failure.
  * `401 Unauthorized`: Missing or invalid authentication credentials.
  * `403 Forbidden`: Authenticated caller lacks permissions for the target resource.
  * `404 Not Found`: Resource does not exist.
  * `422 Unprocessable Entity`: Syntactically valid body fails semantic business rules.
  * `429 Too Many Requests`: Rate limit or token quota exceeded (include `Retry-After` header).
  * `500 Internal Server Error`: Unhandled server exception.
  * `503 Service Unavailable`: Downstream AI inference engine unreachable.

---

## 2. Token Streaming Protocols (SSE vs. WebSockets)

Generative AI applications frequently require streaming token-by-token output to ensure low perceived latency (time-to-first-token):

| Protocol | Preferred Use Case | Architecture & Semantics |
| :--- | :--- | :--- |
| **Server-Sent Events (SSE)** | Unidirectional text/token streaming from server to client. | Standard HTTP/HTTPS (`text/event-stream`). Native browser `EventSource` support, automatic reconnection, lightweight. |
| **WebSockets (WS)** | Full-duplex, bidirectional communication (e.g., real-time audio voice AI). | Persistent bidirectional TCP socket (`ws://`, `wss://`). Higher state management complexity; reserved for full-duplex interactions. |

### Standard SSE Stream Format
Streaming endpoints must format SSE payloads as typed events:

```
event: token
data: {"content": "The", "index": 0}

event: token
data: {"content": " architectural", "index": 1}

event: done
data: {"finish_reason": "stop", "total_tokens": 125}
```

---

## 3. RFC 7807 / RFC 9457 Problem Details Error Schema

All error responses across all APIs must return `Content-Type: application/problem+json` conforming to RFC 7807 / RFC 9457:

```json
{
  "type": "https://errors.ai-architecture.dev/model-rate-limit-exceeded",
  "title": "Model Rate Limit Exceeded",
  "status": 429,
  "detail": "The Ollama inference backend has exceeded its concurrent request capacity. Please retry after 5 seconds.",
  "instance": "/api/v1/chat-sessions/session-981/messages",
  "trace_id": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
  "invalid_params": []
}
```

---

## 4. OpenAPI 3.1 Contracts & Interactive Documentation

* **Single Source of Truth**:
  * Reference architectures must expose an OpenAPI 3.1 compliant schema generated automatically from strongly typed models (via FastAPI, ASP.NET Core OpenApi/Swashbuckle, Springdoc, or tsoa).
* **Complete Metadata**:
  * Every endpoint must document operation summary, description, request body examples, response models for 2xx and 4xx status codes, and security requirements.
* **Interactive UI**:
  * Applications must provide a lightweight Swagger UI or Scalar UI at `/swagger` or `/docs` for local manual inspection in development mode.

---

## 5. Idempotency in State-Mutating Operations

AI operations can be high-cost and slow. If a network blip occurs during a generative generation or document ingestion workflow, a client retry must not result in duplicate billing or duplicate data records:

* **`Idempotency-Key` Header**:
  * For mutating operations (`POST /api/v1/documents/analyze`), clients may provide an `Idempotency-Key: <UUIDv4>` header.
  * The server checks an in-memory cache or Redis store. If an identical key is in progress or completed, the server returns the cached response or a `409 Conflict` without re-running inference.
