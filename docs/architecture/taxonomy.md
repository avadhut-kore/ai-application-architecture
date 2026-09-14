# AI Application Architecture Taxonomy

## 1. Executive Purpose

Architectural clarity requires precise classification. A major failure in AI software engineering is mixing business problem domains, intelligence algorithms, software architectural patterns, and operational capabilities into an ambiguous taxonomy (e.g., treating "RAG" as an application, an architecture, and a technology simultaneously).

This document establishes a **Five-Part Taxonomy** supplemented by **Operational Classification Dimensions**:

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. APPLICATION DOMAINS (What business problem is being solved?)        │
 │    15 strategic enterprise problem spaces                              │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 2. INTELLIGENCE PATTERNS (How is AI reasoning generated?)              │
 │    Computational mechanisms: RAG, tool calling, ReAct, multi-agent     │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 3. ARCHITECTURE PATTERNS (How is the software structured?)             │
 │    Software topology: modular monolith, event-driven, workflows        │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 4. PRODUCTION CAPABILITIES (What operational qualities are enforced?)  │
 │    Cross-cutting concerns: auth, retries, caching, tracing, guardrails │
 ├────────────────────────────────────────────────────────────────────────┤
 │ 5. GOVERNANCE CAPABILITIES (How is the system governed and audited?)   │
 │    Repository standards: ADRs, quality gates, threat models            │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The 15 Enterprise Application Domains

Application domains represent distinct business problem spaces. Each domain possesses unique functional goals, user interaction styles, data lifecycles, and failure modes.

### 1. Conversational & Assistant Systems
* **Purpose**: Multi-turn natural language dialogue assisting human users with tasks, inquiries, or guided onboarding.
* **Boundaries**: Focuses on conversational state, persona maintenance, and interactive guidance. Does not include open-ended autonomous background task execution.
* **Representative Use Cases**: Customer service assistants, internal IT helpdesks, interactive product advisors.
* **Overlap Rules**: When a conversational assistant initiates multi-step autonomous tool executions, it coordinates with Domain 6 (Agentic Task Execution).

### 2. Knowledge Intelligence & Enterprise Search
* **Purpose**: Grounded retrieval, question answering, and contextual synthesis over proprietary enterprise documentation, policies, and knowledge bases.
* **Boundaries**: Read-only information retrieval and synthesis. Does not execute transactional state mutations.
* **Representative Use Cases**: Corporate policy search, technical documentation assistants, regulatory compliance Q&A.
* **Overlap Rules**: Focuses on knowledge access; when documents require layout extraction and OCR, it consumes outputs from Domain 4 (Document Intelligence).

### 3. Structured Extraction & Transformation
* **Purpose**: Converting unstructured or semi-structured text and legacy payloads into strongly typed, schema-validated enterprise domain models.
* **Boundaries**: Deterministic schema adherence, entity parsing, and field mapping. Does not manage conversational dialogue.
* **Representative Use Cases**: Customer email intent extraction, legacy EDI-to-JSON mapping, regulatory notice classification.
* **Overlap Rules**: Serves as an upstream ingestion stage for transactional workflows and business applications.

### 4. Document Intelligence / Intelligent Document Processing (IDP)
* **Purpose**: Automated parsing, layout understanding, table recognition, and data extraction from complex multi-page documents.
* **Boundaries**: Handles visual document structure, forms, tables, and OCR artifacts. Distinct from plain text extraction.
* **Representative Use Cases**: Invoice and receipt extraction, bill of lading parsing, contract metadata indexing.
* **Overlap Rules**: Integrates vision/multimodal models (Domain 10) and feeds validated structured records to workflows (Domain 7).

### 5. Decision Intelligence
* **Purpose**: Augmenting high-stakes operational or strategic decisions by combining deterministic business rules, predictive ML models, and LLM contextual explanations.
* **Boundaries**: Focuses on decision evaluation, scoring, trade-off analysis, and auditable reasoning traces.
* **Representative Use Cases**: Credit risk assessment, insurance underwriting triage, fraud adjudication, loan pre-qualification.
* **Overlap Rules**: Deterministic rules govern the final decision threshold; models provide contextual explanations and feature interpretation.

### 6. Agentic Task Execution
* **Purpose**: Goal-directed, bounded autonomous reasoning loops that inspect runtime state, select tools, and adapt to intermediate observations.
* **Boundaries**: Autonomous problem-solving within an isolated task context. Does not manage long-running multi-system business sagas.
* **Representative Use Cases**: System diagnostic troubleshooting, data gathering scripts, sandbox code execution.
* **Overlap Rules**: Executes individual tasks within boundaries defined by Domain 7 (Agentic Workflow Orchestration).

