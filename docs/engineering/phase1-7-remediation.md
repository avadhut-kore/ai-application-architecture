# Phases 1–7 remediation plan and evidence

## Approved scope

The repository owner approved this plan in the Codex chat on 20 November 2026.
Work is based on cross-platform fix commit `02f782f` on
`codex/phase1-7-completion`. Phase 7 delivers the Tier 2 single-agent workflow
baseline in ADR-0009; Tier 1 multi-agent applications remain decision-gated.

## Implementation sequence

1. Repair approval, input/proposal parsing and evaluator false positives.
2. Implement durable domain action receipts and exclusive crash-released workflow
   ownership; verify restart recovery through the public API.
3. Repair agent idempotency/budgets and RAG schema/evidence/budget enforcement.
4. Add runtime telemetry, pinned tooling, static analysis, coverage and CI checks.
5. Reconcile authoritative documentation and run deterministic and live local
   verification. Store exact commands, exit codes and limitations here.

## Acceptance

Applicable gates remain owned by [QUALITY-GATES.md](../../QUALITY-GATES.md).
Implementation verification does not constitute independent acceptance. No
unexecuted check or unavailable platform/model may be marked passed.

## Executive summary

> **Internal Self-Assessment — Not Independent Certification**

Implementation remediation addresses the original review's R01–R15 findings.
Local implementation verification was completed on 21 November 2026. Independent
acceptance remains pending. Remote CI and the explicitly unverified items below
must not be interpreted as passed.

The baseline preserves ports/adapters, deterministic authorization and the
approved Tier 2 Phase 7 scope. It adds durable local business transactions,
crash recovery, strict model boundaries, enforceable budgets, actual SDK spans,
locked tooling and evidence-producing quality checks. Phase 8 was not implemented.

| Phase | Implementation assessment | Independent acceptance |
| :--- | :--- | :--- |
| 1 — Standards | Executable checks and current language guidance; Windows checks passed. | Pending |
| 2 — Foundation | Strict contracts and packaging; installed wheel imports without telemetry dependencies. | Pending |
| 3 — Templates | Tier matrix, manifests and documentation validated. Templates are not deployed applications. | Pending |
| 4 — AI foundations | Live local adapter/structured generation: 30/30 valid schemas; actual SDK spans. | Pending |
| 5 — RAG | Final live 32-case reference benchmark passed: 87.5% cited reference-fact coverage, 88.54% relevance, 100% schema adherence. | Pending |
| 6 — Agent execution | Safety/budget/idempotency regressions and live read demo passed; 147.48 seconds, three steps and two read-only receipts. | Pending |
| 7 — Workflow | Public live read/credit smoke and fresh-clone/fresh-venv cross-process balance/replay trial passed. | Pending |

## Files created and modified

The [changed-file inventory](evidence/phase1-7/changed-files.txt) enumerates
repository-relative paths; the [source manifest](evidence/phase1-7/source-manifest.json)
records SHA-256 hashes. Both describe the final working-tree snapshot; generated evidence is excluded from source hashes to avoid recursion.
Changes cover root governance/tooling, CI, contracts and
telemetry, three runtime adapters, four pattern/evaluation directories, their
tests, ADRs and the relevant architecture, engineering, setup and learning docs.
Formatting changes are included; the diff is broader than the behavioral fixes.
Evidence was captured before publication. Git history identifies the published
revision; remote CI execution must be checked separately.

Executed Windows evidence is retained in the
[check manifest](evidence/phase1-7/windows-check-results.json),
[command log](evidence/phase1-7/windows-quality.txt),
[module statement measurements](evidence/phase1-7/windows-module-statements.json)
and [artifact line/branch measurements](evidence/phase1-7/windows-artifact-measurements.json).

## Architecture decisions and finding disposition

[ADR-0012](../../adr/0012-phase1-7-verification-and-local-recovery.md) records the
owner-approved scope and implementation decisions. Existing ADRs remain linked
from the affected artifacts rather than duplicating their architectural content.

