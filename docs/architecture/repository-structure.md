# Repository Structure & Dependency Governance

## 1. Executive Architectural Design

This repository adopts a **Modular Monorepo Architecture**. The repository houses multiple reference applications, building blocks, platform capabilities, and architectural documentation within a single unified Git repository while enforcing strict **dependency isolation**.

> [!IMPORTANT]
> **Independent Application Isolation Rule**  
> Future applications must **not** become tightly coupled merely because they reside in the same monorepo.  
> Every reference application in `apps/` must be an independent deployment unit with its own dependencies, configuration, tests, and execution lifecycle.

---

## 2. Directory Layout & Structural Zones

```text
ai-application-architecture/
├── README.md                           # Executive entry point, mission, navigation
├── VISION.md                           # Strategic long-term vision & paradigm
├── SCOPE.md                            # Operational scope boundaries
├── ROADMAP.md                          # 15-phase sequential engineering roadmap
├── AGENTS.md                           # Operating constitution for AI coding agents
├── QUALITY-GATES.md                    # Objective Quality Gates A through J
│
├── adr/                                # Architecture Decision Records
│   ├── README.md                       # ADR lifecycle, governance, and index
│   └── template.md                     # Canonical MADR/AI decision template
│
├── docs/                               # Authoritative Architecture Documentation
│   └── architecture/                   # Core architectural standards
│       ├── principles.md               # 14 core AI engineering principles
│       ├── taxonomy.md                 # 15 application domains, patterns & dimensions
│       ├── repository-structure.md     # Structural design & dependency rules
│       ├── reference-standard.md       # Four reference implementation tiers
│       ├── local-first.md              # 3-mode local-first & Ollama policy
│       ├── technology-governance.md    # Technology evaluation & abstraction policy
│       ├── language-strategy.md        # Language roles & polyglot boundaries
│       └── anti-patterns.md            # Catalog of prohibited anti-patterns
│
├── apps/                               # Independent Reference Applications
│   ├── _template/                      # Scaffolding archetypes (Tier 4)
│   └── <app-name>/                     # Self-contained reference applications (Tier 1 & 2)
│
├── building-blocks/                    # Reusable Architectural Primitives (Tier 3)
│   ├── python/                         # Python core abstractions & adapters
│   ├── dotnet/                         # .NET enterprise abstractions & contracts
│   └── typescript/                     # TypeScript shared client contracts
│
├── platform/                           # Shared Platform Capabilities (Tier 3)
│   ├── local-env/                      # Shared local container configurations
│   ├── model-gateway/                  # Conditional resilient AI gateway service
│   └── eval-harness/                   # Consolidated evaluation runners (Phase 11+)
│
├── tests/                              # Cross-Cutting & Governance Verification
│   ├── governance/                     # Quality gate verification & structural linters
│   └── integration/                    # Multi-component cross-service integration tests
│
└── scripts/                            # Task Automation & CI Scripts
    ├── bootstrap.sh                    # Workstation developer setup
    └── verify-gates.sh                 # Automated quality gate audit runner
```

---

## 3. Structural Zone Responsibilities

### 3.1 `apps/` (Independent Applications)
* Every application lives in an isolated subdirectory (`apps/<app-name>/`).
* Each application contains its own package definition (`pyproject.toml`, `.csproj`, or `package.json`), Docker Compose environment, test suite, and evaluation dataset.
* Applications consume shared abstractions from `building-blocks/` or connect to services in `platform/` via network contracts.
* **Prohibition**: An application in `apps/foo` must **never** import code directly from `apps/bar`.

### 3.2 `building-blocks/` (Reusable Primitives & Ports)
* Contains vendor-neutral port interfaces, common domain value objects, and reusable base adapters.
* Organized strictly by programming language.
* Must maintain zero dependencies on application-specific domain logic.

### 3.3 `platform/` (Shared Infrastructure & Capabilities)
* Houses shared developer and operational infrastructure (e.g., shared local Docker Compose files for Ollama/PostgreSQL, consolidated evaluation runners, and optional model gateways).
* Components here are managed as Tier 3 Platform Components.

### 3.4 `docs/` (Authoritative Architecture Documentation)
* The repository's intellectual and governance center.
* Concentrated in `docs/architecture/` to prevent documentation sprawl and empty placeholder directories.

### 3.5 `adr/` (Architecture Decision Records)
* Historical, immutable log of architectural decisions following the sequential numbering format `NNNN-title.md`.

---

## 4. Monorepo Dependency Rules

To prevent architectural erosion, the following dependency flow rules are enforced:

```
┌────────────────────────────────────────────────────────┐
│ apps/<app-name>                                        │
│ May depend on: building-blocks/<language>              │
│ May NOT depend on: apps/<other-app>                    │
└───────────────────────────┬────────────────────────────┘
                            │ imports
┌───────────────────────────▼────────────────────────────┐
│ building-blocks/<language>                             │
│ May NOT depend on: apps/* or platform/*                │
└────────────────────────────────────────────────────────┘

Platform services run as independent network containers;
Applications communicate with platform services via HTTP/gRPC,
never through shared memory or compile-time coupling.
```

---

## 5. Phased Scaffolding Rule

In compliance with Phase 0 constraints:
* No application directories (`apps/<app-name>`) are created in Phase 0.
* No shared building block libraries are implemented in Phase 0.
* Only the governance standards and directory designs are established in this phase.
