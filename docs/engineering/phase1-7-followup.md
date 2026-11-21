# Phase 1–7 selective hardening: completion evidence

> **Internal Self-Assessment — Not Independent Certification**

## 1. Executive summary

The owner approved selective integration following review of PR #1, head
`28aef29595641c81eea0538a06ccaeb74c5f505b`. Work extends baseline
`e5f8908f79b931494216c3a8298c7ab2ad4b5c88` on `codex/phase1-7-completion`.
The PR was not merged wholesale. This is an implementation assessment, not independent
acceptance, production certification, or a claim of 100% accuracy.

The selected changes enforce recursive argument schemas, explicit MCP host classifications,
strict/bounded MCP stdio, complete RAG prompt budgets and strict JSON parsing, bounded
agent arguments/results/observations, scoped replay identities, current mutation authority,
and transactional approval/checkpoint updates. Live defaults, native model schemas,
cumulative token/deadline limits, ambiguous receipts, telemetry, human gates and existing
domain database tables remain in place.

## 2. Files created and modified

The complete repository-relative inventory is in
[`changed-files.txt`](evidence/phase1-7-followup/changed-files.txt).
The main implementation paths are:

- `examples/agent-execution/agent/{schema,observation,registry,executor,engine}.py`
- `platform/mcp-adapter/mcp_adapter/{adapter,client,protocol,server}.py`
- `examples/rag/rag/{service,context_builder}.py`
- `examples/agentic-workflow/workflow/{engine,store,remediation_workflow}.py`
- `examples/agentic-workflow/workflow/steps/mutation.py`
- Corresponding regression suites, composition roots, four artifact READMEs, two threat
  models, ADR-0013 and the ADR index. `.gitignore` excludes transient quality outputs.

## 3. Architecture decisions

[ADR-0013](../../adr/0013-selective-phase7-boundary-hardening.md) records the approved
scope. Schema registration fails closed on unsupported declarations. The recursive
validator deliberately supports a subset of JSON Schema. MCP server discovery never
supplies authority: the host declares allowed tools and their side effects.

Mutations resolve the initiating identity through an injected current-actor callback;
missing identities never fall back to a saved role. Both forward execution and compensation
use this boundary. SQLite commits the pending approval decision and resulting checkpoint
in one conditional transaction. Legacy claim-only recovery remains supported. Existing
`customers`, `accounts` and `domain_actions` tables and workflow definition 1.1.0 are retained.

Executor action identities bind trusted scope, capability instance/name and argument
snapshot. Caller mutations cannot change an in-flight argument snapshot or cached result.
Oversized/invalid mutation outputs remain ambiguous because the effect may already exist.
Observation truncation preserves framing; model/provider failures retain prior receipts.

## 4. Decisions deliberately deferred

No preparation cache, alternate business database, note approval bypass, scripted
production workflow or future-phase capability was imported. Enterprise identity-provider
integration remains outside this reference example. No dependencies or model images
were changed, and AGENTS.md did not require further modification.

## 5. Quality gate verification

The authoritative applicability is [QUALITY-GATES.md](../../QUALITY-GATES.md).
Tier 2 examples require B/C/H/I; the Tier 3 MCP component requires A/B/C/E/F/H.

