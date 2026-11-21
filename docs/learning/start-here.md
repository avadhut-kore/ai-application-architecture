# Start Here: A Beginner's Navigation Guide

This guide is the entry point for a new engineer learning this repository. Follow
the steps in order, run one example at a time, and use the checkpoints to decide
when to move on. You do not need to read every document before your first exercise.

The implemented learning path currently reaches the approved Phase 7 baseline.
Implementation and independent acceptance are different; consult the
[roadmap](../../ROADMAP.md) and [verification report](../engineering/phase1-7-followup.md)
for scope, evidence and limitations. Future roadmap phases are not existing tutorials.

## On This Page

- [1. Choose your starting point](#1-choose-your-starting-point)
- [2. Learn the vocabulary](#2-learn-the-vocabulary)
- [3. Find your way around](#3-find-your-way-around)
- [4. Set up and run your first checks](#4-set-up-and-run-your-first-checks)
- [5. Follow the phase-by-phase path](#5-follow-the-phase-by-phase-path)
- [6. Read an example without getting lost](#6-read-an-example-without-getting-lost)
- [7. Move from deterministic exercises to real models](#7-move-from-deterministic-exercises-to-real-models)
- [8. Make your first contribution](#8-make-your-first-contribution)
- [9. Troubleshoot common problems](#9-troubleshoot-common-problems)
- [10. Know which document to trust](#10-know-which-document-to-trust)

## 1. Choose Your Starting Point

| Your background | Start with |
| --- | --- |
| New to Python or software development | Learn functions, classes, dictionaries, JSON, exceptions, type hints, basic tests and `async`/`await` first. Then complete this guide's setup and Phase 4 exercise. Return to the architecture explanations as the code becomes familiar. |
| Software engineer, new to AI | Follow the complete path below. Start with deterministic examples before installing models. |
| Architect or technical lead | Read the orientation documents, tier definitions and ADRs; then trace and run one request through each example. |

Python is the language used in the current runnable learning examples. You do not
need to install .NET, Java or Node.js to follow this path. Their standards describe
repository language roles, not prerequisites for the Python exercises.

## 2. Learn the Vocabulary

| Term | Meaning in this repository |
| --- | --- |
| LLM | A language model that generates text; its answer still needs application checks. |
| Inference | Running a model to produce an answer. |
| Port | An interface describing what an application needs, without choosing a vendor. |
| Adapter | Code connecting a port to a concrete implementation, such as Ollama. |
| Embedding | A numerical representation used to compare the meaning of text. |
| RAG | Retrieval-augmented generation: retrieve relevant evidence and supply it to a model. |
| Agent | A bounded loop in which a model proposes actions and application code checks them. |
| Workflow | Application-defined steps and transitions, including pauses and recovery. |
| HITL | Human-in-the-loop: a required human decision before a controlled action. |
| Test double | A controlled substitute used to test software behavior without real inference. |
| Evaluation | Measuring model behavior against scenarios and expected outcomes. |
| ADR | An Architecture Decision Record explaining a design choice and its trade-offs. |

## 3. Find Your Way Around

| Location | What you will find | When to open it |
| --- | --- | --- |
| [Root README](../../README.md) | Repository purpose, navigation and environment commands | First visit |
| [VISION](../../VISION.md), [SCOPE](../../SCOPE.md), [ROADMAP](../../ROADMAP.md) | Goals, boundaries and delivery sequence | Before choosing a topic |
| [Learning curriculum](README.md) | Phase guides and deeper explanations | Alongside each exercise |
| [Architecture documents](../architecture/) | Principles, taxonomy, tier definitions and local-first policy | To understand design constraints |
| [Engineering standards](../engineering/README.md) | Python, testing, security, documentation and other standards | When reading or changing the relevant area |
| [Core contracts](../../building-blocks/python/contracts/) | Provider-neutral requests, responses, ports and errors | Phase 2 and whenever following an adapter call |
| [Platform components](../../platform/) | Ollama, embedding and MCP adapters | When following an external boundary |
| [Examples](../../examples/) | Runnable patterns, tests, demos and evaluators | Main hands-on study area |
| [Templates](../../templates/README.md) | Four scaffolding archetypes | Phase 3 and before creating an approved artifact |
| [Applications](../../apps/) | The application area defined by repository governance | When following a roadmap-approved application; do not assume every planned app exists |
| [ADRs](../../adr/README.md) | Decisions and rejected alternatives | When asking why the code is designed this way |
| [Scripts](../../scripts/) | Repository validation and quality tools | Before and after making changes |

Start by skimming [architecture principles](../architecture/principles.md),
[reference tiers](../architecture/reference-standard.md) and
[local-first policy](../architecture/local-first.md). Consult individual engineering
standards as needed. AI coding agents must additionally follow [AGENTS.md](../../AGENTS.md).

## 4. Set Up and Run Your First Checks

Use Python 3.11 or newer and Git. Open a terminal at the repository root: the folder
containing `README.md`, `pyproject.toml` and `uv.lock`. The commands below work in
PowerShell and common Unix shells. The pinned `uv` installation follows the
[root quickstart](../../README.md#reproduce-the-locked-environment).

```powershell
python --version
git status --short
python -m pip install uv==0.13.9
uv sync --frozen
uv run --frozen python scripts/validate.py
uv run --frozen python scripts/quality.py
```

Initial tool/dependency installation requires network access. These deterministic
checks do not need Ollama, downloaded models, Docker or paid API keys. `--frozen`
uses the committed dependency lock rather than updating it for your exercise.

- `validate.py` checks repository structure, import boundaries, documentation,
  templates/manifests and discovered tests.
- `quality.py` checks formatting, linting, strict Python typing and coverage.
- Generated quality logs are available under `.quality/`.

**Checkpoint:** you can explain what each command checks and locate the output of
a failed check. A failure is a finding to investigate, not a reason to lower a threshold.

## 5. Follow the Phase-by-Phase Path

Read each linked guide, inspect the named implementation, and complete its checkpoint.
The guides explain the code; the roadmap owns phase scope.

| Order | Read | Inspect or do | Checkpoint before moving on |
| --- | --- | --- | --- |
| Phase 0 | [Governance guide](phase-00-governance.md) | Root vision/scope, architecture principles and local-first policy | Explain what the repository builds and what it deliberately defers. |
| Phase 1 | [Engineering standards guide](phase-01-engineering-standards.md) | [Quality gates](../../QUALITY-GATES.md), Python and testing standards | Explain why deterministic tests and real model evaluations answer different questions. |
| Phase 2 | [Foundation guide](phase-02-repository-foundation.md) | Contracts: start with `models.py`, `ports.py`, `errors.py`, then `telemetry.py` | Trace a request/response without assuming a specific model provider. |
| Phase 3 | [Template guide](phase-03-reference-templates.md) | Four template directories and their `artifact.json` manifests | Identify a pattern example, platform component and reference application without treating them as equivalent. |
| Phase 4 | [AI foundations guide](phase-04-ai-foundations.md) | [Structured generation README](../../examples/structured-generation/README.md); run the first exercise below | Explain how generated output becomes validated application data. |
| Phase 5 | [RAG guide](phase-05-knowledge-intelligence-rag.md) | [RAG README](../../examples/rag/README.md), corpus, retrieval and citation tests | Follow document → chunks → embeddings → retrieval → context → answer → citation checks. |
| Phase 6 | [Agent guide](phase-06-agentic-task-execution.md) | [Agent README](../../examples/agent-execution/README.md), registry, policy, approval and executor | Explain why a model proposal cannot directly authorize a mutation. |
| Phase 7 | [Workflow guide](phase-07-agentic-workflow-orchestration.md) | [Workflow README](../../examples/agentic-workflow/README.md), definition, engine, store and recovery tests | Explain how approval, current authority and durable receipts control execution after a restart. |

### Your First Exercise: Structured Output Without a Model

```powershell
uv run --frozen python examples/structured-generation/demo.py --mode fake
```

Open the [demo](../../examples/structured-generation/demo.py) and its
[implementation](../../examples/structured-generation/structured_generation/).
Find the request, controlled response and validation boundary. Read the
[tests](../../examples/structured-generation/tests/) for malformed-output cases.

**Expected learning:** predictable fixtures let you inspect parsing and validation.
This exercise does not demonstrate real inference or establish AI accuracy.

### Next Exercises: Retrieval and Workflow Safety

Run these separately when you reach their phases:

```powershell
uv run --frozen python examples/rag/demo.py --mode fake --query "What is the mandatory retention period for security audit logs?"
uv run --frozen python examples/agent-execution/eval_runner.py --mode fake
uv run --frozen python examples/agentic-workflow/eval_runner.py
```

The first two explicitly select controlled responses. The workflow evaluator is
also deterministic, even though it has no `--mode fake` flag. Read its safety
invariants and negative controls. Passing these exercises verifies software and
evaluation mechanics; it does not establish live model quality.

## 6. Read an Example Without Getting Lost

Use this order for each example; open only the files needed for one request first:

1. **README:** identify the problem, boundaries, prerequisites and commands.
2. **`artifact.json`:** identify the artifact's tier and declared execution mode.
3. **`demo.py`:** see which components are created and connected. This wiring is
   the composition root, not necessarily where the main business logic lives.
4. **Port and implementation:** follow the request into its service or engine,
   then across the relevant adapter boundary.
5. **Tests:** read a success case and a failure case before exploring every helper.
6. **Evaluator and dataset:** inspect how outcomes are scored and what a passing
   metric actually proves. Not every artifact has an AI evaluation dataset.
7. **ADR and verification report:** understand the trade-offs and recorded limitations.

For Phase 7, begin with the
[workflow definition](../../examples/agentic-workflow/workflow/remediation_workflow.py),
then the [engine](../../examples/agentic-workflow/workflow/engine.py),
[mutation step](../../examples/agentic-workflow/workflow/steps/mutation.py), and
[store](../../examples/agentic-workflow/workflow/store.py). Find the host-supplied
current-actor resolver and the atomic approval/checkpoint transition. The saved
initiator snapshot records history; it is not a fallback for current authorization.

**Exercise:** sketch the call path and mark where an invalid model response, denied
permission, rejected approval or timed-out mutation stops progress. Use existing
negative tests before attempting fault injection yourself.

## 7. Move From Deterministic Exercises to Real Models

Follow the [local environment guide](../setup/local-ai-environment.md) before
installing or starting a runtime. It covers Ollama, Docker storage and the local
model profile. Use its current setup instructions rather than downloading arbitrary
models from an older example in a learning guide.

The recorded reference profile uses `qwen2.5:7b` for generation and
`nomic-embed-text` for RAG embeddings. Initial setup requires network access and
model storage; subsequent inference runs locally without paid API keys. For Docker
on Windows, check the disk location before pulling images or models.

Start with one live structured-output example:

```powershell
uv run --frozen python examples/structured-generation/demo.py --mode live
```

Then follow the current live commands in the
[RAG](../../examples/rag/README.md),
[agent](../../examples/agent-execution/README.md) and
[workflow](../../examples/agentic-workflow/README.md) READMEs. For the workflow,
use the documented start → status → approve/reject sequence with the same database
and workflow ID. Review the proposed action before approving it.

Local CPU inference can take minutes. A timeout is a failed run, not successful
verification. Keep failed attempts alongside retries, and do not use an
`--allow-unverified` result as proof of a working model. A live smoke checks selected
paths; a full evaluation measures a larger scenario set.

## 8. Make Your First Contribution

Choose a small change to an existing example: clarify an explanation, reproduce a
documented error case, or add a meaningful regression for an actual defect.

1. Check the working tree and create your own branch before editing.
2. Read the relevant requirements, standards, tests and ADRs. Follow
   [AGENTS.md](../../AGENTS.md) when using an AI coding agent.
3. Change the smallest relevant area; do not implement a future phase as an exercise.
4. Run checks appropriate to the change. Documentation-only changes use:

```powershell
uv run --frozen python scripts/validate-docs.py
git diff --check
```

For runtime changes, follow the applicable checks in the root quickstart and
artifact README. Keep your own study notes outside authoritative documentation
until you have verified them against the implementation.

## 9. Troubleshoot Common Problems

| Symptom | Next action |
| --- | --- |
| `uv` is not recognized | Install it using the setup command above; if needed, reopen the terminal so its executable directory is on `PATH`. |
| `pyproject.toml` or an example cannot be found | Return to the repository root before running the command. |
| Import or dependency error | Run `uv sync --frozen`, then use `uv run --frozen python` rather than an unrelated global Python environment. |
| Ollama is unreachable or a model is missing | Follow the local setup and health checks; deterministic exercises remain available without Ollama. |
| Live output differs between runs | Inspect schema, citations, permissions and receipts; model text alone is not proof that an action happened. |
| Workflow is waiting for approval | Inspect its status, then explicitly approve or reject the recorded proposal using the documented CLI. |
| Live command times out | Record the failure and inspect resource use and logs. Do not silently switch to fake mode or declare a pass. |
| A guide and current implementation disagree | Consult the authoritative document for the topic and report the specific discrepancy; do not pick whichever rule is easier. |

## 10. Know Which Document to Trust

| Question | Authoritative starting point |
| --- | --- |
| What belongs in each phase? | [ROADMAP.md](../../ROADMAP.md) |
| Which gates and thresholds apply? | [QUALITY-GATES.md](../../QUALITY-GATES.md) |
| What are the architecture and local execution rules? | [Architecture principles](../architecture/principles.md) and [local-first policy](../architecture/local-first.md) |
| How should I implement or test a change? | Relevant [engineering standard](../engineering/README.md) |
| Why was a design chosen? | Relevant [ADR](../../adr/README.md) |
| How do I run this example? | Its current README, CLI help and implementation |
| What has actually been verified? | [Baseline evidence](../engineering/phase1-7-remediation.md) and [follow-up evidence](../engineering/phase1-7-followup.md), with their recorded revisions and limitations |

Learning guides explain these sources; they do not replace them or certify phase
acceptance. After Phase 7, use the roadmap to understand planned work, and wait for
an approved implementation and its learning material before treating it as a runnable
next lesson.
