# ADR-0013: Selective Phase 7 boundary hardening

- Status: Accepted for implementation by the repository owner in the current review session.
- Scope: Existing Phase 1–7 implementations; no new roadmap capabilities.

## Context

Review of PR #1 identified useful boundary checks alongside changes incompatible with
our live-model defaults, approval controls, telemetry and persisted business data.
The existing verification baseline is recorded in [ADR-0012](0012-phase1-7-verification-and-local-recovery.md).

## Decision and approved plan

Selectively integrate recursive capability validation, explicit MCP host classifications
and bounded protocol handling, strict RAG parsing and complete prompt budgets, bounded
agent observations, scoped execution identities, current actor resolution and atomic
approval/checkpoint transitions. Preserve native output schemas, cumulative token and
time limits, ambiguous receipts, telemetry, existing SQLite tables and approval gates.
Validate each boundary with deterministic regressions, then run repository static,
coverage and cross-platform checks and relevant local-model smoke tests. Record actual
results separately from the historical baseline.

## Deferred decisions

Do not import the preparation cache, scripted production workflow, alternate business
database or note approval bypass. An external identity provider remains outside this
reference implementation; composition roots supply a trusted current-actor resolver.

## Consequences

MCP integrations must explicitly classify allowed tools. Unsupported schema keywords
fail closed. Inputs exceeding configured budgets are rejected before model dispatch.
Concurrent approval transitions must commit their checkpoint and decision together.
