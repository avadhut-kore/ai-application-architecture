# Phase 8 Planning Draft: Invoice Document Intelligence

## 1. Status, Authority and Business Problem

**Status: requirements and architecture proposal; not approved for implementation.**
The repository owner selected **invoices with line-item tables** in the current
planning conversation. The detailed scope, limits, technology choices and acceptance
protocol below still require architectural review. No application, dependency,
model download, dataset or speculative interface is introduced by this document.

[ROADMAP.md](../../ROADMAP.md#phase-8-document-intelligence) owns Phase 8 scope and
its extraction-accuracy exit criterion. [QUALITY-GATES.md](../../QUALITY-GATES.md)
owns the applicable gates and thresholds. This proposal elaborates one concrete
use case; it does not amend either authority. The prior baseline is recorded in the
[Phase 1–7 acceptance record](../engineering/phase1-7-acceptance.md).

An operations engineer should be able to submit an invoice, inspect extracted header
fields and line-item tables beside their source evidence, correct uncertain values,
and export an explicitly reviewed structured result. The application demonstrates
document layout, OCR, provenance, deterministic validation and durable human review.
It does not pay an invoice, certify tax compliance or write to an ERP.

### Proposed Reference Scope

- **Artifact:** a Tier 1 reference application, proposed location `apps/invoice-intelligence/`.
- **Runtime:** Python modular monolith, local document/OCR worker, local model adapter,
  protected document files and SQLite metadata. One local Compose deployment.
- **Users:** submitting operator, authenticated reviewer and administrator, with distinct
  authorization rules. Caller-supplied role strings never grant authority.
- **Inputs:** printed English invoices as native-text PDFs, scanned PDFs, PNG or JPEG.
  Multi-page and continued line-item tables are required within approved input limits.
- **Initial currency proposal:** explicitly identified USD and INR amounts with a
  versioned two-decimal rounding policy. Other currencies, ambiguous separators and
  unsupported layouts require an explicit unsupported/review outcome, not inference.
- **Outputs:** versioned JSON with extracted values, source evidence, validation flags,
  review status and audit identity. Original candidate extraction remains inspectable.

Handwriting, general contract/form extraction, arbitrary remote URL ingestion, payment
execution, ERP posting, shared gateways, multi-agent collaboration and general
vision-language applications are deferred. Document-specific OCR/layout work belongs
to Phase 8; the broader Phase 9 application is not pulled into this scope.

## 2. Proposed Functional Requirements

| ID | Requirement | Acceptance evidence to produce |
| --- | --- | --- |
| FR-01 | Accept authenticated local uploads with size, page, pixel, format and content checks. Reject unsafe, corrupt, encrypted or unsupported documents with a typed reason. Do not follow links, embedded scripts, attachments or QR-code URLs. | Valid/invalid upload and parser isolation tests, including spoofed file extensions and resource-exhaustion inputs. |
| FR-02 | Assign an immutable document identity, digest and owner; persist a bounded processing job. Repeated submissions must not silently duplicate review/export side effects. | Duplicate/concurrent submission and ownership tests with persisted records. |
| FR-03 | Read text and layout from native PDFs; run genuine local OCR on scanned/image pages. Record page number, region coordinates, rotation/coordinate transform and extraction method. | Live extraction on native and scanned documents; page/region evidence checked against original files. |
| FR-04 | Extract invoice identifier/date, seller/buyer, currency, declared subtotal/tax/total and line-item description, quantity, unit price and declared line total. Preserve leading zeros in identifiers and missing values explicitly. | Independently annotated field and table fixtures; missing/ambiguous values do not become invented values. |
| FR-05 | Preserve table row/cell identity across pages, including repeated headers and continued rows. Each populated field/cell links to source page/region/text evidence. | Multi-page table tests and field/cell provenance coverage. A correct number attached to the wrong row is incorrect. |
| FR-06 | Validate model output strictly at the boundary, with bounded fields, arrays and nesting. Reject duplicate/conflicting fields and unsupported values; allow at most the approved bounded repair attempt. | Schema/adversarial tests and raw candidate versus validated-result separation. |
| FR-07 | Use deterministic decimal arithmetic for consistency checks. Compare extracted declared amounts under the approved rounding policy; never ask a model to authorize a payment or decide tax law. | Decimal, rounding, subtotal/line mismatch and currency tests. Discrepancies remain visible rather than being silently repaired. |
| FR-08 | Flag low/unknown OCR quality, ambiguous layout, missing evidence, arithmetic mismatches and schema failures for review. OCR confidence and model self-reported confidence are distinct; self-scores cannot authorize approval. | Calibrated confidence/abstention checks and failure routing tests. An uncalibrated score is labeled as such. |
| FR-09 | Require an authenticated reviewer to approve or reject every exported result. Show field values and source evidence; record corrections without overwriting the original candidate. | Role, ownership, revocation, stale-version, approval/rejection and audit tests. High confidence does not bypass human review. |
| FR-10 | Commit the decision against the exact document/result version. Export only the approved version and identify the approving principal, source digest and schema/model/parser versions. | Atomic decision/version conflict, replay and export authorization tests. |
| FR-11 | Recover interrupted jobs without inventing completed extraction or approval. Bound retries and cancel/terminate unresponsive document workers. | Real process-restart, timeout, cancellation, crash and unavailable-model tests. |
| FR-12 | Provide a local API and documented review/demo client with job status, evidence inspection, review and JSON export. Expose health/readiness and privacy-preserving telemetry. | End-to-end local journey, API contract, authentication and exporter/privacy checks. |

## 3. Non-Functional Requirements and Proposed Bounds

These are design constraints to review, not measurements or promises already met.

| ID | Constraint | Proposed target and verification |
| --- | --- | --- |
| NFR-01 | Local operation | After explicit dependency/model installation, extraction and review run without paid API keys or document egress. Block unexpected outbound network access in document workers and integration-test that boundary. |
| NFR-02 | Input/processing bounds | Start with 20 MiB/upload, 20 pages/document, 10 megapixels/rendered page, 500 line items/document and one active extraction job per reference instance. Validate before allocation where possible; malformed-file workers also require OS-level CPU/memory limits. Tune only through a documented profile and rerun the benchmark. |
| NFR-03 | Authorization and privacy | Zero successful cross-owner access or unauthorized review/export in the security suite. No raw invoice text, bank details, prompts or model completions in telemetry. Use protected local storage and an explicit retention/deletion policy. |
| NFR-04 | Correctness | Phase 8's extraction target and all applicable Tier 1 gates remain binding. Section 5 defines a proposed reproducible scoring contract; do not report a successful human-corrected export as model extraction accuracy. |
| NFR-05 | Performance | Demonstrate Gate G on named hardware, including its TTFT, streaming and memory-stability requirements. The existing CPU profile is not assumed to meet them. Choose/document the OCR/job latency and memory SLOs from feasibility measurements before implementation approval. |
| NFR-06 | Durability | Zero duplicate approval/export effects and zero invented approvals in restart/concurrent-review tests. Original source and candidate are immutable; corrected results have explicit versions. |
| NFR-07 | Verification | Strict typing/linting, applicable coverage floors, container integration, dependency/image scans and all other Tier 1 gates must pass with retained evidence. Current planning has no PASS claim. |
| NFR-08 | Portability and reproducibility | Define supported Windows host/Docker Linux operation, pinned dependencies/images/models and document hashes. Retain actual commands, timestamps, hardware, failures and outcomes. Put workstation Docker/model data on D: under the existing setup. |

Timeouts, prompt/output budgets, worker RSS/CPU limits, supported scan quality and
job latency SLOs are unresolved profile decisions. They must be numeric and approved
before implementation acceptance; they are not silently inherited from a Tier 2 demo.

## 4. Proposed Architecture and Trust Boundaries

### Processing Flow

```text
Authenticated upload
  -> bounded file validation and immutable source storage
  -> persisted job and isolated native-text/OCR/layout processing
  -> bounded text/region evidence and table candidates
  -> local model proposes typed invoice fields when needed
  -> strict schema, provenance and decimal consistency checks
  -> durable human review of candidate/corrections/source evidence
  -> approve or reject the exact result version
  -> authorized JSON export of the approved version
```

Malformed inputs become `REJECTED_INPUT`; infrastructure/parser failures become
`PROCESSING_FAILED`. Valid but uncertain extraction becomes `NEEDS_REVIEW`; validated
candidates become `READY_FOR_REVIEW`. Neither review state permits export. Only an
explicit authorized transition produces `APPROVED`; `REJECTED` cannot be exported.
These are proposed application statuses, not additions to shared contracts yet.

### Component Responsibilities

| Component | Responsibility and boundary |
| --- | --- |
| Inbound API/review client | Authentication, request bounds, ownership and escaped evidence presentation. No business authority in caller-provided roles or model text. |
| Application use cases | Job lifecycle, bounded processing, review/version conflicts and export policy. Framework-independent orchestration. |
| Domain model | Invoice fields, decimal consistency, evidence references, review decisions and immutable result versions. No model SDK or database imports. |
| Document/OCR/layout adapters | Real local extraction and coordinate mapping in an isolated worker. Treat file structure, OCR text and metadata as untrusted. |
| Model adapter | Proposed reuse of existing provider-neutral generation contracts and local platform adapter; no inference emulation or cloud-key requirement. |
| Persistence/source storage | SQLite transactions for job/review state plus protected source files. Explicit recovery for file/database partial failure; a local transaction is not distributed 2PC. |
| Telemetry | Correlated stages, model/parser versions, resource counts, timing and status without raw document content. |

Reuse supported packages from `building-blocks/` and `platform/`. Do not import
application/domain code from `examples/agentic-workflow` or another application.
Use its reviewed patterns as design evidence; introduce only the app-owned ports and
adapters justified by the approved requirements. No generic document framework,
broker, vector database or model gateway is needed for this first use case.

The current Qwen reference profile is text generation, not an OCR implementation.
A scanned invoice therefore requires a real local OCR/layout path. Parser/OCR/model
selections need license, security, layout/provenance, resource and accuracy evidence;
they are not decided by copying a model name from an earlier phase.

The current shared generation contract returns a completed response. Tier 1 streaming
and performance cannot be claimed from that alone. The architecture review must decide
whether a concrete streaming adapter/contract is required and how to avoid treating
partial, unvalidated model output as an approved result. No speculative interface is
created in this planning task.

### Security and Failure Analysis to Complete

Threat-model parser exploits/decompression bombs, malicious document instructions,
SSRF via embedded links, path traversal, forged evidence coordinates, bank/PII leakage,
cross-owner reads, reviewer spoofing, stale approval, duplicate export and poisoned
benchmark data. Isolate untrusted parsing, use parameterized storage, reauthorize
review/export, and bind approval to source/result versions.

Choose a genuine local authentication adapter and secret provisioning strategy;
test invalid, expired and revoked identities. External enterprise identity integration
may remain a separately documented deployment option, but authenticated local review
is required. A role supplied on a request or a static demonstration identity is not
proof of authentication.

## 5. Benchmark and Extraction-Accuracy Contract

The [roadmap's extraction target](../../ROADMAP.md#phase-8-document-intelligence)
must be evaluated before human correction on a fixed, versioned corpus. Approve the
metric definition and dataset before tuning the pipeline; do not reinterpret the
target after observing results.

### Proposed Dataset

Propose 100 owned/licensed documents: 25 development documents, 60 held-out valid
invoices and 15 held-out invalid/adversarial cases. Keep document families and derived
scans together when splitting; hold out some layout families entirely. Report results
by native/scanned, single/multi-page, table complexity and degradation category.

Include repeated table headers, row continuation, long descriptions, missing fields,
ambiguous dates/currency, inconsistent totals, rotated/noisy scans, corrupt/encrypted
inputs and embedded prompt-injection attempts. The invalid/adversarial cases do not
inflate extraction accuracy by being counted as easy abstentions.

No real customer invoices or private identifiers enter Git. Any authored synthetic
fixtures must be explicitly labeled, architecturally reviewed and human-annotated
before commitment, in accordance with the
[evaluation standard](../engineering/ai-evaluation.md). Gold values, row/cell alignment
and evidence regions need a separate human review; model-generated answers are not
their own ground truth. Synthetic-only benchmark results have an explicit external
validity limit and cannot certify arbitrary production invoices.

### Proposed Scoring Rules

- Normalize only documented representation differences: whitespace, explicit date
  formats and exact decimal representation under the chosen currency policy. Do not
  remove identifier leading zeros or repair an incorrect amount to match the label.
- Score each header field and each table cell against its gold identity. A value in
  the wrong row/page is wrong. Missing, incorrect and unmatched extra values must
  reduce the score; duplicates cannot add credit.
- Define score as `correct gold slots / (gold slots + unmatched extra populated slots)`.
  Report populated-field accuracy separately from expected-null accuracy. The proposed
  release target is at least 95% on populated header fields and on line-item cells,
  as well as the declared overall extraction score. Freeze the slot/alignment rules
  before running the holdout set.
- Report document exact-match rate, table precision/recall, OCR error rates, evidence
  coverage, uncertainty/review rate and pre/post-human results separately. They are
  distinct metrics, not interchangeable names for accuracy.
- Route uncertainty to review without removing that document from the valid-input
  denominator. No oracle answers, silent exclusions or human correction may improve
  the pre-review score. Keep all failed cases and per-stratum results.
- Score invalid-input rejection and adversarial safety separately. No injection or
  model self-score may bypass required review or produce an unauthorized export.

Gate D's scenario minimum, schema adherence, faithfulness and context relevance still
apply to this Tier 1 AI application. Define invoice evidence-support and supplied-region
relevance scoring with independently checked labels. If no retrieval component is used,
resolve the exact applicability/method with the gate owner before implementation; do
not silently mark a mandatory Tier 1 criterion N/A or substitute the 95% metric for it.

## 6. Gate Evidence and Release Conditions

All Gates A–J apply to the proposed Tier 1 application. None is satisfied by this plan.

| Gate | Evidence required from the future implementation |
| --- | --- |
| A | Approved architecture/ADRs and dependency-boundary checks. |
| B | Strict language typing/linting and validated public/document/model boundaries. |
| C | Required coverage, deterministic boundary tests, real local container/parser/model integration and restart/concurrency tests. |
| D | Fixed held-out live evaluation, approved ground truth/scoring, model/parser digests and full failure analysis; harness tests kept separate. |
| E | Threat model, secret/privacy/auth checks, parser isolation, licensed inputs/dependencies and zero prohibited dependency/image vulnerabilities. |
| F | Actual exported spans/metrics with required semantic attributes, correlation and tested document/PII redaction. |
| G | Named-hardware performance, streaming and memory-stability evidence under the authoritative thresholds. Current CPU examples are not proof. |
| H | Requirements, architecture, API/runbook, ADRs, renderable diagrams, trade-offs and executable documentation checks. |
| I | Reproducible local boot and timed upload → review → export demo using real inference and no paid API key. |
| J | Provider/worker deadlines, bounded transient retries, circuit behavior, graceful failure, health/readiness and fault-injection evidence. |

## 7. Delivery Sequence and Approval Decisions

| Step | Deliverable | Dependency / completion condition |
| --- | --- | --- |
| P8-0 | Reviewed requirements, currency/input/resource profile and baseline learning-guide synchronization | Owner reviews this proposal and accepted-baseline limitations; no application implementation yet. |
| P8-1 | Architecture decisions and bounded feasibility evidence | Select licensed native-PDF/OCR/layout/model/auth components; establish hardware/streaming feasibility and measurable SLOs without relaxing gates. Any executable spike is separately reviewed within the approved scope. |
| P8-2 | Approved benchmark and scoring specification | Independently reviewed gold labels, provenance, fixed splits and declared metrics before tuning. |
| P8-3 | Concrete app contracts, adapters and deterministic validation | Create the isolated app only after governance/requirements/architecture review; actual local extraction, not inference simulation. |
| P8-4 | Authenticated durable review/export journey | Version binding, recovery, ownership and fail-closed behavior verified against local storage. |
| P8-5 | All-gate verification and independent acceptance | Retain raw logs/reports, all benchmark outcomes, security/performance evidence and a fresh review tied to the final revision. |
| P8-6 | Accepted implementation learning guide | Derive runnable learning material from accepted code before progression to Phase 9. |

Open decisions: supported invoice profile and limits; OCR/layout selection and licensing;
model/digest choice; authentication and retention; evidence coordinates; confidence
calibration; exact benchmark/scoring; hardware, streaming, deadlines and latency SLOs.
Approval of the invoice use case alone does not settle these architecture decisions.

## 8. Planning Verification and Next Action

**Manual Evidence:** this proposal is derived from the roadmap, application template,
architecture principles, local-first policy and relevant engineering standards. It
also identifies reuse limits from current contracts and Phase 1–7 evidence.

**Not Verified:** no OCR/parser/model feasibility, extraction accuracy, performance,
security or runtime capability is asserted here. No application or test dataset exists
as a result of this plan. Documentation links and structure are checked separately.

Next, review P8-0/P8-1 decisions and the proposed scoring contract. Resolve measurable
resource/SLO and Tier 1 feasibility questions before authorizing implementation.
