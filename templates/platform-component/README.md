# Tier 3 Platform Component: [Component Name]

> **Tier Classification**: **Tier 3 — Platform Component**  
> **Component Role**: [e.g. Inbound Adapter / Telemetry Middleware / Evaluation Runner / Core Port]  
> **Target Ecosystem**: [e.g. Python / .NET / Polyglot Platform]  
> **Status**: Planned / Implemented / Validated  

---

## 1. Responsibility & Bounded Scope

* **Purpose**: Define the specific technical capability provided by this component.
* **Supported Behavior**: Explicitly list capabilities within scope.
* **Unsupported Behavior**: Explicitly list what this component does *not* do (anti-framework boundary).
* **Reuse Justification**: Explain why this capability is factored into a shared building block or platform tool rather than duplicated across applications.

---

## 2. Public Contracts & Interface Specification

Document the public interfaces, protocols, or ports exposed to consuming applications:

```python
# Provide concrete interface or protocol definition
class TargetPort(Protocol):
    async def execute(self, payload: RequestType) -> ResponseType: ...
```

---

## 3. Integration Guide & Usage Example

Demonstrate how a consuming application imports and configures the component:

```python
from building_blocks.[package] import ConcreteComponent

# Example initialization and usage
component = ConcreteComponent(config)
result = await component.execute(payload)
```

---

## 4. Failure Modes & Error Taxonomy

Document all explicit exceptions raised by this component:

| Exception Class | Error Code | Transient? | Trigger Condition | Recommended Recovery |
| :--- | :--- | :---: | :--- | :--- |
| `ComponentError` | `COMPONENT_BASE` | No | Base exception for component domain. | Log and fail fast. |
| `ComponentTransientError` | `COMPONENT_TIMEOUT` | Yes | Network timeout or provider unavailable. | Retry with exponential backoff. |

---

## 5. Security & Observability Considerations

* **Security Boundaries**: How secrets, sensitive payloads, or untrusted inputs are handled.
* **Observability**: Tracing spans created, metrics emitted, and OpenTelemetry GenAI semantic conventions applied.

---

## 6. Testing Strategy

* **Unit Tests**: Coverage of normal, edge, and error conditions using test doubles.
* **Verification Command**:
```bash
[test-command]
```

---

## 7. Quality Gate Checklist (Scaled for Tier 3)

Per [QUALITY-GATES.md](../../QUALITY-GATES.md):
- [ ] **Gate A (Architecture & Boundaries)**: Inward dependency direction maintained; zero reverse dependencies on apps.
- [ ] **Gate B (Local-First)**: Operates without unneeded third-party cloud dependencies.
- [ ] **Gate C (Software Quality)**: Unit tests verify all failure modes and contract behaviors.
- [ ] **Gate F (Observability)**: Telemetry context propagated where component manages runtime invocations.
- [ ] **Gate H (API & Documentation)**: Stable, documented public contracts with clean type annotations.
