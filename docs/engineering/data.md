# Data Architecture, Persistence & Provenance Standards

This document establishes the persistence boundaries, schema evolution rules, multi-tenant partitioning, and AI data provenance standards across the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Data standards defined in this document satisfy [`Gate A (Architecture & Structural Boundaries)`](../../QUALITY-GATES.md#gate-a--architecture--structural-boundaries) and [`Gate E (Security & Safety)`](../../QUALITY-GATES.md#gate-e--security--safety) in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). In enterprise AI, preserving data integrity, auditability, and provenance is critical when mixing human-authored data with probabilistic model generations.

---

## 1. Domain Entities vs. Persistence Models

To maintain high decoupling and prevent database concerns from contaminating business rules, applications must separate domain entities from database models:

```
┌──────────────────────────────────────┐
│            Domain Layer              │
│  • Pure business invariants          │
│  • Immutable value objects           │
│  • Zero database annotations/imports │
└──────────────────┬───────────────────┘
                   │
                   ▼ (Mapping via Mapper/Translator)
┌──────────────────────────────────────┐
│         Infrastructure Layer         │
│  • EF Core Entity / SQLAlchemy Model │
│  • Foreign keys, indexes, table maps │
│  • Migration scripts & drivers       │
└──────────────────────────────────────┘
```

* **No Leaky Abstractions**:
  * Domain logic must never depend directly on ORM attributes (`@Table`, `[Key]`, `ForeignKey`).
  * Repositories accept and return domain entities or immutable DTOs, translating internally to/from database models.

---

## 2. Versioned Schema Migrations

Database structures must evolve deterministically using version-controlled migration scripts:

| Ecosystem | Migration Tool | Storage Path | Enforcement Policy |
| :--- | :--- | :--- | :--- |
| **Python** | Alembic | `alembic/versions/*.py` | Pinned revision tree; migration dry-run in CI. |
| **.NET** | EF Core Migrations | `src/Infrastructure/Migrations/*.cs` | Compiled C# migrations; zero manual DB tampering. |
| **Java** | Flyway / Liquibase | `src/main/resources/db/migration/V*.sql` | Checksum validation on boot. |

### Operational Migration Rules
1. **Zero Runtime Auto-Sync in Production**:
   * Tools must never use `AutoMigrate()`, `EnsureCreated()`, or `hibernate.ddl-auto=update` in production environments.
   * Schema updates are applied as an explicit, auditable step during deployment pipelines.
2. **Backwards-Compatible Schema Changes**:
   * Implement migrations following the Expand-Contract pattern (add new column as nullable, backfill data, switch application code, drop old column in subsequent release).

---

## 3. Tenant Data Partitioning & Isolation

When implementing multi-tenant RAG, memory stores, or knowledge repositories, strict data isolation is mandatory:

* **Logical Partitioning via Metadata Filtering**:
  * In shared vector databases (e.g., Qdrant, Chroma, pgvector), every vector embedding must include an indexed `tenant_id` payload attribute.
  * Retrieval queries must enforce mandatory, non-bypassable tenant filter predicates (`filter={"tenant_id": current_tenant}`).
* **Row-Level Security (RLS)**:
  * In relational stores (PostgreSQL), enable Row-Level Security policies tied to session tenant contexts to guarantee database-enforced isolation.
* **Storage Encryption**:
  * All sensitive customer documents and embeddings must be encrypted at rest and in transit.

---

## 4. AI-Generated Data Provenance & Lineage Tracking

When probabilistic models generate classifications, summaries, extracted entities, or synthetic documents, downstream systems must know their provenance:

### Mandatory Lineage Metadata Attributes
Every database record generated or modified by an AI model must capture the following provenance audit columns:

```json
{
  "source_document_id": "doc-78129-rev3",
  "generated_by_model": "llama3.2:3b",
  "model_version_tag": "latest-2026",
  "prompt_template_id": "prompt-extract-v2.1",
  "prompt_hash_sha256": "8f4e2b...",
  "inference_temperature": 0.0,
  "confidence_score": 0.94,
  "is_synthetic": true,
  "human_reviewed": false,
  "created_at_utc": "2026-09-14T12:00:00Z"
}
```

* **Auditability**: Prevents model "drift" from silently polluting training datasets or financial records.
* **Explainability**: Allows human reviewers to trace any extracted attribute directly back to the source text and specific prompt version that produced it.
