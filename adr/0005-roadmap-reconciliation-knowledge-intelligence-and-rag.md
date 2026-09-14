# ADR-0005: Roadmap Reconciliation for Knowledge Intelligence & RAG

* **Status**: Accepted
* **Deciders**: Principal AI Application Architect, Enterprise Governance Auditor, RAG Engineer, Search/Retrieval Engineer
* **Date**: 2026-09-14
* **Technical Story**: Phase 5.1 — RAG Evidence, Structured Output & Governance Remediation ([`ROADMAP.md`](../ROADMAP.md#phase-5-knowledge-intelligence--rag))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

During initial Phase 0 repository governance drafting, the roadmap entry for Phase 5 ([`ROADMAP.md`](../ROADMAP.md#phase-5-knowledge-intelligence--rag)) was sketched with a speculative, checklist-driven scope:
* A Tier 1 Enterprise RAG reference application;
* Dense vector search combined with BM25 sparse keyword search;
* Reciprocal Rank Fusion (RRF);
* Grounded citation extraction and automated evaluation.

During Phase 5 implementation, architectural analysis and repository principles ([`docs/architecture/principles.md`](../docs/architecture/principles.md) — *Principle 4: Architecture Complexity Rule* and *Principle 12: Knowledge Grounding & Citation Integrity*) established that adding lexical search (BM25) and score fusion (RRF) before establishing and measuring a clean dense semantic retrieval baseline violates evidence-driven engineering. Consequently, [`ADR-0004`](0004-knowledge-intelligence-and-rag-architecture.md) formally established a **baseline-first retrieval policy**:
1. Build a modular, decoupled Tier 2 Pattern Example (`examples/rag`) establishing provider-neutral embeddings, structural chunking, vector indexing, context budgeting, grounded generation, and application-level citation validation;
2. Build a Tier 3 Platform Component (`platform/ollama-embedding-adapter`) providing the standard-library HTTP adapter for local embedding models;
3. Measure baseline retrieval and generation metrics across 32 ground-truth evaluation scenarios;
4. Formally defer BM25, RRF, cross-encoder rerankers, and persistent vector databases until concrete benchmark failure modes justify their added operational and computational complexity.

An independent architectural audit identified a governance discrepancy: `ROADMAP.md` still contained the early pre-implementation wording requiring Tier 1, BM25, and RRF as mandatory Phase 5 deliverables.

---

## 2. Problem Statement

How should the repository resolve the mismatch between early roadmap expectations and the accepted baseline-first architecture without lowering long-term architectural ambition or silently mutating frozen governance?

---

## 3. Decision Drivers

* **Evidence-Driven Engineering**: AI architecture must introduce complexity (e.g., hybrid search, rerankers, multi-index fusion) only when empirical evaluation demonstrates that simpler baselines fail.
* **Governance Traceability**: Frozen roadmap governance must not be changed silently; all modifications must be authorized by an explicit Architecture Decision Record.
* **Tier Distinction**: Reference implementations must be categorized accurately by tier according to their operational scope and evidence burden (Tier 2 Pattern Example vs. Tier 1 Production Reference Application), not by prestige.
* **Preservation of Long-Term Enterprise Ambition**: Reconciling Phase 5 must not discard advanced enterprise RAG capabilities (hybrid retrieval, RRF, persistent vector DBs); it must establish a clear progression path for their introduction.

---

## 4. Key Architectural Decisions

### 4.1 Formal Roadmap Reconciliation
We formally update the Phase 5 roadmap definition in [`ROADMAP.md`](../ROADMAP.md#phase-5-knowledge-intelligence--rag) to reflect the baseline-first architectural strategy:
* **Phase 5 Core Deliverable**: A modular Tier 2 Pattern Example (`examples/rag`) and Tier 3 Platform Component (`platform/ollama-embedding-adapter`) establishing:
  * Ingestion, frontmatter parsing, and heading-aware structural chunking;
  * Provider-neutral `EmbeddingPort` and local Ollama embedding adapter;
  * In-memory cosine vector index with metadata filtering and deterministic tie-breaking;
  * Decoupled semantic retrieval with evidence-sufficiency threshold policy;
  * Context budget management with untrusted delimiter framing;
  * Grounded generation consuming the frozen Phase 4 `TextGenerationPort`;
  * Application-layer citation validation and anti-spoofing defense;
  * Voluntary reference RAG evaluation harness and versioned 32-scenario dataset.

### 4.2 Decision-Gated Progression for Advanced Retrieval
Advanced knowledge intelligence capabilities are formally scheduled as decision-gated enhancements, to be introduced when specific empirical triggers are met:

```text
Foundational Reference Pattern (Phase 5 Baseline)
  [Dense Semantic Retrieval + In-Memory Index + Citation Validation]
                        │
                        ▼ (Evaluation Benchmark Measurement)
   ┌────────────────────┴────────────────────┐
   │                                         │
   ▼ (Trigger: Lexical Disambiguation Defect)▼ (Trigger: Scale / Persistence Defect)
Decision Gate: Hybrid Search              Decision Gate: Persistent Vector DB
  [BM25 Sparse Search + RRF Fusion]         [pgvector / Qdrant / Milvus Engine]
   │                                         │
   └────────────────────┬────────────────────┘
                        │
                        ▼ (Trigger: Large-Scale Corpus Inversion)
             Decision Gate: Reranking
               [Cross-Encoder Reranker]
                        │
                        ▼
       Tier 1 Enterprise Knowledge Application
```

* **Hybrid Search (BM25 + RRF)**: Triggered when dense embeddings demonstrably fail on exact token lookups (e.g., part numbers, specific error codes, unique alphanumeric identifiers).
* **Persistent Vector Database**: Triggered when corpus volume exceeds memory bounds ($> 100,000$ chunks) or requires cross-process persistence and concurrent updates.
* **Cross-Encoder Reranking**: Triggered when retrieval ranking inversions on large candidate sets reduce top-$K$ relevance below target thresholds.
* **Tier 1 Enterprise Knowledge Application**: An end-to-end, multi-service enterprise knowledge application packaging hybrid search, persistent vector storage, and background ingestion workers.

---

## 5. Architectural Consequences

### Positive
* **Governance Consistency**: Eliminates contradiction between [`ROADMAP.md`](../ROADMAP.md) and [`adr/0004-knowledge-intelligence-and-rag-architecture.md`](0004-knowledge-intelligence-and-rag-architecture.md).
* **Defensible Simplicity**: Prevents premature optimization and dependency bloat in early roadmap phases.
* **Clear Evolution Path**: Future contributors have an explicit, trigger-based roadmap for implementing hybrid search, RRF, and persistent vector databases.

### Negative
* **Two-Stage Delivery**: Full Tier 1 enterprise knowledge application capabilities are decoupled from the initial baseline pattern example.

---

## 6. References

* [`ROADMAP.md`](../ROADMAP.md) — Phase 5 Roadmap Definition
* [`adr/0004-knowledge-intelligence-and-rag-architecture.md`](0004-knowledge-intelligence-and-rag-architecture.md) — Baseline-First RAG Architecture
* [`QUALITY-GATES.md`](../QUALITY-GATES.md) — Tier Applicability Governance
* [`docs/architecture/principles.md`](../docs/architecture/principles.md) — Principle 4 (Complexity Rule) & Principle 12 (Knowledge Grounding)