### 7. Agentic Workflow Orchestration
* **Purpose**: Coordinating multiple specialized agents, human approval gates, and deterministic state transitions across long-running business workflows.
* **Boundaries**: Manages distributed state persistence, sagas, compensation transactions, and pause/resume checkpoints.
* **Representative Use Cases**: Multi-party contract approval, end-to-end employee onboarding, financial reconciliation.
* **Overlap Rules**: Orchestrates agents (Domain 6) and deterministic rules within a durable workflow backbone.

### 8. Research & Synthesis Systems
* **Purpose**: Deep, recursive investigation of complex topics across heterogeneous data sources, producing structured analytical synthesis.
* **Boundaries**: Focuses on multi-source discovery, cross-referencing, contradiction resolution, and citation graph generation.
* **Representative Use Cases**: Competitive market research, legal case law analysis, clinical research synthesis.
* **Overlap Rules**: Employs deep search techniques distinct from single-turn enterprise search (Domain 2).

### 9. Voice & Real-Time Interaction
* **Purpose**: Ultra-low-latency, bi-directional audio streaming, speech-to-text, and conversational voice interfaces.
* **Boundaries**: Addresses sub-second latency, voice activity detection (VAD), full-duplex streaming, and barge-in handling.
* **Representative Use Cases**: Telephony customer support, hands-free field technician voice assistants, live translation.
* **Overlap Rules**: Voice is an interaction transport layer that can drive Conversational Systems (Domain 1) or Task Agents (Domain 6).

### 10. Multimodal Intelligence
* **Purpose**: Joint reasoning across images, video, spatial layouts, diagrams, sensor data, and text.
* **Boundaries**: Requires vision-language models and media processing pipelines.
* **Representative Use Cases**: Quality control defect inspection, medical image preliminary triage, architectural blueprint analysis.
* **Overlap Rules**: Frequently integrated into Document Intelligence (Domain 4) and Voice/Real-Time systems (Domain 9).

### 11. Data & Analytics Intelligence
* **Purpose**: Natural language interfaces for relational databases, data warehouses, and analytics platforms (Text-to-SQL, Text-to-Pandas).
* **Boundaries**: Generates, validates, and safely executes analytical queries with strict read-only guarantees and schema isolation.
* **Representative Use Cases**: Self-service business intelligence, ad-hoc metric exploration, automated dashboard summary generation.
* **Overlap Rules**: Must enforce read-only transaction boundaries; never conflated with operational OLTP updates.

### 12. Predictive ML & Forecasting
* **Purpose**: Integrating statistical machine learning, numerical regression, classification, and time-series forecasting with AI systems.
* **Boundaries**: Solves numerical predictive problems where classical statistical methods outperform text models.
* **Representative Use Cases**: Demand forecasting, equipment predictive maintenance, churn propensity scoring.
* **Overlap Rules**: ML outputs are consumed as features or signals by Decision Intelligence (Domain 5).

### 13. Recommendation & Personalization
* **Purpose**: Contextual discovery, candidate retrieval, ranking, and explanation generation for products, content, or actions.
* **Boundaries**: Combines collaborative/content filtering algorithms with generative reasoning for personalized explanations.
* **Representative Use Cases**: Enterprise software navigation recommendations, personalized learning pathways.
* **Overlap Rules**: Uses vector embeddings and predictive models to retrieve candidates; models generate natural language rationales.

### 14. Software Engineering & Coding AI
* **Purpose**: Assisting software engineering lifecycles: code generation, architectural analysis, refactoring, test synthesis, and security reviews.
* **Boundaries**: Involves Abstract Syntax Tree (AST) parsing, compiler feedback loops, and deterministic test execution sandboxes.
* **Representative Use Cases**: Automated pull request review assistants, legacy codebase migration, test suite generation.
* **Overlap Rules**: Specialized agentic task execution applied specifically to codebases and developer environments.

### 15. AIOps / DevOps / IT Operations AI
* **Purpose**: Autonomous monitoring, log analysis, anomaly correlation, incident diagnosis, and guided remediation across IT systems.
* **Boundaries**: High-volume telemetry processing, safe read-only diagnostics, and gated remediation commands.
* **Representative Use Cases**: Distributed trace anomaly diagnosis, automated root-cause analysis, post-incident summary drafting.
* **Overlap Rules**: Employs agents (Domain 6) operating under strict authorization controls (Principle 7).

---

## 3. Intelligence Patterns

Intelligence patterns describe **how** artificial intelligence reasoning is generated and structured. A single application domain often composes multiple intelligence patterns:

