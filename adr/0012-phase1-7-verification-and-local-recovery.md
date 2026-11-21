# ADR-0012: Verify the Phase 1–7 baseline and recover local workflows safely

* **Status**: Accepted for implementation scope; independent acceptance pending
* **Decider**: Repository owner, explicit approval in the Codex chat on 2026-11-20
* **Date**: 2026-11-20
* **Amends**: ADR-0003, ADR-0009, ADR-0010 and ADR-0011 where described below

## Context and decision drivers

The owner approved remediation of Phases 1–7 using the Tier 2 single-agent
workflow baseline from ADR-0009. The earlier roadmap still described a Tier 1
multi-agent application. Review also reproduced approval bypass, volatile domain
outcomes, inaccessible crash recovery, evaluator false positives and citations
outside supplied context. Offline test doubles cannot establish real model quality.

## Decision

1. Reconcile Phase 7 in the authoritative [roadmap](../ROADMAP.md). This does not
   declare implementation independently accepted or introduce Phase 8 capabilities.
2. Preserve dependency-free contracts. Runtime instrumentation lives separately in
   `building-blocks/python/ai_telemetry`, using pinned OpenTelemetry dependencies.
   Root `pyproject.toml` and `uv.lock` define the active Python development/runtime
   environment; the contracts package can still be consumed without telemetry.
3. Typed dataclasses and explicit strict boundary validation remain permitted for
   the existing standard-library patterns. Schema validation must reject wrong
   types, unknown fields and invented values. Pydantic remains the default for new
   application boundaries; using dataclasses does not waive validation or typing.
   Existing Tier 2/3 `unittest` suites and flat colocated `tests/` directories remain
   supported. New applications follow the pytest/layout default; existing fixtures
   must satisfy isolation, assertion and coverage requirements. Strict typing
   evidence covers runtime code and tooling, and does not claim typed test fixtures.
4. Real runtime demos default to local model inference. Scripted behavior is
   restricted to named test-support modules or explicitly requested deterministic
   verification harnesses. A harness reports its mode and cannot certify AI quality.
   Provider-native schemas constrain registered tool arguments and structured final
   proposals. The last reasoning step is reserved for real model synthesis; it
   does not inject a canned conclusion. Application validation and approval remain
   authoritative even when a provider enforces the requested output schema.
5. SQLite domain transactions persist the business effect and action identity
   together. A repeated key must match the original operation. Workflow checkpoint
   and domain receipt commits remain separate; recovery reconciles the action ID.
6. Single-host file ownership surrounds start, resume and recovery. Nonblocking OS
   locks release on process death; recovery cannot steal a live owner's lock. No
   time-based lease or unsafe takeover is used. This is not a distributed protocol.
7. Missing human decisions return to suspension. Notes and compensating mutations
   require approval as well as authorization. Ambiguous execution is not an ordinary
   retry. Terminal workflows remain terminal.
8. Strict typing, lint, per-module statement coverage, security checks, trace-export
   assertions and evaluator negative controls supply evidence. Local model runs
   remain distinct from deterministic verification and independent acceptance.
9. Live retrieval evidence justified a bounded primary-document policy for the
   reference corpus: preserve the first two ranked results, and retain later
   candidates only from the leading document, within the caller's top-k ceiling.
   The generic retriever keeps this optional; the reference composition enables
   it with a three-chunk ceiling. This trades broader cross-document recall for
   document completeness and must be recalibrated for other corpora. Nomic task
   prefixes remain inside its adapter and are selected by neutral input-purpose
   metadata. Evaluation verifies reference facts against cited, supplied context;
   source-ID membership alone is not factual support.
10. A narrow host policy refuses direct runtime system/developer/hidden prompt
    disclosure requests before retrieval. It does not impersonate model inference
    or claim general injection resistance; benign security-document questions
    remain eligible. Adversarial evaluation derives its outcome from actual
    schema, abstention and citation checks instead of a constant success value.
11. The pinned upstream Ollama 0.40.16 image had three HIGH package findings:
    two APT entries and `golang.org/x/net`. The local runtime rebuilds the same
    checksummed upstream release with `x/net v0.62.0`, upgrades APT and its library
    to `2.8.4ubuntu0.1`, and retains the upstream inference libraries. Builder and
    base images are digest-pinned. This bounded security patch must be rescanned,
    smoke-tested and retired when a verified upstream image supersedes it; it is
    not a separately maintained model-server product.

## Alternatives and consequences

Distributed workflow engines and multi-agent frameworks would add unsupported
scope. Merely editing completion labels would leave reproduced defects unfixed.
The selected approach keeps the small local reference architecture and adds the
minimum ownership, persistence and verification required by demonstrated failures.

File locks assume a local filesystem on one host. Network filesystems and multiple
machines are unsupported. SQLite is not a substitute for enterprise authentication,
distributed consensus, external API idempotency or a security audit. Development
tools and runtime telemetry require an initial dependency installation; model
weights are explicitly installed by the developer and never fetched by tests.

## Verification and acceptance

The implementing agent records commands and outcomes in the
[remediation record](../docs/engineering/phase1-7-remediation.md). Process-death tests
must inspect durable balances and action receipts from fresh processes. Independent
review is a separate acceptance step; this ADR records the owner's scope approval.

## Subsequent Review Record

The original status above describes this implementation-scope decision when written.
The later reviewer-issued acceptance of baseline `e5daf8f` is separately attributed in
[the acceptance record](../docs/engineering/phase1-7-acceptance.md). This note preserves
the original decision and does not claim certification or extend acceptance to later code.