| Gate | Assessment and verification method |
| --- | --- |
| A — Architecture | **Automated Evidence:** `scripts/validate.py` passed structure/import/template checks on Linux. **Manual Evidence:** selective adapter/domain boundary review and ADR-0013. No new provider dependencies enter contracts. |
| B — Quality/types | **Automated Evidence:** final Ruff formatting/checking and strict mypy pass on Windows 3.14.3 and Linux 3.11.18. Initial formatting and Windows-only constant typing failures are retained in the initial logs; corrected static runs and MCP regressions are separate evidence. |
| C — Tests | **Automated Evidence:** 358 tests in nine suites passed per platform. 53 runtime modules meet the statement threshold; minimum 87.65%. Aggregate artifact line/branch thresholds also pass. The final portable subprocess lookup additionally passed all 34 MCP tests per platform. |
| D — AI evaluation | **Not mandatory for these Tier 2 artifacts. Automated Evidence:** workflow 30/30 deterministic scenarios; agent, RAG and foundation deterministic evaluators exit 0. These verify harness/safety mechanics, not real model quality. Full live 30/32-case datasets were not rerun; historical scores remain in the baseline report. Selected live checks are recorded below. |
| E — Security | **Automated Evidence:** Bandit reports 21 low, zero medium/high findings; locked runtime `pip-audit` reports no known vulnerabilities; redacted Git-visible secret scan reports no leaks. **Manual Evidence:** updated threat models and current-authority/approval/transport review. Existing model image was unchanged; its previous image audit is historical evidence. |
| F — Observability | **Automated Evidence:** contracts/telemetry suite 56/56; MCP tracing decorator retained and failure payload span regression passed. **Not Verified:** a fresh comprehensive live trace/privacy audit of every path was not repeated. |
| G — Performance | **Not applicable to Tier 2/3. Not Verified:** no throughput/load/SLA certification. A live credit attempt exceeded 300 seconds and failed closed. Timings are local observations, not benchmarks. |
| H — Documentation | **Automated Evidence:** documentation/link checker and whitespace validation; exact final counts are recorded in `documentation.log`. **Manual Evidence:** readme/threat-model descriptions reconciled with implemented boundaries. No diagram topology changed. |
| I — Local execution | **Automated Evidence:** local Docker Ollama with Qwen 2.5 7B and Nomic embeddings, without paid API keys. See live outcomes below. |
| J — Resilience | **Not applicable to Tier 2/3. Automated Evidence:** focused timeout, cancellation, atomic rollback, concurrent resume and real process-death regressions. This is not comprehensive chaos certification. |

Evidence is retained under [`evidence/phase1-7-followup/`](evidence/phase1-7-followup/).
The `*-quality-initial.log` files intentionally retain failures. Final static logs,
MCP rerun logs, `*-coverage-summary.json` and `*-artifact-coverage.json` establish the
corrected result; do not interpret an initial full-run exit code as a clean pass.
Linux runs use the pinned Python image and native named-volume snapshot recorded in
`linux-initial-command.json`. `linux-corrected-command.json` records the final source
patches, static rerun and 34 MCP tests after the portability correction.
All Python files in that snapshot match the final host source; documentation/evidence
added afterward is validated separately. No remote merge, PR comment or publication
was performed by this follow-up task.

## 6. Local execution verification

**Automated Evidence:** `.venv/Scripts/python.exe -X utf8 -u
examples/agentic-workflow/live_smoke.py` exited 0 on retry. The read-only investigation
completed in 61.942 seconds with zero financial mutations; the real $10 credit proposal
reached `AWAITING_APPROVAL` in 132.540 seconds. Operator approval resumed it to
`COMPLETED`, with the durable balance moving from $150 to $160. The first run exited 1,
as described below. Both complete logs and command outcomes are retained.

**Automated Evidence:** the retained `rag-live-smoke.txt` harness exited 0 using real
Nomic corpus/query embeddings and Qwen generation. It returned the exact seven-year
audit-log retention rule, with schema validity, sufficient evidence and valid citation
`sec-01#c1`, in 93.0 seconds including indexing. Default limits were 8,000 prompt
characters and 512 output tokens. This is one smoke scenario, not the 32-case evaluation.
See `rag-live.json` and `rag-live.log` for the actual response and assertions.

The initial workflow run completed read-only investigation in 283.481 seconds, then
hit the 300-second deadline on the credit proposal (300.231 seconds) without requesting
approval or mutating funds. That failed run is retained, not hidden by a retry.

## 7. Known risks and limitations

- Local 7B inference latency varies substantially; a deadline failure is operationally
  significant even though authorization and financial safety fail closed.
- The host resolver is an integration seam; the CLI directory is a reference fixture.
  CLI manager/admin role validation is not external authentication. Directory freshness
  and authenticated operator identity remain deployment responsibilities.
- Approval/checkpoint atomicity does not make every audit event or external side effect
  part of one distributed transaction. Durable domain receipts and reconciliation remain
  necessary; local checksum integrity does not protect against a privileged database writer.
- Character bounds limit retained/forwarded data; a tool can allocate memory internally
  before returning. In-process test-server calls do not provide process isolation.
- Valid citation identifiers do not establish semantic entailment. Smoke checks and
  deterministic evaluators cannot certify general AI accuracy or adversarial resistance.
- Remote GitHub CI, macOS, other model versions and independent acceptance are **Not Verified**.

## 8. Remaining issues and next steps

The approved selective hardening and local verification are complete. Arrange independent
review of this change and the baseline before accepting Phase 1–7. Keep Phase 8 onward
outside this scope. A passing local smoke does not remove the latency risk or replace
full probabilistic evaluation before a release that changes model behavior.
