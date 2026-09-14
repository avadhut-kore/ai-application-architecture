# Reliability, Resilience & Error Handling Standards

This document establishes the error taxonomy, retry policies, circuit breaking mechanics, timeout disciplines, and graceful degradation strategies across the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Reliability standards in this document satisfy Gate G6 and Gate G1 in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). AI inference endpoints are inherently prone to latency variance, rate limiting, and output non-determinism. Applications must be architected for resilience from the ground up.

---

## 1. AI Failure Modes & Error Taxonomy

To prevent cascading system collapse, failures must be classified into three distinct categories before deciding on a recovery strategy:

```
                          ┌────────────────────────┐
                          │    System Exception    │
                          └───────────┬────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌───────────────────┐       ┌───────────────────┐       ┌───────────────────┐
│ 1. Transient      │       │ 2. Non-Transient  │       │ 3. Semantic /     │
│    Errors         │       │    (Permanent)    │       │    Model Errors   │
├───────────────────┤       ├───────────────────┤       ├───────────────────┤
│ • HTTP 429 (Rate) │       │ • HTTP 400 (Bad)  │       │ • Malformed JSON  │
│ • HTTP 503 (Down) │       │ • HTTP 401 / 403  │       │ • Schema Mismatch │
│ • Network Timeout │       │ • Context Overflow│       │ • Guardrail Block │
│ • Connect Reset   │       │ • Model Missing   │       │ • Refusal Output  │
└───────────────────┘       └───────────────────┘       └───────────────────┘
```

| Error Category | Characteristics | Permitted Action | Prohibited Action |
| :--- | :--- | :--- | :--- |
| **1. Transient Errors** | Temporary network interruption, server busy, or rate limit quota replenishment. | **Conditional Retry** with exponential backoff and jitter; circuit breaker monitoring. | Never retry immediately without delay; never retry indefinitely. |
| **2. Non-Transient Errors** | Client invalid request, invalid authentication, model does not exist, context window exceeded. | **Fail Fast**: Log error, return RFC 7807 problem details, abort transaction. | **Never retry**. Retrying deterministic errors wastes tokens and amplifies traffic. |
| **3. Semantic AI Errors** | Model returns valid HTTP 200, but output fails schema validation, is unparseable, or hallucinates. | **Single Correction Re-prompt** or fall back to rule-based extractive handler. | Do not loop indefinitely re-prompting the model. Maximum 1 automated schema repair retry. |

---

## 2. Conditional Retry with Exponential Backoff & Jitter

When retrying transient failures, applications must apply exponential backoff with full jitter to avoid the "thundering herd" problem:

$$\text{Delay} = \text{random}(0, \, \min(\text{MaxDelay}, \, \text{BaseDelay} \times 2^{\text{attempt}}))$$

### Standard Policy Parameters
* **Max Retry Attempts**: 3 attempts maximum.
* **Base Delay**: 500 ms.
* **Max Delay**: 8,000 ms.
* **Jitter**: Full random jitter across the computed interval.

### Implementation Pattern (.NET Polly Example)
```csharp
var retryPipeline = new ResiliencePipelineBuilder<HttpResponseMessage>()
    .AddRetry(new RetryStrategyOptions<HttpResponseMessage>
    {
        ShouldHandle = new PredicateBuilder<HttpResponseMessage>()
            .Handle<HttpRequestException>()
            .HandleResult(response => response.StatusCode == HttpStatusCode.TooManyRequests
                                   || response.StatusCode == HttpStatusCode.ServiceUnavailable),
        MaxRetryAttempts = 3,
        BackoffType = DelayBackoffType.Exponential,
        UseJitter = true,
        Delay = TimeSpan.FromMilliseconds(500),
        MaxDelay = TimeSpan.FromSeconds(8)
    })
    .Build();
```

---

## 3. Circuit Breaking Architecture

When downstream AI inference providers or vector databases experience persistent outages, a circuit breaker must trip to prevent thread exhaustion and queue pileups:

```
        Successes
     ┌─────────────┐
     │             ▼
┌─────────┐   Failure Threshold    ┌────────┐
│ CLOSED  │ ─────────────────────► │  OPEN  │ ──► [Fail Fast / Cached Fallback]
└─────────┘                        └────────┘
     ▲                                  │
     │ Half-Open Probe Passes           │ Cooldown Period (e.g. 30s)
     │                                  ▼
     └──────────────────────────── ┌───────────┐
                                   │ HALF-OPEN │
                                   └───────────┘
```

* **Threshold**: Trip to `OPEN` when failure rate exceeds 50% over a 30-second sampling window (minimum 10 requests).
* **Cooldown**: Remain `OPEN` for 30 seconds before transitioning to `HALF-OPEN`.
* **Half-Open Probe**: Allow 3 consecutive requests to probe service recovery. If all succeed, reset to `CLOSED`; if any fail, return to `OPEN`.

---

## 4. Mandatory Timeouts & Cancellation Propagation

Every network call to an AI inference endpoint, vector database, or external tool must be bound by strict timeouts:

* **Inference Timeout**: Set explicit timeouts based on model capability (e.g., 30s for small local models, 60s for large reasoning models).
* **Cancellation Propagation**:
  * In .NET: Pass `CancellationToken` through all async call stacks.
  * In Python: Pass `asyncio.timeout()` or `asyncio.wait_for()`.
  * In TypeScript: Pass `AbortSignal` to `fetch()` or client SDKs.
* When a user disconnects or an upstream client closes connection, immediately trigger cancellation to release GPU and inference resources.

---

## 5. Graceful Degradation Strategies

When AI inference is completely unavailable, systems must degrade gracefully rather than presenting unhandled fatal crashes:

1. **Local Model Fallback**: Fall back from primary model to a lightweight secondary local model (e.g., from `llama3.2:3b` to `phi3:mini`).
2. **Deterministic Extractive Fallback**: Fall back from generative synthesis to deterministic keyword extraction or pre-cached FAQ responses.
3. **Structured Degraded Response**: Return a partial response with explicit metadata indicating degraded mode:
   ```json
   {
     "status": "degraded",
     "result": "System currently operating in degraded mode. Generating summary from cached document headers.",
     "data": { ... }
   }
   ```
