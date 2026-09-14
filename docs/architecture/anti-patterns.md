# Prohibited Architectural & AI Anti-Patterns

## 1. Executive Purpose

To safeguard the architectural rigor of this repository, this document catalogs the **prohibited and strongly discouraged anti-patterns** that must never be introduced into reference implementations, platform components, or documentation.

Every pull request, design review, and AI coding agent execution is validated against this catalog.

---

## 2. Catalog of Prohibited Anti-Patterns

### 1. Toy Demos Presented as Enterprise Systems
* **Anti-Pattern**: A single-file script calling an LLM endpoint, lacking domain models, error handling, tests, or evaluation, marketed as a "production reference architecture".
* **Rule**: All reference applications must meet the criteria defined in [reference-standard.md](reference-standard.md) for their designated tier.

### 2. Vendor SDKs Inside Domain or Application Logic
* **Anti-Pattern**: Direct imports of `openai`, `anthropic`, or `google.generativeai` within domain entities, use case coordinators, or business rules.
* **Rule**: Application logic must depend strictly on architectural ports. Vendor SDKs are restricted to infrastructure adapters.

### 3. Hard-Coded Provider and Model Names in Business Logic
* **Anti-Pattern**: String literals like `"gpt-4o"` or `"llama3:8b"` hardcoded deep in domain functions or prompt templates.
* **Rule**: Model identifiers and provider endpoints must be injected via configuration profiles or resolved dynamically.

### 4. API Keys and Credentials Committed to Source
* **Anti-Pattern**: Real or expired API keys, tokens, or connection strings committed into code, test files, or documentation.
* **Rule**: Zero-tolerance secrets policy. All credentials must be injected via environment variables (`.env.example` templates only).

### 5. Fake AI Responses and Simulated Production Behavior
* **Anti-Pattern**: Committing fake sleep loops (`time.sleep(2)`) or hardcoded static strings in production code paths to mimic AI inference.
* **Rule**: Production execution paths must execute real local models (Ollama) or live adapters. Test doubles are restricted strictly to unit tests (`tests/unit/`).

### 6. AI Where Deterministic Logic Is Superior
* **Anti-Pattern**: Invoking an LLM to compute math, sort arrays, validate email syntax, or execute predictable state transitions.
* **Rule**: Follow Principle 2: Deterministic logic must remain deterministic. Use native language algorithms, regular expressions, and relational queries.

### 7. Agents Where Simple Workflows Are Better
* **Anti-Pattern**: Deploying a non-deterministic autonomous ReAct agent loop for a business process that follows a strictly predefined sequence of steps.
* **Rule**: Use deterministic workflow orchestrators for known paths. Reserve autonomous agents for open-ended problem exploration.

### 8. Microservices Without Justified Non-Functional Requirements
* **Anti-Pattern**: Decomposing a simple system into multiple distributed microservices requiring message buses and service discovery without performance or domain justification.
* **Rule**: Default to a Modular Monolith. Microservices are justified only when independent deployment cycles, polyglot runtimes, or distinct scaling boundaries demand them.

### 9. Unnecessary Abstractions and Premature Shared Frameworks
* **Anti-Pattern**: Building extensive speculative inheritance hierarchies, generic interface layers, or shared multi-app frameworks before a concrete use case proves the need.
* **Rule**: Adhere to the Just-in-Time Abstraction Policy (Principle 18). Introduce abstractions only when a concrete implementation requires them.

### 10. Unbounded Autonomous Agents
* **Anti-Pattern**: Running agent reasoning loops with `while True` logic, open-ended tool access, no timeout caps, and no iteration limits.
* **Rule**: Enforce hard iteration limits (e.g., maximum 8 tool calls per turn), wall-clock timeouts, token budgets, and cycle detection.

### 11. Trusting Model Output Blindly
* **Anti-Pattern**: Passing raw model strings directly into SQL queries, database inserts, shell command interpreters, or frontend DOMs.
* **Rule**: Follow Principle 1: Parse, validate against strict domain schemas (Pydantic/Zod), and sanitize all structured outputs.

### 12. Missing Continuous Evaluations (Eval Blindness)
* **Anti-Pattern**: Merging an AI application with unit tests that only verify code syntax, without quantitative evaluation of model output quality.
* **Rule**: Every probabilistic capability must include an automated evaluation harness and versioned evaluation dataset (`eval_dataset.jsonl`).

### 13. Missing Failure Handling and Resilience
* **Anti-Pattern**: Applications crashing with uncaught exceptions when a model endpoint returns rate limits (HTTP 429), timeouts, or malformed JSON.
* **Rule**: Implement configurable timeouts, exponential backoff retries, circuit breaking, and graceful degradation paths.

### 14. Logging Sensitive Data
* **Anti-Pattern**: Dumping unredacted customer prompts, confidential documents, or credentials into persistent log sinks or OpenTelemetry trace spans.
* **Rule**: Follow Principle 10: Sanitize and redact sensitive data before emitting logs or telemetry.

### 15. Confusing RAG with Conversational Memory
* **Anti-Pattern**: Storing user chat transcripts as raw chunks in a vector database and using semantic similarity to recover the previous turn.
* **Rule**: Follow Principle 5: Separate RAG (static factual knowledge retrieval) from Memory (temporal session state, working buffers, and episodic profiles).

### 16. Confusing Tools with Agents
* **Anti-Pattern**: Calling an API client or Python function an "AI Agent".
* **Rule**: Tools are passive capabilities exposed to models. Agents are goal-directed reasoning loops that select and invoke tools dynamically.

### 17. Confusing Workflows with Agents
* **Anti-Pattern**: Labeling a 3-step hardcoded prompt chain as an "Autonomous Multi-Agent System".
* **Rule**: Workflows define deterministic control flow; agents execute non-deterministic reasoning.

### 18. Unnecessary Infrastructure Before Requirements Justify It
* **Anti-Pattern**: Provisioning Kubernetes clusters, distributed message brokers, or dedicated vector databases before defining the domain problem.
* **Rule**: Architecture First: Start with functional requirements, domain logic, and minimal local infrastructure.

### 19. Documentation Duplication and Document Sprawl
* **Anti-Pattern**: Creating multiple overlapping documents explaining the same architectural concept, or creating empty directories full of placeholder README files.
* **Rule**: Maintain one authoritative source per topic. Cross-reference authoritative standards rather than duplicating text.
