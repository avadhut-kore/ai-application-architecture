# ADR-0008: Model Context Protocol as External Capability Adapter

* **Status**: Accepted
* **Deciders**: Principal AI Application Architect, Enterprise Governance Auditor, AI Platform Lead
* **Date**: 2026-09-15
* **Technical Story**: Phase 6 — Agentic Task Execution ([`ROADMAP.md`](../ROADMAP.md#phase-6-agentic-task-execution))
* **Supersedes**: N/A
* **Superseded By**: N/A

---

## 1. Context

As AI systems evolve from isolated generation to connected operational workflows, standard protocols are emerging to interface models with external tools, diagnostic services, and enterprise data sources. The Model Context Protocol (MCP) has emerged as an open standard for standardizing tool discovery and execution via JSON-RPC 2.0 over standard I/O (stdio) or HTTP/SSE transports.

However, adopting external protocols in enterprise architectures introduces severe supply chain, security, and portability risks:
1. External package dependencies (`mcp` SDK) may introduce heavy dependencies or cloud requirements that break local-first (Mode A) offline determinism.
2. Blindly exposing external MCP servers without host-level authorization violates the Separation of Authority principle.

---

## 2. Problem Statement

How should `ai-application-architecture` implement Model Context Protocol integration as a Tier 3 platform component while adhering to zero-dependency local-first rules, provider neutrality, and capability allowlisting?

---

## 3. Decision Drivers

* **Zero Third-Party Dependency Rule**: Core protocol framing and client/server logic must use pure Python standard library (`asyncio`, `json`, `subprocess`).
* **Capability Port Conformance**: MCP tools must project cleanly onto the repository's core `CapabilityPort` interface without exposing transport details to the agent engine.
* **Strict Capability Allowlisting**: The host application must explicitly control which MCP tools are exposed; wildcard or unverified tool discovery is prohibited.
* **Hermetic Testability**: Both in-memory and subprocess stdio transports must be fully testable in offline automated test suites without external background daemons.

---

## 4. Key Architectural Decisions

### 4.1 Pure Standard-Library JSON-RPC 2.0 Implementation
We implement the MCP wire protocol in `platform/mcp-adapter/mcp_adapter/protocol.py` using standard library `json` and `asyncio`:
* Standard JSON-RPC 2.0 message framing (`jsonrpc: "2.0"`, `id`, `method`, `params`, `result`, `error`);
* Support for core MCP methods: `tools/list` (tool discovery) and `tools/call` (tool execution);
* Standardized error codes conforming to JSON-RPC 2.0 specifications.

### 4.2 Decoupled Client Transports
We implement two client transports in `platform/mcp-adapter/mcp_adapter/client.py`:
* `InMemoryMcpClient`: Connects directly to an in-process `McpServer` instance for zero-overhead, hermetic unit testing.
* `StdioMcpClient`: Launches and communicates with an external MCP server process over standard input/output (`stdin`/`stdout`).

### 4.3 Adapter Projection & Capability Allowlisting
The `McpCapabilityAdapter` in `platform/mcp-adapter/mcp_adapter/adapter.py`:
* Connects to the MCP client during initialization and discovers available tools;
* Filters discovered tools against an application-supplied `allowed_capabilities` allowlist;
* Instantiates individual `McpToolCapability` adapters conforming to `CapabilityPort`;
* Preserves JSON schema parameters and maps side-effect levels defensively.

---

## 5. Consequences

### Positive
* 100% offline, hermetic, zero-external-dependency MCP adapter.
* Agent control engines can execute tools provided by external MCP servers using the exact same interface (`CapabilityPort`) as internal Python tools.
* Host application maintains complete control over tool exposure via allowlisting.

### Negative / Trade-offs
* Advanced MCP features such as dynamic server-side notifications and HTTP/SSE transports are deferred to future iterations.
* Tool schema translation is limited to standard JSON-RPC tool declarations.

---

## 6. Compliance with Repository Principles

* **Principle 3 (Modularity & Loose Coupling)**: MCP is implemented as an external adapter at the infrastructure boundary (Tier 3), never coupled into core contracts.
* **Principle 6 (Local-First)**: Fully runnable without cloud services or external servers under Mode A.
* **Principle 13 (Capability Safety)**: Strict allowlist prevents untrusted external tools from entering the capability registry.
