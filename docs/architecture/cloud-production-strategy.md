# Cloud & Production Deployment Strategy

## 1. Architectural Parity: Local to Production

A major failure in enterprise AI projects is the **Environment Disconnect**: applications prototyped locally against lightweight scripts must be substantially rewritten when deployed to production to accommodate enterprise gateways, authentication, rate limits, and cloud-managed model endpoints.

In `ai-application-architecture`, we mandate **Architectural Parity**:

> **The application domain logic, workflow orchestration, and internal port contracts must be 100% identical whether executing locally on a developer laptop or running in an enterprise cloud Kubernetes cluster.**

Transitioning an application from local development to production is achieved exclusively by swapping **infrastructure adapters** and adjusting **environment configuration**, with zero modifications to application source code.

---

## 2. Environment Comparison Topology

```
 LOCAL ENVIRONMENT (Developer Workstation)

  ┌────────────────────────────────────────────────────────────┐
  │                 Application Boundary                       │
  │     Domain Logic  │  Workflows  │  Deterministic Rules     │
  └──────────────────────────────┬─────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │               Provider Abstraction Layer                   │
  │                  ILlmProvider Port                         │
  └──────────────────────────────┬─────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │                Ollama Infrastructure Adapter               │
  └──────────────────────────────┬─────────────────────────────┘
                                 │ HTTP (localhost:11434)
  ┌──────────────────────────────▼─────────────────────────────┐
  │              Ollama Local Engine (Llama 3 8B)              │
  └────────────────────────────────────────────────────────────┘


 PRODUCTION ENVIRONMENT (Enterprise Cloud / Kubernetes)

  ┌────────────────────────────────────────────────────────────┐
  │                 Application Boundary                       │
  │     Domain Logic  │  Workflows  │  Deterministic Rules     │
  │              (IDENTICAL COMPILED CODE)                     │
  └──────────────────────────────┬─────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │               Provider Abstraction Layer                   │
  │                  ILlmProvider Port                         │
  └──────────────────────────────┬─────────────────────────────┘
                                 │
  ┌──────────────────────────────▼─────────────────────────────┐
  │         Enterprise Cloud / Gateway Adapter                 │
  └──────────────────────────────┬─────────────────────────────┘
                                 │ HTTPS (mTLS / IAM / PrivateLink)
  ┌──────────────────────────────▼─────────────────────────────┐
  │           Enterprise AI Model Gateway                      │
  │   Rate Limiting │ Token Quota │ Circuit Breaker │ Caching  │
  └──────────────┬──────────────────────────────┬──────────────┘
                 │                              │
  ┌──────────────▼───────────────┐ ┌────────────▼──────────────┐
  │ Private Enterprise Endpoint  │ │ Public Cloud Provider     │
  │ (Self-hosted vLLM on EKS)    │ │ (Azure OpenAI / Anthropic)│
  └──────────────────────────────┘ └───────────────────────────┘
```

---

## 3. Configuration-Driven Provider Resolution

Provider selection is resolved dynamically at application startup via Dependency Injection and environment variables, adhering to the **Twelve-Factor App** configuration methodology:

```ini
# Local Development Configuration (.env)
AI_PROVIDER_TYPE=ollama
AI_MODEL_NAME=llama3:8b-instruct-q4_K_M
AI_BASE_URL=http://localhost:11434
AI_EMBEDDING_PROVIDER=ollama
AI_EMBEDDING_MODEL=nomic-embed-text

# Production Configuration (Environment Secret Injection)
AI_PROVIDER_TYPE=azure_openai
AI_MODEL_NAME=gpt-4o-enterprise
AI_BASE_URL=https://corp-ai-gateway.internal.net
AI_GATEWAY_AUTH_MODE=managed_identity
AI_EMBEDDING_PROVIDER=azure_openai
AI_EMBEDDING_MODEL=text-embedding-3-small
```

The application's composition root instantiates the corresponding adapter:

```python
# Composition Root / DI Factory
def get_llm_provider(config: AppConfig) -> ILlmProvider:
    match config.provider_type:
        case "ollama":
            return OllamaLlmAdapter(base_url=config.base_url, model=config.model_name)
        case "azure_openai":
            return AzureOpenAiLlmAdapter(endpoint=config.base_url, model=config.model_name)
        case "anthropic":
            return AnthropicLlmAdapter(endpoint=config.base_url, model=config.model_name)
        case _:
            raise ConfigurationError(f"Unsupported AI provider: {config.provider_type}")
```

---

## 4. Enterprise Production Capabilities

When deployed to production, the architecture introduces enterprise-grade cross-cutting capabilities via the **Model Gateway** without polluting application code:

### 4.1 Resilient Fallback Routing
If the primary production model endpoint returns HTTP 429 (Rate Limited), 500, or 503, the gateway automatically routes the payload to a designated secondary model endpoint (e.g., falling back from Azure OpenAI US-East to Azure OpenAI US-West, or from Claude 3.5 Sonnet to GPT-4o).

### 4.2 Rate Limiting & Token Quota Enforcement
The gateway coordinates token-bucket rate limits per tenant/user, preventing a single rogue workload or denial-of-service attack from consuming the entire organizational API allocation.

### 4.3 Semantic Response Caching
High-volume query patterns (such as standard policy queries in an enterprise knowledge base) are cached using exact-match hashing and semantic similarity search in Redis. This reduces inference latency from $>1.5$s to $<15$ms and drops token expenses by up to 40%.

### 4.4 Centralized Audit & Telemetry
In production, OpenTelemetry trace spans and metrics are exported directly to enterprise observability clusters (Datadog, Dynatrace, or self-hosted Grafana Mimir/Tempo). Token consumption is tagged with tenant metadata for internal chargeback accounting.

---

## 5. Architectural Invariant Summary

1. **Zero Domain Rewrites**: Moving from Ollama to Azure OpenAI, AWS Bedrock, or GCP Vertex AI must require zero changes to domain entities, workflows, or validation schemas.
2. **Deterministic Fallbacks**: If all cloud endpoints fail, the gateway can degrade gracefully to local models or pre-computed static responses.
3. **Identity & Secret Isolation**: Production endpoints authenticate via cloud-native IAM (AWS IAM roles, Azure Managed Identity, GCP Workload Identity) rather than static long-lived API keys.
