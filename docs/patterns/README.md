# Architecture & Intelligence Patterns Catalog

## 1. Domain Scope

The `docs/patterns/` directory provides an authoritative catalog of **Intelligence Patterns** (Dimension 2) and **Architecture Patterns** (Dimension 3) used across enterprise AI applications.

Each pattern documented here must include an architectural overview, sequence diagram, failure modes, trade-offs, and reference code mappings.

---

## 2. Intelligence Patterns (Dimension 2 Catalog)

* **Retrieval-Augmented Generation (RAG)**:
  * Naive RAG, Advanced Chunking, Dense + Sparse (BM25) Hybrid Search, Reciprocal Rank Fusion (RRF), Cross-Encoder Re-ranking, GraphRAG.
* **Tool Calling & Execution**:
  * Single-turn tool calling, parallel tool execution, tool parameter schema validation, sandboxed execution.
* **Agentic Reasoning Loops**:
  * ReAct (Reasoning + Acting), Plan-and-Solve, Reflexion, Tree of Thoughts.
* **Multi-Agent Topologies**:
  * Hierarchical Supervisor-Worker, Round-Robin Debate, Consensus Voting, Swarm routing.
* **Semantic Memory Architectures**:
  * Working scratchpad memory, conversational buffer memory, summary memory, vector episodic memory.

---

## 3. Architecture Patterns (Dimension 3 Catalog)

* **Modular Monolith**: Strongly bounded modules within a single containerized process.
* **Hexagonal / Clean Architecture**: Ports and adapters isolating domain logic from external LLM providers and vector databases.
* **Deterministic Workflow Engine**: Durable state machines coordinating steps with saga compensation.
* **Event-Driven AI Processing**: Asynchronous message queues decoupling high-latency inference from client requests.
* **Human-in-the-Loop (HITL)**: Durable suspension, approval routing, and callback resumption.
* **Streaming Full-Duplex**: WebSockets delivering real-time tokens, audio streaming, and barge-in control.

---

## 4. Pattern Documentation Standard

Every pattern added to this directory must follow the standard structure:
1. **Intent & Problem**: What enterprise challenge does this pattern address?
2. **Structure & Diagram**: Mermaid diagram of components and interactions.
3. **Applicability**: When to use and when to avoid.
4. **Resilience & Failure Modes**: How the pattern behaves under model failure or network timeouts.
5. **Reference Implementations**: Links to applications in `apps/` implementing this pattern.
