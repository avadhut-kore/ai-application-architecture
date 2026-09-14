# Building Blocks: Python AI Contracts

This package contains the bounded, vendor-agnostic minimum core contracts for enterprise AI reference implementations in the `ai-application-architecture` repository.

## Design Principles

1. **Zero External Runtime Dependencies**: Implemented strictly using standard library typing, dataclasses, and enums.
2. **Strict Type Safety**: Fully compatible with `mypy --strict`.
3. **OpenTelemetry Semantic Conventions**: Telemetry context adheres to OpenTelemetry GenAI standards.
4. **Bounded Exception Taxonomy**: Distinguishes transient (retriable), non-transient, and semantic AI errors.
5. **Structured Parsing Envelopes**: Type-safe `ValidationResult[T]` for robust structured output extraction.
