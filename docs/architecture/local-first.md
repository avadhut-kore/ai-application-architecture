# Local-First AI Policy & Execution Modes

## 1. Executive Policy

This repository rejects the false dichotomy between "cloud-only AI development" and "mandating that every capability must run 100% disconnected on a laptop". 

We do **not** enforce an absolute dogma that every single application must run completely offline without internet connectivity. Such a rule would artificially prohibit realistic enterprise patterns like live telephony integration, web research, external SaaS webhooks, or hybrid enterprise deployments.

Instead, this repository establishes a pragmatic, tiered **Three-Mode Local-First Policy**:

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ MODE A: OFFLINE LOCAL                                                  │
 │ 100% self-contained on developer machine; zero internet or external API│
 ├────────────────────────────────────────────────────────────────────────┤
 │ MODE B: LOCAL-FIRST (DEFAULT POLICY)                                   │
 │ Core application runs locally; selected external dependencies permitted│
 ├────────────────────────────────────────────────────────────────────────┤
 │ MODE C: CLOUD-COMPARABLE                                               │
 │ Same architecture configurable against local models or cloud endpoints │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Three Execution Modes

### Mode A — Offline Local
* **Definition**: The entire system executes locally without any external network dependency, external AI endpoint, or third-party cloud service.
* **Component Stack**:
  * Local models via local runtimes (e.g., Ollama, llama.cpp, vLLM).
  * Local embedding generation.
  * Local containerized databases (PostgreSQL, SQLite).
  * Local vector indexing (pgvector, local vector files).
  * Local telemetry (in-memory or local OpenTelemetry collectors).
* **Applicability**: Highly sensitive data processing, air-gapped environments, core document processing, and foundational algorithm demonstration.

### Mode B — Local-First (The Default Policy)
* **Definition**: The core application, business logic, domain models, and primary reasoning loops run locally on the developer's workstation, but the system may integrate with selected external services where technically or architecturally required.
* **Permitted External Capabilities**:
  * Live web search and deep research APIs.
  * External telephony gateways (SIP / Twilio) for voice streaming.
  * External SaaS enterprise APIs (CRM, ERP, ticketing systems).
  * Outbound email, messaging, or notification webhooks.
* **Standard**: Developers should be able to run and test the core application logic locally with zero cloud AI inference costs. External services must be stubbed or mockable during automated unit test runs.

### Mode C — Cloud-Comparable
* **Definition**: The application architecture is designed such that the exact same application code, domain entities, and workflow state machines can execute against either local models or managed enterprise cloud providers purely through configuration changes.
* **Objective**: **Architectural Portability**, not identical model behavior. We recognize that open-weights local models (e.g., 8B parameters) and massive commercial cloud models (e.g., Claude 3.5 Sonnet, GPT-4o) exhibit different reasoning latencies and parameter capacities. The system's ports and adapters must accommodate both without code alterations.

---

## 3. Ollama Policy

**Ollama** is the preferred local foundation model runtime for reference implementations in this repository.

However, the following boundaries govern its use:

1. **Default Choice, Not the Architecture**: Ollama is a convenient developer tool and default implementation choice; it is **not** an architectural foundation. Applications must never hardcode Ollama-specific API assumptions, endpoints, or proprietary flags into domain or application logic.
2. **Provider Decoupling**: Applications must interface with foundation models via architectural ports (`ILlmClient`, `IEmbeddingClient`). The Ollama integration exists strictly as an infrastructure adapter (`OllamaAdapter`).
3. **Explicit Exceptions**: Reference implementations are permitted to use alternative local runtimes (e.g., vLLM for high-throughput GPU serving, llama.cpp for embedded edge execution) or cloud adapters when technical requirements dictate capabilities Ollama does not natively support. All exceptions must be explicitly documented in the application's architecture specification or ADR.

---

## 4. Multi-Provider Evolution

The architecture must support diverse providers beneath the abstraction port:

```
                              Application Port Layer
                               (ILlmClient Interface)
                                          │
                  ┌───────────────────────┼───────────────────────┐
                  ▼                       ▼                       ▼
          [Ollama Adapter]       [vLLM / Local IPC]     [Cloud Adapter]
          Default Local Run       High-Throughput GPU    Azure OpenAI / Claude
```

* **Local Runtimes**: Ollama, vLLM, llama.cpp, LocalAI.
* **Cloud Adapters**: Azure OpenAI, OpenAI, Anthropic Claude, Google Gemini, AWS Bedrock.
* **Specialized Runtimes**: Triton Inference Server, dedicated embedding microservices.

---

## 5. Developer Workstation Guidelines

To maintain accessibility for developers, reference implementations designed for Mode A and Mode B must document their minimum hardware profiles:
* **Lightweight Profile**: 8GB RAM, CPU-only (suitable for 3B parameter models like `phi3:mini` or `qwen2.5:3b`).
* **Standard Profile**: 16GB RAM / Apple Silicon unified memory (suitable for 8B parameter models like `llama3:8b-instruct-q4_K_M` and local PostgreSQL).
* **Heavy Profile**: 32GB+ RAM / dedicated GPU (for concurrent multimodal, vision, or multi-agent execution).
