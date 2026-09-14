# ADR-NNNN: [Short, Imperative Title of Decision]

* **Status**: [Proposed | Accepted | Rejected | Superseded | Deprecated]
* **Deciders**: [List of architects, engineers, stakeholders]
* **Date**: [YYYY-MM-DD]
* **Technical Story**: [Link to issue, roadmap phase, or architectural initiative]
* **Supersedes**: [ADR-XXXX if applicable, otherwise N/A]
* **Superseded By**: [ADR-YYYY if applicable, otherwise N/A]

---

## 1. Context

[Describe the business, architectural, or organizational context in which this decision is being made. What system, application, or platform component is affected?]

---

## 2. Problem Statement

[What specific technical or architectural problem needs to be resolved? What functional or non-functional requirements (NFRs) must be satisfied?]

---

## 3. Decision Drivers

* [Driver 1, e.g., Local-first execution feasibility under Mode A or B]
* [Driver 2, e.g., Strict provider decoupling from vendor SDKs]
* [Driver 3, e.g., Latency budget of < 1.5s time-to-first-token]
* [Driver 4, e.g., OpenTelemetry GenAI semantic tracing support]
* [Driver 5, e.g., Workstation memory constraint on 16GB machines]

---

## 4. Options Considered

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

## 5. Decision Outcome

**Chosen Option**: **Option [X]: [Option Name]**

### Rationale
[Explain why this option was chosen. How does it satisfy the decision drivers? Why is it superior to the alternatives for this specific context?]

### Architectural Implementation Details
[Describe key structural aspects, interfaces, ports, or adapters that will be introduced as part of executing this decision.]

---

## 6. Consequences

### Positive Consequences
* [Benefit 1]
* [Benefit 2]

### Negative Consequences & Trade-offs
* [Trade-off 1 and how it will be managed]
* [Trade-off 2 and how it will be managed]

### Neutral / Operational Consequences
* [Operational impact 1]
* [Maintenance or tooling impact 2]

---

## 7. Risks & Mitigations

* **[Risk 1]**: [Description of technical or operational risk]
  * *Mitigation*: [Concrete action or architectural constraint that mitigates this risk]
* **[Risk 2]**: [Description of technical or operational risk]
  * *Mitigation*: [Concrete action or architectural constraint that mitigates this risk]

---

## 8. Alternatives Rejected & Why

* **[Option A]**: Rejected because [concrete technical reason, e.g., tight coupling to proprietary vendor SDK, incompatible with local Ollama runtime].
* **[Option B]**: Rejected because [concrete technical reason, e.g., excessive operational complexity, unmaintained library, missing type safety].

---

## 9. Compliance with Architectural Principles

Verify alignment with [docs/architecture/principles.md](../docs/architecture/principles.md):

* **Principle 1 (Untrusted Model Output)**: [Compliant | N/A - Explain]
* **Principle 2 (Deterministic Rules)**: [Compliant | N/A - Explain]
* **Principle 3 (Provider Decoupling)**: [Compliant | N/A - Explain]
* **Principle 4 (Conditional Gateway)**: [Compliant | N/A - Explain]
* **Principle 9 (Observability)**: [Compliant | N/A - Explain]
