# Enterprise AI Security Standards

This document establishes the threat modeling principles, security architecture, and operational safeguards across all implementations in the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Security controls defined here satisfy [`Gate E (Security & Safety)`](../../QUALITY-GATES.md#gate-e--security--safety) in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). In AI systems, software boundaries and probabilistic boundaries must both be hardened. Model outputs must be treated as untrusted user input.

---

## 1. Threat Modeling & Untrusted Boundaries

Enterprise AI applications operate across four distinct untrusted boundaries:

```
┌─────────────────────┐
│ 1. External User    │ ──► [Direct Prompt Injection / Jailbreak / Malformed Input]
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Retrieval / Web  │ ──► [Indirect Prompt Injection / Data Poisoning / SSRF]
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ 3. LLM / Generative │ ──► [Hallucination / Prompt Leakage / Unsafe Tool Calling]
└─────────────────────┘
           │
           ▼
┌─────────────────────┐
│ 4. Execution / DB   │ ──► [SQL Injection / Unauthorized State Mutation / Shell Exec]
└─────────────────────┘
```

### Core Security Axioms
1. **Model Output is Untrusted Input**: Never pass LLM output directly into database queries, operating system shells, dynamic code execution engines (`eval()`), or raw HTML renderers without strict schema validation and sanitization.
2. **Retrieved Context is Untrusted Input**: Ingested third-party documents, emails, scraped web pages, and user files may contain indirect prompt injections designed to hijack model instructions.
3. **System Prompts are Public by Default**: Never rely on system prompts or instructions to protect confidential secrets, API keys, or security authorization logic.

---

## 2. OWASP Top 10 for LLM Applications Matrix

All reference architectures must address the OWASP Top 10 for LLM Applications:

| Vulnerability | Repository Threat Profile | Enforced Mitigation |
| :--- | :--- | :--- |
| **LLM01: Prompt Injection** | User or retrieved content overrides system guidance to execute unintended actions. | Delimiter isolation (XML/Markdown tags), structural schema enforcement, input guardrails, and refusal testing in eval suite. |
| **LLM02: Sensitive Information Disclosure** | Model regurgitates confidential data, PII, or internal credentials in responses. | Output regex scrubbers, PII anonymization before inference, strict context filtering, and no secrets in prompts. |
| **LLM03: Supply Chain Vulnerabilities** | Compromised base models, embedding models, or third-party orchestration packages. | Software Bill of Materials (SBOM), pinned package hashes, audited package manifests, and CVE vulnerability scanning. |
| **LLM04: Data & Model Poisoning** | Malicious content embedded in knowledge stores or vector embeddings to manipulate answers. | Ingestion integrity checks, authenticated ingestion pipelines, and provenance metadata tracking. |
| **LLM05: Improper Output Handling** | Downstream systems blindly trust LLM output, enabling XSS, SQLi, or command execution. | Strict Pydantic/Zod/C# record parsing, parameterized queries, and context-aware HTML escaping. |
| **LLM06: Excessive Agency** | Agent possesses open-ended tool access or executes destructive actions autonomously. | Principle of Least Privilege, human-in-the-loop (HITL) gates for state mutations, and fine-grained tool authorization. |
| **LLM07: System Prompt Leakage** | Attackers extract internal system architecture, prompts, and business logic. | Architecture designed assuming prompts are accessible; no proprietary trade secrets stored inside prompts. |
| **LLM08: Vector & Embedding Weaknesses** | Exploitation of vector similarity search to bypass access control or inject adversarial embeddings. | Tenant isolation in vector indices, row-level security (RLS) on document metadata, and embedding dimension validation. |
| **LLM09: Misinformation & Hallucination** | System presents fabricated facts as authoritative enterprise truth. | Grounded RAG architecture with citation enforcement, hallucination metric gating (Gate D Faithfulness ≥ 0.85, recommended target ≥ 0.90), and clear confidence disclaimers. |
| **LLM10: Unbounded Consumption** | Resource exhaustion, token denial-of-service, or cost spikes from looping queries. | Hard token limits per request, request rate limiting, maximum loop counters in agents, and streaming timeouts. |

---

## 3. Principle of Least Privilege for AI Agents & Tools

AI agents must never receive unrestricted execution capabilities:

* **Read-Only by Default**: Tools exposed to agents must be read-only unless the specific use case requires state modification.
* **Granular Scoping**: An agent tasked with searching customer records must not have access to financial ledger modification tools or system administrative tools.
* **Human-in-the-Loop (HITL) for High-Impact Actions**:
  * Any tool action that mutates persistent state, deletes data, transfers financial funds, or sends external communications must require explicit human confirmation.
  * The agent proposes a draft action with structured parameters; execution occurs only after an authenticated user approves the proposal.
* **Strict Tool Parameter Schemas**:
  * Tool arguments must be strictly typed and validated using Pydantic, Zod, or C# strong typing before the underlying business logic executes.

---

## 4. Secrets Management & Zero-Leakage Policy

* **Zero Hardcoded Secrets**:
  * API keys, tokens, database passwords, and private certificates must never be committed to source code or documentation.
  * Use `.env.example` templates with empty or placeholder values (`sk-proj-PLACEHOLDER_KEY`).
* **Automated Secret Scanning**:
  * CI pipelines and pre-commit hooks must run automated scanners (e.g., `git-secrets`, `trufflehog`, or GitHub secret scanning) before changes merge.
* **Environment Variable Resolution**:
  * Secrets must be loaded from operating system environment variables or secure enterprise vaults (e.g., Azure Key Vault, AWS Secrets Manager, HashiCorp Vault).

---

## 5. Input Sanitization & Output Encoding

* **Input Sanitization**:
  * Strip null bytes, unprintable control characters, and excessively long inputs before dispatching prompts to LLM engines.
  * For tool-assisted retrieval, sanitize URLs against Server-Side Request Forgery (SSRF): block private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.1`, `169.254.169.254`).
* **Output Encoding & Sanitization**:
  * When rendering LLM markdown responses in web interfaces, parse markdown using secure AST parsers that sanitize HTML tags and disallow raw `<script>` or `javascript:` URI schemes.
  * SQL statements generated by AI must never be executed directly. Use read-only query builders or enforce strict schema parameterization.
