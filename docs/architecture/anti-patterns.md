# Enterprise AI Architectural Anti-Patterns

## 1. Executive Purpose

To maintain the architectural integrity of `ai-application-architecture`, this document catalogs the **22 Prohibited Anti-Patterns** that must never be introduced into this codebase.

Each anti-pattern is documented with its **Architectural Symptom**, **Root Cause**, and **Enforced Remediation**.

---

## 2. Prohibited Anti-Patterns Catalog

### 1. Toy Demos Presented as Enterprise Architecture
* **Symptom**: A single Python file with a basic script calling an LLM endpoint, lacking unit tests, error handling, or architecture specifications, marketed as a "production reference".
* **Remediation**: Every application must satisfy the [Reference Implementation Contract](reference-implementation-standard.md) with clean architecture, tests, evaluation, and Docker orchestration.

### 2. Direct Vendor SDK Lock-In
* **Symptom**: Direct imports of `import openai` or `from anthropic import Anthropic` scattered across domain business logic, use cases, or controller files.
* **Remediation**: Business logic must depend strictly on internal port abstractions (`ILlmProvider`). Vendor SDKs live strictly inside infrastructure adapters.

### 3. Hardcoded Secrets & API Keys
* **Symptom**: Strings like `api_key = "sk-..."` or bearer tokens committed in code, test files, or sample configurations.
* **Remediation**: Enforce zero-tolerance secrets policy. Inject configuration via environment variables validated at startup. Verified by pre-commit scanners.

### 4. Hardcoded Model Identifiers Throughout Business Logic
* **Symptom**: String literals like `"gpt-4o"` or `"llama3:8b"` hardcoded deep in domain functions, prompts, or workflow rules.
* **Remediation**: Model identifiers must be defined in configuration profiles or resolved dynamically via the Model Gateway.

### 5. Hardcoded Phase / Roadmap Metadata in Runtime Logic
* **Symptom**: Application code containing checks like `if current_phase == "Phase 5": ...` or UI headers displaying internal repository roadmap milestones.
* **Remediation**: Runtime applications must be completely decoupled from repository development roadmap metadata.

### 6. Fake / Simulated Production AI Responses
* **Symptom**: Functions returning static mock strings or sleeping for two seconds (`time.sleep(2)`) to simulate AI inference in production code paths.
* **Remediation**: Production code must execute real local models (Ollama) or live adapters. Mocks and doubles are restricted strictly to automated unit test suites (`tests/unit/`).

### 7. "AI-for-the-Sake-of-AI" (Spurious Machine Learning)
* **Symptom**: Using a 70B parameter LLM to sort lists, compute mathematical sums, validate email syntax, or perform simple regex string matching.
* **Remediation**: Follow Principle 4: Deterministic logic must remain deterministic. Use native language algorithms, SQL queries, and deterministic validators.

### 8. Autonomous Agents Where Workflows Are Better
* **Symptom**: Deploying a non-deterministic ReAct agent loop for a business process that follows a strictly predefined sequence of operational steps.
* **Remediation**: Use deterministic workflow engines (DAGs, state machines). Reserve autonomous agents for open-ended problem exploration where the sequence of steps cannot be known in advance.

### 9. Premature Microservices Sprawl
* **Symptom**: Decomposing a simple reference application into 7 distributed microservices, requiring Kafka, Consul, and complex service meshes without performance or domain justification.
* **Remediation**: Default to a Modular Monolith. Microservices are justified only when independent deployability, scaling boundaries, or polyglot runtime constraints strictly demand them.

### 10. Excessive / Astronaut Abstraction
* **Symptom**: Creating seven layers of indirection (`IModelProviderFactoryProxyHandlerBean`) for a single straightforward operation.
* **Remediation**: Adhere to clean abstraction: define ports for genuine boundaries (models, vector stores, tools), but keep internal logic direct, readable, and idiomatic.

### 11. Copy-Pasted Polyglot Implementations
* **Symptom**: Translating Python code line-by-line into C# or Java without adhering to the idioms, design patterns, and frameworks of the host ecosystem.
* **Remediation**: Implementations in other languages must be architecturally justified and fully idiomatic to their respective platforms.

### 12. Missing Continuous Evaluation (Eval Blindness)
* **Symptom**: Merging an AI application with unit tests that only verify code syntax, without any quantitative evaluation of model output quality.
* **Remediation**: Mandatory evaluation harness with versioned `eval_dataset.jsonl` testing groundedness, context relevance, faithfulness, and schema adherence.

### 13. Telemetry & Observability Blindness
* **Symptom**: Invoking models without distributed tracing, with zero tracking of prompt tokens, completion tokens, or time-to-first-token.
* **Remediation**: Standardize on OpenTelemetry GenAI semantic conventions. Trace every prompt, completion, tool call, and retrieval step.

### 14. Missing Failure Handling & Graceful Degradation
* **Symptom**: An application crashing with uncaught exceptions when a model endpoint returns HTTP 429, timeouts, or malformed JSON.
* **Remediation**: Implement timeouts, exponential backoff retries, circuit breakers, and fallback routing with informative user degradation messages.

### 15. Unbounded Autonomous Agents
* **Symptom**: An agent loop running with a `while True:` condition, no iteration limits, no timeout caps, and unmonitored write access to external databases.
* **Remediation**: Hard caps on maximum iterations (e.g., 8 tool calls), timeouts, and token budgets. State-mutating tools require human-in-the-loop authorization.

### 16. Blindly Trusting Model Output
* **Symptom**: Passing raw LLM generated strings directly into SQL queries, shell commands, HTML DOMs, or database inserts.
* **Remediation**: Follow Principle 1: Parse and validate all structured outputs using Pydantic / Zod schemas and sanitize data against injection.

### 17. Conflating RAG with Conversational Memory
* **Symptom**: Storing user chat history as raw unstructured text chunks in a public vector database and performing vector similarity to recover the previous message.
* **Remediation**: Separate RAG (static factual knowledge retrieval) from Memory (temporal session state, working scratchpads, and structured episodic user profiles).

### 18. Treating Memory as a Raw Database Dump
* **Symptom**: Shoveling the entire historical chat transcript (thousands of tokens) into every prompt context until context overflow occurs.
* **Remediation**: Implement tiered memory: sliding window buffers, hierarchical summarization, and key-value preference extraction.

### 19. Treating Agents as Chatbots
* **Symptom**: Building an interactive text chat UI and calling it an "Agent" when it performs zero autonomous tool calling, planning, or state inspection.
* **Remediation**: Chatbots are conversational interfaces (Dimension 1). Agents are autonomous reasoning loops that manipulate tools and environment state (Dimension 2).

### 20. Treating Workflows as Agents
* **Symptom**: Labeling a sequential 3-step hardcoded prompt chain as an "Autonomous Multi-Agent System".
* **Remediation**: Call a workflow a workflow. Workflows execute deterministic control flow; agents execute non-deterministic reasoning.

### 21. Building Infrastructure Before Requirements Justify It
* **Symptom**: Provisioning complex Kubernetes clusters, Redis clusters, and distributed vector databases before defining the business problem and domain model.
* **Remediation**: Architecture First: Start with requirements and domain logic. Provision supporting infrastructure only when non-functional requirements require it.

### 22. Naked Tool Execution (Unchecked Privilege)
* **Symptom**: Granting an agent raw Python `exec()` or root shell execution access without parameter validation, network sandboxing, or audit logging.
* **Remediation**: Tools must expose typed JSON schemas, run in least-privilege sandboxes, and prohibit direct OS execution unless explicitly designed and monitored.
