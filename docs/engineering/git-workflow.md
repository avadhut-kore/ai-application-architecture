# Git Workflow & Source Control Standards

This document establishes the branching model, Conventional Commits specification, pull request governance, and review standards for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Source control standards in this document satisfy Gate G7 in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). Clean commit history, traceable changes, and verified pull requests are prerequisites for production readiness.

---

## 1. Branching Strategy & Trunk-Based Discipline

The repository utilizes **short-lived feature branches** merged directly into the `main` branch:

* **Main Branch**: The `main` branch is continuously deployable, protected from direct commits, and requires passing CI checks and reviews to merge.
* **Branch Naming Standard**:
  * `feat/<short-description>`: New reference application, pattern, or engineering capability.
  * `fix/<short-description>`: Defect fix, broken link remediation, or bug resolution.
  * `docs/<short-description>`: Documentation improvements, ADR additions, or diagram updates.
  * `refactor/<short-description>`: Structural code improvements without behavioral modification.
  * `test/<short-description>`: Test suite additions or evaluation dataset expansion.
* **Branch Lifespan**: Branches should live no longer than 48–72 hours to prevent merge drift and large conflict surfaces.

---

## 2. Conventional Commits Specification

All commit messages must follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) standard:

```
<type>(<scope>): <concise description in imperative mood>

[optional body explaining motivation, trade-offs, and architecture rationale]

[optional footer: BREAKING CHANGE, Closes #123, ADR-0004]
```

### Approved Types
* `feat`: A new feature or reference application implementation.
* `fix`: A bug fix or defect correction.
* `docs`: Documentation-only changes.
* `style`: Code style formatting (whitespace, formatting, linter fixes).
* `refactor`: Code restructuring that neither fixes a bug nor adds a feature.
* `perf`: Performance improvement (token efficiency, latency reduction).
* `test`: Adding missing tests, golden eval datasets, or test doubles.
* `build`: Build system, package manager, or dependency lockfile changes.
* `ci`: Continuous integration workflow or script changes.
* `chore`: Repository maintenance tasks.

### Commit Message Examples
```
feat(eval): add golden evaluation harness for invoice extraction

Integrates local Ollama-based evaluation runner testing faithfulness,
answer relevance, and schema compliance. Adds 50 curated samples to
tests/eval/eval_dataset.jsonl.

Closes #42
```

---

## 3. Pull Request Structure & Tier-Aware Requirements

Every Pull Request must include verifiable evidence corresponding to the tier of the code being introduced:

### PR Body Structure
```markdown
## Summary of Changes
- Concise bullet points of what changed and why.

## Implementation Tier
- [ ] Tier 1: Reference Application
- [ ] Tier 2: Pattern Example
- [ ] Tier 3: Platform Component
- [ ] Tier 4: Enterprise Template

## Verification Evidence
- Link Validation: `python3 scripts/validate-docs.py` (attach exit code 0 output)
- Linter & Type Check: `ruff` / `mypy` / `dotnet build` output
- Unit & Integration Tests: command output with coverage percentage
- AI Evaluation: baseline vs current scorecard (for Tier 1 / Tier 2)

## Applicable ADRs
- List any relevant Architecture Decision Records.
```

---

## 4. Code Review Guidelines & Non-Negotiables

Reviewers (human or automated governance checks) must verify:
1. **Phase Boundary Integrity**: Does this PR introduce future-phase speculative code?
2. **Local-First Compliance**: Does the code execute in Mode A (Ollama) or Mode B (in-memory test doubles) without requiring paid API keys?
3. **No Fake Delays**: Are there any hardcoded `time.sleep()` calls mimicking AI behavior?
4. **Separation of Assessment from Acceptance**: The author or agent must never declare their own work independently certified.
