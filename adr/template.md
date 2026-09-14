# ADR-NNNN: [Short, Imperative Title of Decision]

* **Status**: [Proposed | Accepted | Rejected | Superseded | Deprecated]
* **Deciders**: [List of architects, engineers, stakeholders]
* **Date**: [YYYY-MM-DD]
* **Technical Story**: [Link to issue, roadmap phase, or architectural initiative]
* **Supersedes**: [ADR-XXXX if applicable, otherwise N/A]
* **Superseded By**: [ADR-YYYY if applicable, otherwise N/A]

---

## 1. Context and Problem Statement

[Describe the context and problem being addressed. What situation requires an architectural decision? What business, functional, or non-functional requirements must be satisfied? Keep this objective and grounded in facts.]

---

## 2. Decision Drivers

* [Driver 1, e.g., Local development requirement without cloud API keys]
* [Driver 2, e.g., Strict vendor portability across cloud providers]
* [Driver 3, e.g., Latency requirement of < 500ms time-to-first-token]
* [Driver 4, e.g., OpenTelemetry semantic tracing compatibility]
* [Driver 5, e.g., Memory and hardware constraints on developer workstations]

---

## 3. Options Considered

### Option 1: [Option Name]
* **Description**: [Brief summary of option 1]
* **Pros**:
  * [Advantage 1]
  * [Advantage 2]
* **Cons**:
  * [Disadvantage 1]
  * [Disadvantage 2]

### Option 2: [Option Name]
* **Description**: [Brief summary of option 2]
* **Pros**:
  * [Advantage 1]
  * [Advantage 2]
* **Cons**:
  * [Disadvantage 1]
  * [Disadvantage 2]

### Option 3: [Option Name]
* **Description**: [Brief summary of option 3]
* **Pros**:
  * [Advantage 1]
  * [Advantage 2]
* **Cons**:
  * [Disadvantage 1]
  * [Disadvantage 2]

---

## 4. Decision Outcome

**Chosen Option**: **Option [X]: [Option Name]**

### Positive Rationale
[Explain why this option was chosen. How does it satisfy the decision drivers? Why is it superior to the alternatives for this specific context?]

### Architectural Implementation Details
[Describe key structural aspects, interfaces, dependencies, or patterns that will be applied as part of executing this decision.]

---

## 5. Consequences

### Positive Consequences
* [Benefit 1]
* [Benefit 2]

### Negative Consequences & Trade-offs (Mitigations Required)
* [Trade-off 1: Mitigation strategy]
* [Trade-off 2: Mitigation strategy]

### Neutral / Operational Consequences
* [Operational impact 1]
* [Tooling or maintenance impact 2]

---

## 6. Alternatives Rejected & Why

* **[Option A]**: Rejected because [concrete technical reason, e.g., incompatible with local execution, tight vendor coupling, lack of async support].
* **[Option B]**: Rejected because [concrete technical reason, e.g., excessive operational overhead, licensing restrictions, immature community support].

---

## 7. Compliance with Architectural Principles

Verify alignment with [docs/architecture/architecture-principles.md](../docs/architecture/architecture-principles.md):

* **Principle 1 (Untrusted LLM Output)**: [Compliant | N/A - Explain]
* **Principle 3 (Provider Abstraction)**: [Compliant | N/A - Explain]
* **Principle 4 (Deterministic Logic)**: [Compliant | N/A - Explain]
* **Principle 12 (Observability)**: [Compliant | N/A - Explain]
* **Principle 15 (Local-First Parity)**: [Compliant | N/A - Explain]