| Finding | Remediation and verification focus |
| :--- | :--- |
| R01 | Notes and compensation require explicit approval; execution cannot lower capability policy. |
| R02 | Public recovery owns a crash-released single-host file lock; fresh processes test claim/effect/receipt boundaries. |
| R03 | SQLite persists business effects and action identities together; restart checks inspect balances and receipts. |
| R04 | Workflow scoring compares mutations and typed outcomes; negative controls exercise the scorer. |
| R05 | Live smoke fails unless expected workflow states, approvals, receipts and balances are observed. |
| R06 | Actual inquiry reaches the agent; strict proposals reject prose defaults, incomplete runs and customer-scope changes. |
| R07 | Action keys bind canonical operations; concurrent duplicates serialize; timeout/cancellation remains ambiguous. |
| R08 | Citations resolve only against chunks actually supplied to generation. |
| R09 | Exact response fields/types and factual/abstention constraints; invalid output fails safely. |
| R10 | Hard context limits, oversized chunk handling, finite agent deadlines/token reservations and lifetime workflow ceilings. |
| R11 | ROADMAP and ADRs agree on Tier 2 Phase 7 scope and distinguish implementation from independent acceptance. |
| R12 | Frozen environment, Windows/Linux CI matrix, strict checks, coverage, scans and evaluator regressions. Remote execution pending. |
| R13 | Real OpenTelemetry SDK spans and exporter assertions replace metadata-only observability claims. |
| R14 | Heading fragments, duplicate anchors, H1/fence rules and Mermaid rendering are checked. |
| R15 | Tier/language/version guidance, diagrams, snippets and stale verification claims reconciled with current behavior. |

Nomic query/document prefixes follow the model contract. Measured retrieval
failures justified an optional bounded primary-document policy in the reference
composition; the generic retriever retains its broader default. Direct runtime
prompt-disclosure requests have a narrow, explicit host refusal. This is not a
general injection detector. Evaluation never inserts expected answers into the
production pipeline or lowers the reference thresholds.

## Decisions deliberately deferred

Phases 8–14, a Tier 1 application, multi-agent coordination, distributed ownership,
enterprise identity integration, persistent vector infrastructure, rerankers and
hybrid retrieval remain deferred to their approved requirements and decision
gates. No speculative service/interface framework was added. No checkpoint
migration, automatic model download or cloud-key dependency was introduced.

## Quality gate verification

Gate applicability follows [QUALITY-GATES.md](../../QUALITY-GATES.md). Current
examples are Tier 2, runtime platform components Tier 3 and templates Tier 4.
The gate table records implementation evidence, not independent acceptance.

| Gate | Method, evidence and disposition |
| :--- | :--- |
| A — Boundaries | **Automated Evidence:** `python scripts/validate.py` import/structure checks. **Manual Evidence:** ports, composition roots and ADR review. Applies to Tier 3; no provider SDK dependency added to domain/contracts. |
| B — Quality | **Automated Evidence:** `python scripts/quality.py`: Ruff format/check and strict mypy across runtime packages, entrypoints and tooling. Windows final run exit 0. .NET/TypeScript execution is **Not Verified**: no implementations in those languages were added. |
| C — Testing | **Automated Evidence:** Windows final quality run: 323 tests, nine suites, no failures; every measured runtime module meets 85% statements and artifact line/branch floors. OS-death recovery and fresh-process business-state assertions included. Linux/Python 3.11.18 native-volume validation and quality checks also passed (323 tests). The telemetry runtime initializer is included in the enforced coverage floor; its measured statement coverage is 100%, branch coverage 95%. |
| D — Evaluation | Not mandatory for current Tier 2 examples, but Phase 5 reference exits remain binding. Deterministic harness results are separate from live quality. Final 32-case live RAG reference benchmark passed at 87.5% cited reference-fact coverage, 88.54% context relevance and 100% schema adherence; the preceding run failed at 84.38%. Both reports are retained. |
| E — Security | **Automated Evidence:** Bandit `-ll` exit 0: 23 low, zero medium/high findings; frozen Python runtime audit reports no known vulnerabilities; the pinned Ollama image has three HIGH package findings (two APT entries and x/net). The same-release patched image scan passed with zero HIGH/CRITICAL findings; live generation and embedding verification both exited 0. Git-history and working-tree secret scans are retained. **Manual Evidence:** boundary/threat-model review. Independent security sign-off **Not Verified**. |
| F — Telemetry | **Automated Evidence:** actual SDK exporter tests and local generation/embedding/retrieval/tool/workflow trace dumps. Span attributes omit raw goals, arguments and observations. Static data/protocol-only contracts have an explicit exemption. Distributed collector deployment is deferred. |
| G — Performance | Not applicable to current Tier 2/3 baseline. CPU latencies are measured and slow. TTFT ≤2 seconds, streaming endpoint acceptance and 500-request memory stability are **Not Verified**; no Tier 1 performance claim. |
| H — Documentation | **Automated Evidence:** internal link/anchor/style validator, external URL check and pinned Mermaid renderer. **Manual Evidence:** governance/critical runtime documentation and changed diagrams inspected. Exhaustive manual semantic review of every line and independent peer architecture review are **Not Verified**. |
| I — Local execution | **Automated Evidence:** local Ollama workflow smoke exit 0, including explicit approval and a $160 balance. Local clone plus current-source overlay, fresh venv and multi-process SQLite trial passed: 15,000 cents before approval, 16,000 after approval and after rejected replay. CLI start took 295.28 seconds; bootstrap took 12.95 seconds separately. A genuinely independent clean workstation is **Not Verified**. |
| J — Production resilience | Not applicable to current Tier 2/3 baseline. Timeouts, retry/error handling, ambiguous-action and crash recovery tests exist. Full Tier 1 circuit breaker/fallback/health-probe acceptance is **Not Verified**. |

