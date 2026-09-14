# Repository Structure Standard & Structural Design

## 1. Executive Structural Analysis

Designing the directory topology of an enterprise AI reference architecture repository requires balancing three competing architectural tensions:

1. **Independent Application Isolation**: Each reference application in `apps/` must be self-contained, independently runnable, testable, and demonstrable without creating tight coupling to other applications.
2. **Reusable Architectural Building Blocks**: Common domain abstractions (e.g., `ILlmProvider`, `IEmbeddingProvider`, `IVectorStore`, `ITool`, guardrail primitives) must be centralized in `building-blocks/` to prevent code duplication across applications.
3. **Polyglot Clarity & Dependency Segregation**: Because enterprise AI architectures span Python (AI-native), .NET (enterprise APIs), TypeScript (frontends), and Java (legacy enterprise backends), language boundaries must be cleanly isolated without creating monolithic dependency sprawl.

---

## 2. Structural Architecture & Directory Layout

The repository adopts a **Modular Monorepo Architecture** organized into seven top-level zones:

```text
ai-application-architecture/
├── README.md                           # Repository entry point, mission, topology
├── VISION.md                           # Strategic long-term vision
├── SCOPE.md                            # In-scope vs. out-of-scope boundaries
├── ROADMAP.md                          # 15-phase implementation roadmap
├── AGENTS.md                           # Operating constitution for AI coding agents
├── QUALITY-GATES.md                    # Objective Quality Gates A through J
│
├── adr/                                # Architecture Decision Records
│   ├── README.md                       # ADR governance, lifecycle, index
│   └── template.md                     # Canonical ADR markdown template
│
├── docs/                               # Comprehensive Architecture Documentation
│   ├── architecture/                   # Core principles, taxonomies, standards
│   ├── ai/                             # Model governance, prompt & token standards
│   ├── patterns/                       # Intelligence & software architecture patterns
│   ├── security/                       # Threat models, OWASP LLM mitigations, RBAC
│   ├── testing/                        # Deterministic & integration test standards
│   ├── evaluation/                     # Automated eval harnesses, benchmarks, metrics
│   ├── observability/                  # OpenTelemetry GenAI semantic tracing & dashboards
│   ├── deployment/                     # Production deployment, containers, gateways
│   └── decisions/                      # Historical architectural review summaries
│
├── apps/                               # Independent Reference Applications
│   ├── _template/                      # Canonical reference application archetype
│   ├── rag-enterprise-kb/              # Enterprise RAG reference implementation
│   ├── agent-incident-triage/          # Tool-calling agent reference implementation
│   ├── workflow-reconciliation/        # Multi-agent stateful workflow implementation
│   └── ...                             # Future domain reference implementations
│
├── building-blocks/                    # Reusable Architectural Primitives & Ports
│   ├── python/                         # Python core abstractions & adapters
│   │   ├── core/                       # Interfaces: ILlmProvider, IVectorStore, etc.
│   │   ├── gateway/                    # Model gateway: rate limiting, retries, fallback
│   │   └── guardrails/                 # Input/output validation & schema enforcement
│   ├── dotnet/                         # .NET enterprise abstractions & contracts
│   └── typescript/                     # TypeScript client & shared contracts
│
├── platform/                           # Shared Local & Production Platform Services
│   ├── local-env/                      # Local Ollama orchestration & docker-compose
│   ├── model-gateway/                  # Standalone resilient AI gateway service
│   ├── eval-harness/                   # Centralized CI/CD evaluation runner
│   └── observability/                  # Prometheus, Grafana, OpenTelemetry Collector configs
│
├── tests/                              # Cross-Cutting & Governance Test Suites
│   ├── governance/                     # Quality gate verification & structural linters
│   └── integration/                    # End-to-end multi-service integration tests
│
└── scripts/                            # Operational, Task & CI Automation
    ├── bootstrap.sh                    # Developer workstation environment setup
    └── verify-gates.sh                 # Quality gate automated audit runner
```

---

## 3. Detailed Zone Responsibilities

### 3.1 `apps/` (Independent Reference Applications)
* Every application lives in its own subdirectory (`apps/<app-name>/`).
* Each application is an autonomous deployment unit containing its own:
  * `README.md` (conforming to the Reference Implementation Contract).
  * Architecture specifications and Mermaid diagrams.
  * Application source code (`src/`).
  * Unit and integration test suites (`tests/`).
  * Evaluation datasets and runners (`eval/`).
  * `docker-compose.yml` for single-command local execution.
