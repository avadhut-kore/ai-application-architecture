# Phase 1–7: Recorded Independent Review and Accepted Baseline

## Recorded Decision and Attribution

**Reviewer-issued verdict:** Accepted with explicitly listed non-blocking limitations.

| Record | Value |
| --- | --- |
| Reviewer identified in the supplied report | Antigravity, a separate verification agent |
| Reviewed revision | `e5daf8feddca0f06499247d65109d937f8fceb82` |
| Branch at review | `codex/phase1-7-completion` |
| Review and recording date | 21 November 2026 |
| Scope | The documented Phase 1–7 baseline, comprising Tier 2 examples, Tier 3 components and supporting governance/templates |
| Prior reviewed revision | `48031c980f91e361ac7d3bf1bf0764820f221bc7` |
| Source | Review reports supplied by the repository owner in the Codex chat |

The verdict belongs to the separate reviewer. The implementing agent archives and
attributes that decision; it does not independently certify its own implementation.
Acceptance is pinned to the reviewed revision, not automatically extended to later
changes, other models, other machines or future roadmap phases. This is not formal
production certification or a claim of 100% AI accuracy.

## Preserved Reports and Provenance

- [Initial report at 48031c9](evidence/phase1-7-acceptance/antigravity-initial-48031c9.txt):
  historical context; its inaccurate descriptions are superseded by the re-review
  and the corrections below.
- [Re-review at e5daf8f](evidence/phase1-7-acceptance/antigravity-rereview-e5daf8f.txt):
  the source of the recorded scoped acceptance.
- [Provenance and hashes](evidence/phase1-7-acceptance/provenance.json): source-byte
  hashes and canonical UTF-8/LF hashes for integrity checks across operating systems.

The report wording is preserved. Newline representation and trailing ASCII
spaces/tabs are normalized in the archive; source-byte hashes identify the original
attachments and canonical hashes identify the documented normalized form. The maintainer's factual corrections are separate below; they must not be
represented as a revised or countersigned reviewer report.

The supplied reports summarize command outputs. They did not include a durable
bundle of the reviewer's raw execution logs, and the re-review says temporary timestamp
reports were deleted. Reviewer identity and execution history were not independently
authenticated by the archiving agent. These provenance/evidence limitations remain
visible rather than being filled with implementing-agent logs.

Existing [implementation evidence](phase1-7-remediation.md),
[hardening evidence](phase1-7-followup.md), and
[maintenance checks](evidence/phase1-7-followup/review-corrections.json) are separate
supporting records. They do not become independent evidence by being linked here.

## Finding Disposition Reported by the Reviewer

| Finding | Recorded disposition |
| --- | --- |
| F-01 — Standalone verifier test discovery | Resolved at the reviewed revision |
| F-02 — CPU inference latency and deadlines | Retained non-blocking operational limitation |
| F-03 — Deprecated UTC timestamps | Resolved at the reviewed revision |
| F-04 — Uncommitted beginner documentation | Resolved at the reviewed revision |

The reviewer reports 358 unit tests across nine suites and distinguishes those tests
from evaluation scenarios. It carries earlier live smoke/security results forward
rather than presenting them as newly executed full benchmarks. Consult the archived
report for its claimed commands, exclusions and exact results.

## Maintainer Corrections to Residual Reporting Errors

**Manual Evidence:** checked against source and authoritative governance while
recording the supplied review. These corrections do not modify the reviewer's verdict.

| Report statement | Repository fact and source |
| --- | --- |
| `ExecutionReceipt` is defined in `contracts/capability.py` | It is defined in [contracts/agent.py](../../building-blocks/python/contracts/agent.py). The referenced `capability.py` file does not exist. |
| Structured generation extracts a Pydantic entity | The current example uses a validated frozen dataclass in [structured_generation/models.py](../../examples/structured-generation/structured_generation/models.py), permitted by ADR-0012. |
| There are 56 telemetry-only tests | The 56 tests are the combined contracts/telemetry suite under `building-blocks/python/tests/`; they are not 56 tests exclusively for telemetry. |
| Gate I applies to Tiers 1, 2 and 3 | [QUALITY-GATES.md](../../QUALITY-GATES.md#gate-i--demo--operational-verification) lists Tiers 1 and 2. Tier 3 integration requirements may still arise under other applicable gates and engineering standards. |
| All 109 evaluation scenarios have a reproducible listed runner | The report's structured-generation count references an `eval_runner.py` that does not exist in that example directory. Treat the aggregate scenario count as unsubstantiated; independently identify datasets and their actual runners before repeating it. |
| Gate B was verified anew on both Windows and Linux | The re-review's new-command table lists Linux repository validation, not a new Linux strict-type command. Its Linux typing assertion lacks a linked new-run log. Existing implementing-agent Linux checks remain separately attributed. |

Gate applicability and phase scope continue to belong to
[QUALITY-GATES.md](../../QUALITY-GATES.md) and [ROADMAP.md](../../ROADMAP.md), not a
review report. A single local SQLite approval/checkpoint transaction is not distributed
two-phase commit; action-identified receipts are not cryptographic signatures.

## Accepted Limits and Freeze Boundary

- Local CPU inference can exceed the configured deadline. The failed run and successful
  retry remain documented in the [local execution record](phase1-7-followup.md#6-local-execution-verification).
- Full live-dataset quality at the reviewed revision is **Not Verified** by the
  independent re-review. Deterministic harness passes and live smokes do not establish it.
- Tier 2/3 examples and components are not Tier 1 production applications. Enterprise
  identity, distributed orchestration, production load acceptance and future applications
  are outside this scoped acceptance.
- The referenced implementation baseline is frozen by its Git SHA for traceability.
  This record does not lock a branch or assert that later documentation was independently
  reviewed. Phase 0 has no separate acceptance verdict in the supplied Phase 1–7 report.

## Learning Material and Transition to Phase 8

The [curriculum](../learning/README.md) and phase guides link to this baseline. The
[beginner guide](../learning/start-here.md) and current Phase 7 explanations were part
of the reviewed revision. The curriculum remains explanatory; it cannot override
requirements or confer independent acceptance.

Before Phase 8 implementation, complete the post-freeze learning-guide synchronization
review required by the [Git workflow standard](git-workflow.md#5-phase-wise-learning-guide-maintenance-rule),
record remaining guide discrepancies, and approve the new application's requirements,
benchmark and architecture decisions. This documentation pass associates the guides
with the baseline; it does not claim an exhaustive semantic audit of every guide line.

The owner has selected invoice processing with line-item tables for the
[Phase 8 planning draft](../architecture/phase-08-document-intelligence-plan.md).
The draft is a reviewable proposal, not an implemented capability or an accepted
Tier 1 application. Preserve the accepted baseline while developing any separately
approved implementation.
