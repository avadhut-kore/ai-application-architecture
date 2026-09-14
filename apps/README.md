# Applications (`apps/`)

## Architectural Boundary & Isolation Governance

This directory contains standalone, production-grade AI reference applications.

### Architectural Directives

1. **Complete Isolation**: Each application in `apps/` is an independent system with its own packaging, dependency manifest (`pyproject.toml`, `package.json`, or `.csproj`), test suite, Dockerfile, and evaluation harness.
2. **No Cross-Application Coupling**: An application in `apps/<app-a>` must **never** import or depend upon code in `apps/<app-b>`.
3. **Allowed Dependencies**:
   * An application may consume shared contracts or utilities from `building-blocks/`.
   * An application may utilize platform automation scripts from `platform/` or `scripts/`.
4. **Independent Verifiability**: Every application must be independently buildable, testable, and runnable locally under Mode A (Offline Local) or Mode B (Local-First).