* Applications consume shared abstractions from `building-blocks/` but **never depend directly on sibling applications in `apps/`**.

### 3.2 `building-blocks/` (Reusable Architectural Abstractions)
* Houses the vendor-agnostic ports, interfaces, and core utility abstractions.
* Divided strictly by language (`python/`, `dotnet/`, `typescript/`).
* Must maintain zero dependencies on specific application domain logic.
* Defines canonical interfaces:
  * `ILlmProvider`: Standardized prompt completion and structured generation.
  * `IEmbeddingProvider`: Vector embedding computation.
  * `IVectorStore`: Similarity search, filtering, and indexing.
  * `ITool`: Callable capabilities with JSON schema declarations.
  * `IMemoryStore`: Working, session, and episodic state storage.
  * `IGuardrail`: Pre-inference and post-inference validation pipelines.

### 3.3 `platform/` (Shared Local & Production Infrastructure)
* Centralizes infrastructure configurations that support multiple applications:
  * `platform/local-env/`: Common Docker Compose definitions bootstrapping Ollama, PostgreSQL/pgvector, Redis, and Qdrant for local development.
  * `platform/model-gateway/`: Shared reverse-proxy gateway demonstrating rate-limiting, circuit breaking, and caching in front of providers.
  * `platform/observability/`: Pre-configured OpenTelemetry Collector configurations, Prometheus scraping rules, and Grafana dashboard templates.

### 3.4 `docs/` (Architecture & Engineering Standards)
* The repository's intellectual center.
* Divided into specialized functional domains (Architecture, Security, Testing, Evaluation, Observability, Deployment).
* Every concept, pattern, and design decision implemented in `apps/` or `building-blocks/` must have corresponding documentation in `docs/`.

### 3.5 `adr/` (Architecture Decision Records)
* Historical, immutable log of architectural choices.
* Uses the sequential naming format `NNNN-title.md` and standard template.

### 3.6 `tests/` (Cross-Cutting Verification)
* Houses test suites that transcend individual applications:
  * Repository structural tests (ensuring no vendor SDKs are imported into domain layers).
  * License compliance and dependency vulnerability audits.
  * Multi-app regression benchmarks.

### 3.7 `scripts/` (Developer Ergonomics & CI Automation)
* Houses shell scripts and task definitions (`Taskfile` or `Makefile`) to automate developer onboarding, quality gate verification, and CI orchestration.

---

## 4. Critical Structural Evaluation & Trade-off Analysis

### Alternative Considered: Flat Monorepo vs. Polyrepo
* **Polyrepo**: Splitting each AI application into its own GitHub repository.
  * *Rejected*: Severely fragments architectural consistency, makes cross-cutting ADR governance nearly impossible, and leads to redundant building-block re-implementation across repositories.
* **Flat Monorepo (Single language, single folder)**:
  * *Rejected*: Unable to demonstrate polyglot enterprise architectures (.NET API gateways with Python AI workers); causes dependency hell when mixing conflicting library versions.
* **Chosen: Modular Monorepo**: Enables shared building blocks, unified documentation, and independent application runtimes with clean isolation.

---

## 5. File Anatomy of a Reference Application (`apps/<app-name>/`)

Every reference application must strictly adhere to the following directory layout:

```text
apps/<app-name>/
├── README.md                           # Reference implementation contract
├── architecture.md                     # Deep architectural design & data flow
├── docker-compose.yml                  # Single-command local runtime
├── requirements.txt / pyproject.toml   # Application-specific dependencies
├── .env.example                        # Template configuration (zero secrets)
│
├── src/                                # Clean Architecture Layers
│   ├── domain/                         # Pure business logic & entities
│   ├── application/                    # Use case orchestration & workflows
│   └── infrastructure/                 # Adapters: providers, DB, web endpoints
│
├── tests/                              # Automated Software Tests
│   ├── unit/                           # Deterministic unit tests (mocked doubles)
│   └── integration/                    # Integration tests (Ollama / DB)
│
└── eval/                               # Continuous AI Evaluation
    ├── eval_dataset.jsonl              # Versioned test scenarios & ground truth
    ├── eval_runner.py                  # Evaluation scoring script
    └── results/                        # Benchmark score historical logs
```
