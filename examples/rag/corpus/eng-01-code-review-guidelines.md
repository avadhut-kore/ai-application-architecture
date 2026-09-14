---
id: eng-01
title: Engineering Code Review Guidelines
department: engineering
category: guideline
version: 1.4
---

# Engineering Code Review Guidelines

## 1. Review and Approval Policies
All pull requests (PRs) targeting protected branches (`main`, `release/*`) require a minimum of **2 peer review approvals** from designated CODEOWNERS. Self-approval is blocked by repository branch protection rules.

## 2. Quality Gates and Automated Checks
Before a pull request can be merged:
* All automated CI pipelines must report green status with zero exit errors.
* Deterministic unit test statement coverage must meet or exceed **85% statement coverage** on newly added or modified business logic.
* Static type analysis (`mypy --strict`, `tsc --strict`, or `dotnet format`) must pass without warnings or suppressed errors.

## 3. Pull Request Size Limitations
To facilitate thorough peer review, pull requests must not exceed **400 lines of code changed** (excluding auto-generated code and test fixtures). Pull requests exceeding this threshold must be decomposed into smaller sequential milestones.