* **Direct Prompting**: Zero-shot or few-shot inference against an instructed model.
* **Structured Generation**: Enforcing JSON Schema or grammar constraints directly during token generation.
* **Retrieval-Augmented Generation (RAG)**: Augmenting prompts with dense vector semantic search results.
* **Hybrid RAG**: Combining dense vector embeddings with sparse keyword search (BM25) and reciprocal rank fusion.
* **GraphRAG**: Leveraging entity-relationship knowledge graphs for multi-hop contextual grounding.
* **Tool Calling**: Generating typed arguments to execute external functions or APIs.
* **ReAct (Reasoning + Acting)**: Alternating steps of reasoning, action execution, and observation.
* **Planning & Decomposition**: Decomposing a high-level goal into an execution plan prior to execution.
* **Multi-Agent Collaboration**: Specialized agent topologies (supervisor-worker, peer debate, voting consensus).
* **Conversational Memory**: Sliding window buffers, hierarchical summarization, and key-value preference stores.
* **Multimodal Reasoning**: Joint token inference across text, images, and audio tokens.

---

## 4. Architecture Patterns

Architecture patterns describe **how software components are organized, scaled, and integrated**:

* **Modular Monolith**: Strongly bounded modules within a single containerized deployable process.
* **Hexagonal Architecture (Ports & Adapters)**: Isolating domain logic from external providers, databases, and frameworks.
* **Event-Driven Architecture (EDA)**: Decoupling asynchronous producers and consumers via event buses or message brokers.
* **Asynchronous Task Workers**: Background job queues handling long-running inference or batch processing.
* **Durable Workflow Orchestration**: Persistent state machines managing step execution, compensations, and timeouts.
* **Real-Time Streaming**: Full-duplex WebSocket or HTTP SSE streaming for chunked token and audio delivery.
* **Human-in-the-Loop (HITL)**: Durable process suspension awaiting human authorization before resumption.

---

## 5. Production Capabilities

Cross-cutting operational qualities required for production deployments:

* **Identity & Access**: Authentication, authorization, Role-Based Access Control (RBAC), API key management.
* **Tenant Isolation**: Database-level and index-level partitioning of vector and conversational state.
* **Resilience**: Timeouts, retries with exponential backoff, circuit breaking, fallback routing, and graceful degradation.
* **Cost & Quota**: Token budgeting, rate limiting, and exact-match/semantic caching.
* **Observability**: Distributed tracing, GenAI semantic spans, token metrics, and latency percentiles.
* **Input/Output Guardrails**: Prompt injection scanning, PII masking, and schema validation.

---

## 6. Governance Capabilities

Repository-level governance practices that ensure architectural rigor:

* **Architecture Decision Records (ADRs)**: Immutable records of significant architectural choices and trade-offs.
* **Quality Gates (A–J)**: Objective release criteria verifying code, architecture, testing, eval, and security.
* **Threat Modeling**: Formal risk assessment against the OWASP Top 10 for LLMs.
* **Phase Review Evidence**: Verifiable completion reports and audit documentation.

---

## 7. Additional Classification Dimensions

When analyzing reference applications, five orthogonal classification dimensions provide additional architectural clarity:

| Dimension | Options / Spectrum | Architectural Significance |
| :--- | :--- | :--- |
| **Autonomy Level** | Advisory $\rightarrow$ Assisted $\rightarrow$ Semi-Autonomous $\rightarrow$ Autonomous within Bounds | Dictates the degree of human oversight, tool sandboxing, and confirmation gates required. |
| **Data Sensitivity** | Public $\rightarrow$ Internal $\rightarrow$ Confidential $\rightarrow$ Regulated (PII/HIPAA) | Determines whether local offline execution (Mode A) is mandatory to prevent egress. |
| **Interaction Mode** | Synchronous $\rightarrow$ Asynchronous $\rightarrow$ Streaming $\rightarrow$ Real-Time $\rightarrow$ Batch | Drives protocol selection (REST, WebSockets, gRPC, Message Queues). |
| **Latency Class** | Sub-second ($< 1\text{s}$) $\rightarrow$ Interactive ($1\text{--}5\text{s}$) $\rightarrow$ Background ($> 5\text{s}$) $\rightarrow$ Batch | Influences model parameter size (SLM vs. LLM) and streaming requirements. |
| **Deployment Mode**| Local / Workstation $\rightarrow$ Edge $\rightarrow$ Private Cloud $\rightarrow$ Public Cloud $\rightarrow$ Hybrid | Defines container topology, hardware requirements, and networking boundaries. |
