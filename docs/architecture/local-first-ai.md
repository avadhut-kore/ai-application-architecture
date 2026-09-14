# Local-First AI Strategy & Runtime Standard

## 1. Executive Philosophy: Local-First Sovereignty

A foundational tenet of `ai-application-architecture` is **Local-First AI Sovereignty**:

> **A software engineer or architect should be able to clone this repository, run a single command, and execute the majority of reference applications on standard developer hardware without requiring commercial cloud API keys, credit cards, or external network access.**

Relying exclusively on proprietary cloud APIs for development creates severe friction: cost barriers, external rate limits, internet dependency, sensitive data leakage risks, and architectural coupling to closed-source provider behaviors. 

By designing for local execution first, we guarantee reproducibility, privacy, zero-cost continuous development, and true architectural portability.

---

## 2. Local-First Architecture & Runtime Topology

While **Ollama** is the designated default local foundation model runtime, the architecture **must never couple directly to Ollama**. 

All applications interact with models through a multi-tiered abstraction layer:

```
                            Local Runtime Execution Topology
                            
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      Developer Machine / Workstation                   │
 │                                                                        │
 │  ┌──────────────────────────────────────────────────────────────────┐  │
 │  │                         Application Core                         │  │
 │  │      Domain Logic  │  Deterministic Workflows  │  State Machines │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │                                  │
 │  ┌──────────────────────────────────▼───────────────────────────────┐  │
 │  │                 AI Provider Abstraction Port                     │  │
 │  │              ILlmProvider  │  IEmbeddingProvider                 │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │                                  │
 │  ┌──────────────────────────────────▼───────────────────────────────┐  │
 │  │                    Resilient Model Gateway                       │  │
 │  │         Auth  │  Rate Limiting  │  Caching  │  Telemetry         │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 │                                     │                                  │
 │  ┌──────────────────────────────────▼───────────────────────────────┐  │
 │  │                   Infrastructure Provider Adapter                │  │
 │  │                        Ollama Provider Adapter                   │  │
 │  └──────────────────────────────────┬───────────────────────────────┘  │
 └─────────────────────────────────────┼──────────────────────────────────┘
                                       │ HTTP / Native IPC
 ┌─────────────────────────────────────▼──────────────────────────────────┐
 │                     Ollama Local Runtime Engine                        │
 │  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
 │  │   Language Model (LLM/SLM)    │   │   Embedding Model            │  │
 │  │   e.g., Llama 3 (8B Q4_K_M)   │   │   e.g., nomic-embed-text     │  │
 │  └───────────────────────────────┘   └──────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────────────┘
```

### Architectural Responsibilities:
1. **Application Core**: Completely agnostic to model location or vendor. Invokes generic methods: `generate_structured()`, `embed_text()`.
2. **Provider Abstraction Port**: Defines strongly typed contracts in `building-blocks/`.
3. **Model Gateway**: Intercepts requests to handle local semantic caching, token metrics, and retry policies.
4. **Ollama Provider Adapter**: Translates abstract requests into Ollama REST API calls (`/api/chat`, `/api/embeddings`).
5. **Ollama Runtime Engine**: Executes 4-bit and 8-bit quantized models locally using hardware acceleration (Metal on macOS, CUDA on Linux/Windows).

---

## 3. Recommended Baseline Models for Local Execution

To ensure applications run smoothly on typical developer workstations (e.g., Apple Silicon with 16GB+ RAM or x86 laptops with 16GB+ RAM and mid-range GPU), the repository establishes standard baseline model profiles:

| Capability | Recommended Local Model | Parameter Size | Quantization | RAM / VRAM Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **General Reasoning & Tool Calling** | `llama3:8b-instruct-q4_K_M` | 8 Billion | 4-bit | $\approx 4.8\text{ GB}$ |
| **Lightweight / Fast Reasoning** | `phi3:mini` or `qwen2.5:3b` | 3.8B / 3B | 4-bit | $\approx 2.4\text{ GB}$ |
| **Dense Vector Embeddings** | `nomic-embed-text:v1.5` | 137 Million | FP16 | $\approx 280\text{ MB}$ |
| **Document / Vision Understanding** | `minicpm-v` or `llava:7b` | 7-8 Billion | 4-bit | $\approx 5.5\text{ GB}$ |
| **Code Generation & Review** | `qwen2.5-coder:7b` | 7 Billion | 4-bit | $\approx 4.5\text{ GB}$ |

---

## 4. Local Infrastructure Components & When Justified

In addition to Ollama, reference architectures may require supporting services. To avoid premature infrastructure bloat, each component is justified only when specific architectural requirements are present:

```
┌───────────────────────────┬───────────────────────────────┬──────────────────────────────────────────┐
│ Supporting Component      │ Technology Standard           │ Architectural Justification              │
├───────────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Relational & Vector Store │ PostgreSQL 16 + pgvector      │ Unified ACID transactions with vector    │
│                           │                               │ similarity for RAG applications.         │
├───────────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Distributed Session Cache │ Redis 7                       │ Ephemeral conversation session memory,   │
│                           │                               │ rate limiting, and embedding caching.    │
├───────────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Dedicated Vector Database │ Qdrant                        │ High-throughput HNSW indexing and hybrid │
│                           │                               │ search benchmarks (Phase 5+).            │
├───────────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Object Storage            │ MinIO                         │ Local S3-compatible storage for Document │
│                           │                               │ AI and multimodal assets (Phase 8+).     │
├───────────────────────────┼───────────────────────────────┼──────────────────────────────────────────┤
│ Telemetry & Tracing       │ OpenTelemetry Collector +     │ Local observability, GenAI trace spans,  │
│                           │ Prometheus + Jaeger / Grafana │ and token usage analysis (Phase 11+).    │
└───────────────────────────┴───────────────────────────────┴──────────────────────────────────────────┘
```

**Rule**: An application must not spin up supporting containers in its `docker-compose.yml` unless its functional requirements directly depend on them.

---

## 5. Developer Workstation Hardware Profiles

Applications in this repository must specify their minimum and recommended hardware profile in their `README.md`:

* **Profile 1: Minimal (8GB RAM)**: Suitable for lightweight SLMs (`qwen2.5:3b`, `phi3:mini`) and small embedding workloads.
* **Profile 2: Standard Developer (16GB RAM / M-series / 6GB VRAM)**: The primary baseline. Supports 8B parameter instruct models and local PostgreSQL/pgvector.
* **Profile 3: Heavy Multi-Agent / Multimodal (32GB+ RAM / 12GB+ VRAM)**: Required for running multi-model pipelines simultaneously (e.g., Vision model + Reasoning model + Embedding model).

---

## 6. Zero-API-Key Local Validation Guarantee

Every reference implementation is subjected to an automated validation check:
* **The No-Key Test**: The application test suite must pass completely with all external API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.) set to empty or unconfigured strings.
* If any component attempts to contact an external commercial endpoint during local testing or evaluation, the build fails immediately.
