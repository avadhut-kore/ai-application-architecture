# ADR-0004: Knowledge Intelligence & RAG Architecture

* **Status**: Proposed (Pending Independent Codex Audit)
* **Deciders**: Principal AI Application Architect, RAG Engineer, Search/Retrieval Engineer, AI Evaluation Engineer, Security Architect, Senior Python Engineer
* **Date**: 2026-09-14
* **Technical Story**: Phase 5 — Knowledge Intelligence & RAG ([`ROADMAP.md`](../ROADMAP.md#phase-5-knowledge-intelligence--rag))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

Following the completion and freezing of Phase 4 (AI Foundations), which established the provider-neutral `TextGenerationPort`, the concrete local `OllamaAdapter`, structured output validation, and the initial Gate D evaluation harness, Phase 5 addresses the first knowledge-grounded AI capability in the repository.

In enterprise environments, AI applications cannot rely solely on the parametric knowledge embedded in foundation model weights. They must reliably access, retrieve, and synthesize information from private corporate documents while:
1. Proving that retrieval works independently of generation;
2. Enforcing strict security boundaries against document-based prompt injection attacks;
3. Validating that source citations are authentic and traceable rather than hallucinated by language models;
4. Reporting explicit insufficient evidence when domain documents lack required facts.

---

## 2. Problem Statement

How should the repository establish a provider-neutral, evaluation-driven Knowledge Intelligence and RAG reference architecture while:
1. Introducing the minimal provider-neutral embedding boundary deferred from Phase 2 without mixing text generation and embedding concerns;
2. Implementing a clean local embedding adapter without downloading models in CI or runtime startup;
3. Storing and searching vector representations deterministically without premature vector database infrastructure;
4. Ensuring that retrieved evidence is treated as untrusted input;
5. Validating source attribution at the application layer to eliminate citation spoofing;
6. Establishing objective retrieval and generation baselines before considering advanced techniques (reranking, hybrid BM25 search, GraphRAG)?

---

## 3. Decision Drivers

* **Separation of Capabilities**: Keep dense vector embedding (`EmbeddingPort`) strictly separated from text generation (`TextGenerationPort`).
* **Retrieval Independence**: The system must allow retrieval accuracy (Hit Rate, Recall@K, MRR, Context Relevance) to be measured without invoking language models.
* **Untrusted Evidence Boundary**: Retrieved documents may contain malicious or conflicting instructions; prompts must frame evidence with strict delimiters.
* **Application-Controlled Citations**: Source citations must be validated by the application against retrieved chunk metadata, preventing model hallucination.
* **Minimal Infrastructure & Zero Framework Coupling**: Avoid bringing in heavy, rapidly mutating frameworks (LangChain, LlamaIndex, Haystack) or external database containers (pgvector, Qdrant, Milvus) before concrete architectural necessity justifies them.
* **Hermetic Local & CI Execution**: CI and developer workstations must run all tests and evaluation suites deterministically in $< 1$s without cloud keys or background daemons.

---

## 4. Key Architectural Decisions

### 4.1 Minimal Provider-Neutral Embedding Boundary (`EmbeddingPort`)
We introduce a dedicated outbound port `EmbeddingPort` in `building-blocks/python/contracts/ports.py` and supporting request/response models in `contracts/models.py`. Dense vector embedding is modeled as a distinct capability from text generation to prevent interface pollution.

### 4.2 Local Embedding Platform Adapter (`OllamaEmbeddingAdapter`)
We implement `OllamaEmbeddingAdapter` as a Tier 3 platform component in `platform/ollama-embedding-adapter/`. It interfaces with Ollama's HTTP API (`/api/embed` with fallback to `/api/embeddings`) using standard library HTTP client primitives (`urllib.request` + `asyncio.to_thread`) with bounded retries on transient errors. Model downloads (`ollama pull`) are strictly prohibited in code and automated scripts, remaining an explicit developer action.

### 4.3 In-Memory Deterministic Vector Index (`InMemoryVectorIndex`)
Rather than provisioning external database infrastructure (pgvector, Qdrant, Pinecone), we implement a pure Python, in-memory vector index behind a `VectorIndexPort` protocol. It implements exact cosine similarity with zero-norm protection, deterministic tie-breaking (`-score, chunk_id`), and metadata filtering. This guarantees hermetic CI execution and total algorithmic transparency.

### 4.4 Deterministic Heading-Aware Chunking & Stable Identifiers
We implement `HeadingAwareChunker`, which decomposes markdown documents along heading hierarchy boundaries while respecting a configurable character budget (default: 1000 chars). Chunks receive deterministic identifiers (`{document_id}#c{chunk_index}`) and inherit source document metadata, guaranteeing reproducibility across evaluation runs.

### 4.5 Application-Level Citation Validation & Anti-Spoofing Defense
We establish `CitationValidator` in the application domain. The model outputs cited source identifiers inside a structured JSON schema. The application validates each citation ID against the set of chunks actually returned during retrieval. Any hallucinated citation is rejected, and verified citations are enriched with authoritative document titles and source URIs.

### 4.6 Untrusted Evidence Prompt Construction
`ContextBuilder` wraps retrieved chunks inside explicit security boundary delimiters:
```text
=== BEGIN RETRIEVED EVIDENCE (UNTRUSTED DATA) ===
...
=== END RETRIEVED EVIDENCE ===
```
The system prompt explicitly commands the model to treat evidence text strictly as informational data and never execute instructions found within it.

---

## 5. Deliberately Deferred Capabilities (Baseline-First Policy)

In accordance with repository governance, we establish measurable baselines before introducing advanced retrieval complexity:

| Capability | Decision | Rationale | Re-evaluation Trigger |
| :--- | :--- | :--- | :--- |
| **Reranking Models** | DEFERRED | Baseline semantic retrieval achieves 100% Hit Rate and 0.938 MRR on the reference corpus. Adding a cross-encoder introduces substantial latency without measured benefit. | Retrieval benchmark drops below 85% Hit Rate due to ranking inversion on larger corpora. |
| **Hybrid Search (BM25 + Dense)** | DEFERRED | Dense embeddings successfully disambiguate test scenarios. Hybrid search adds inverted index dependencies. | Documented failure of dense retrieval on exact keyword queries, product SKUs, or specialized acronyms. |
| **GraphRAG / Knowledge Graphs** | DEFERRED | Entity graph extraction and graph traversal add massive LLM pre-processing costs out of core Phase 5 scope. | Complex multi-hop relational reasoning requirements across disconnected documents. |
| **Persistent Vector Database** | DEFERRED | In-memory index satisfies all Phase 5 CI and demo requirements without Docker or external services. Storage is decoupled via `VectorIndexPort`. | Corpus size exceeds memory budget ($> 100,000$ chunks) or requires multi-process persistence. |
| **Query Rewriting / Expansion** | DEFERRED | Standard queries embed effectively without expansion. Multi-query rewriting multiplies LLM latency and cost. | Measured retrieval failure on complex, multi-faceted user prompts. |

---

## 6. Architectural Consequences

### Positive
* **Provable Boundaries**: Retrieval quality is measured independently of generation quality.
* **Deterministic Hermetic CI**: All 31 unit tests and 32 evaluation scenarios execute in $< 0.1$s without network or daemon dependencies.
* **Citation Integrity**: Eliminates LLM citation hallucination by validating citations against retrieval metadata.
* **Zero Vendor Lock-In**: Both embedding and generation rely on provider-neutral ports (`EmbeddingPort`, `TextGenerationPort`).

### Negative
* **In-Memory Volatility**: The vector index is rebuilt in-memory on application startup; large datasets require future persistent indexing.
* **Linear Scan at Scale**: Exact cosine similarity against in-memory lists is $O(N)$, which is optimal for small reference corpora but requires approximate nearest neighbor (ANN) indexes at massive scale.

---

## 7. References

* [`docs/architecture/principles.md`](../docs/architecture/principles.md) — Architecture Complexity Rule & Untrusted Model Output Principle
* [`docs/architecture/local-first.md`](../docs/architecture/local-first.md) — Local-First Execution Policy
* [`QUALITY-GATES.md`](../QUALITY-GATES.md) — Gate D (AI Evaluation) & Gate A (Boundaries)
* [`examples/rag/eval_runner.py`](../examples/rag/eval_runner.py) — Gate D Automated Evaluation Runner
