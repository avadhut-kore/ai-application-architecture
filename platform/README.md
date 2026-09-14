# Platform Tooling & Infrastructure (`platform/`)

## Architectural Boundary & Governance

This directory contains repository-wide developer platform tooling, local inference runtime provisioning scripts, and shared infrastructure definitions.

### Architectural Directives

1. **Scope**:
   * Local inference provisioning (e.g. Ollama setup, model pull orchestration).
   * Shared continuous evaluation harness runners.
   * Container orchestration and dev container definitions.
2. **Isolation**: Platform tooling must not embed application-specific business logic or domain entities.
3. **Reproducibility**: All platform scripts must be deterministic, cross-platform compatible, and executable in air-gapped or restricted CI environments.