The live RAG scorer version `2.0-cited-reference-facts` checks expected facts in
both answer and cited supplied context. It is a conservative support/completeness
proxy, not general semantic entailment or an independent hallucination audit.
Citation accuracy measures source-ID membership. Adversarial handling measures
schema, expected abstention and source-ID checks on the adversarial scenarios;
the result is computed from outcomes rather than hardcoded. Model quality is
specific to the recorded model digest, corpus, dataset, prompt and hardware.

## Local execution verification

Docker Desktop data was already located under
`D:\DockerDesktop\DockerDesktopWSL`; model weights use
`D:\ai-models\ollama`. The managed Ollama container publishes loopback only and
has an 8 GB memory limit. Qwen 2.5 7B and Nomic embedding inference use no paid
API keys. Initial image/model/dependency installation requires network access;
subsequent inference runs locally. See the
[setup procedure](../setup/local-ai-environment.md).

The approved live profile is `qwen2.5:7b` (Apache 2.0) plus `nomic-embed-text`.
Earlier Qwen 3B runs are diagnostic only: its research license was unsuitable as
the enterprise default. Model fingerprints, installed license metadata and container settings are retained
in the model manifest. License inspection is not legal certification.

The [live workflow smoke log](evidence/phase1-7/live-workflow-smoke.txt) records a
read-only completion in 227.17 seconds and fee-proposal suspension in 177.63
seconds, followed by approved completion at $160. These are separate scenarios;
the combined smoke runner takes longer than five minutes. The
[structured-evaluation log](evidence/phase1-7/live-structured-evaluation.txt)
records 100% schema adherence, 86.67% category, 76.67% sentiment and 66.67% urgency
accuracy over 30 cases, with 24.53-second mean round-trip latency. Schema validity
does not imply classification correctness.

## Known risks and limitations

File ownership assumes one host and a local filesystem. SQLite/action receipts
cannot make arbitrary third-party APIs transactional. Ambiguous effects require
reconciliation or intervention. Actor snapshots do not integrate a live identity
provider or detect external role revocation. The reference corpus and datasets
are small; synthetic customer data and unit doubles are explicitly identified.
The host refusal can miss paraphrases and reject benign quoted requests.
Approval does not establish proposal correctness; operators must inspect it.

The original review mechanically inventoried all tracked content and manually
examined selected critical code/docs. Neither that traversal nor this remediation
constitutes exhaustive human semantic review of every repository line. Remote
CI, macOS, independent security review and independent acceptance remain pending.

## Remaining issues and next steps

Review the exact working-tree revision and retained evidence independently. Remote
CI still needs execution on the reviewed revision. Accept each artifact against its actual tier
and phase exits before changing acceptance labels. Phase 8 should begin with one
document-intelligence use case, requirements/data rights, field-level scoring,
review routing, local feasibility and an ADR; no Phase 8 code belongs in this change.

## Compatibility and migration

The canonical workflow definition is now `1.1.0`. Its state checksum includes
actor permissions. Existing `1.0.0` checkpoints must not be resumed under this
definition; the engine rejects version drift. Preserve old databases for review
and use a separate new database for this baseline. No automatic checkpoint
migration or destructive reset is performed. Notes and compensation now pause
for explicit approval. Recovery requires action receipts, not matching log text.


## Live RAG evidence interpretation

