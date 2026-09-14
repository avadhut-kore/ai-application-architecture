# Building Blocks (`building-blocks/`)

## Architectural Boundary & Governance

This directory contains shared, reusable foundational components and minimum capability contracts.

### Architectural Directives

1. **Inward Dependency Direction**: Building blocks must **never** import or depend upon any application in `apps/`.
2. **Language Isolation**: Building blocks are organized by programming language (`python/`, `.net/`, `typescript/`, `java/`). Language packages must not cross-contaminate.
3. **Zero Speculative Proliferation**: Contracts and utilities are introduced only when justified by active roadmap milestones (per [ADR 0001](../adr/0001-minimum-core-contracts-and-repository-foundation.md)).
4. **Zero External Runtime Dependencies for Contracts**: Foundational contracts must rely strictly on standard language facilities (e.g. standard library typing, protocols, and data classes).