The final live reference result supersedes the old deterministic canonical report.
The 32-case live run passed its reference thresholds with four conservative
reference-fact coverage failures (09, 10, 13, 30). Manual implementing-agent review
of all 32 observed answers found missing reference details in 09/10/30 and an
actual citation misattribution in 13: the correct 15-minute SLA was attributed to
the severity-definition chunk instead of the supplied SLA chunk. This defect is
retained as a known model error, not rewritten as success.

The arithmetic mean latency is 1,023,141.28 ms because case 32 recorded a
30,935,142.69 ms overnight elapsed-time outlier. Median latency is 55,835.44 ms.
The cause of that interruption was not independently established. These data
must not be presented as a normal workstation performance benchmark or proof of
Gate G. Reference-quality thresholds and latency evidence are distinct.


## Runtime patch and verification limits

The full RAG, structured-evaluation, workflow and agent benchmarks ran on the
original pinned Ollama image. Its three HIGH package findings (two CVE IDs) were
then removed by the same-release security build in
[Dockerfile.security](../../platform/ollama-adapter/Dockerfile.security).
The patched image retains the upstream inference libraries and model weights;
its generation and embedding smoke checks passed. The full probabilistic datasets
were not rerun after this dependency-only wrapper patch. Both image identities,
scan reports, commands and the exact model fingerprints are retained.

See the [patched-image scan](evidence/phase1-7/container-vulnerabilities-patched.json),
[scan command and exit code](evidence/phase1-7/container-audit-patched-command.json),
[runtime smoke results](evidence/phase1-7/runtime-smoke-results.json),
[182-component runtime SBOM](evidence/phase1-7/runtime-sbom.json),
[runtime promotion record](evidence/phase1-7/runtime-promotion.json),
[live RAG result](evidence/phase1-7/rag-live-final.json),
[manual answer review](evidence/phase1-7/rag-manual-review.json),
[fresh-environment commands](evidence/phase1-7/fresh-environment-commands.json) and
[Linux results](evidence/phase1-7/linux-check-results.json).

The constrained Linux attempt used a Windows source bind mount, one GB RAM and
two CPUs alongside inference; one OS-death fixture subprocess exceeded its
30-second deadline. The native-volume rerun passed. Source-copy integrity checks
also rejected a concurrent report edit and generated cache files in a reused
snapshot. A temporary shell script's CRLF suffix prevented one quality invocation.
These orchestration failures were retained. The final run copied only Git-visible
files to a fresh native volume directory, then passed validation and quality checks. No test timeout or
quality threshold was increased to obtain a pass.

The fresh CLI start took 295.28 seconds, close to the five-minute threshold.
Bootstrap took 12.95 seconds separately. Model/image downloads and the first
security image build are prerequisites, not included in that CLI measurement.
Slower or constrained workstations may exceed it. Windows 3.11, Linux 3.14,
macOS and ARM64 runtime builds have not been executed locally; remote CI covers
the declared Windows/Linux Python matrix but has not been run in this session.


Manual diagram inspection of the final workflow state chart and threat-boundary
PNG renders confirmed readable labels, approval routing and the separate
compensation-approval note without clipping. The pinned renderer passed all 22
Mermaid blocks. Rendered SVGs and the two inspected PNGs are retained with the
evidence. The telemetry initializer is now explicitly included in CI coverage
rather than being omitted with namespace-only initializers.


## Final evidence reconciliation

The [verification manifest](evidence/phase1-7/final-verification-summary.json)
reconciles command exits, 323 passing tests on each executed platform, 51 measured
runtime modules (minimum 87.29% statements), the patched image ID against its
scan, recorded live trace attributes, RAG provenance hashes and current Python
sources against the final Linux snapshot. The patched runtime is now the managed
loopback service. Temporary test containers were removed; the managed service,
selected models and reusable Docker build caches remain on D:.

The final default-rule working-tree secret scan passed. Two earlier flags were
verified source-file SHA-256 hashes, not credentials. Their provenance format was
changed from path-as-key mappings to separate path/sha256 records, preserving all
checksums without adding scanner exclusions. The
[redacted finding review](evidence/phase1-7/secret-findings-review.json) retains the
method and disposition. Frozen runtime dependency audit, medium/high Bandit scan,
format/lint, Compose configuration, documentation links and diff checks exited 0.
At verification time, no independent acceptance or remote CI execution had been
performed. Publication is recorded separately in Git history.

Text evidence is normalized for line endings and trailing whitespace only; original
execution outputs remain in the ignored local verification workspace.
