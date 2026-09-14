# Configuration Architecture & Standards

This document establishes the configuration hierarchy, environment management, and startup validation standards across the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Authoritative Baseline**  
> Configuration standards in this document satisfy [`Gate B (Code Quality & Type Safety)`](../../QUALITY-GATES.md#gate-b--code-quality--type-safety) and [`Gate J (Production Readiness & Resilience)`](../../QUALITY-GATES.md#gate-j--production-readiness--resilience) in [`QUALITY-GATES.md`](../../QUALITY-GATES.md). All reference applications must strictly separate code, configuration, secrets, and prompts.

---

## 1. Twelve-Factor Configuration Hierarchy

In compliance with Twelve-Factor App principles, application code must remain strictly independent of the environment in which it executes. The repository enforces a layered configuration precedence hierarchy:

```
┌────────────────────────────────────────────────────────┐
│ 1. Command-Line Flags (Highest Precedence - Runtime)   │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 2. Operating System Environment Variables              │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 3. Local Environment File (.env - Local Dev Only)      │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 4. Base Configuration File (appsettings.json / config)  │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│ 5. Safe Embedded Defaults (Lowest Precedence)          │
└────────────────────────────────────────────────────────┘
```

---

## 2. Separation of Concerns: Code, Config, Secrets, and Prompts

Applications must clearly distinguish between four distinct categories of application data:

| Category | Definition & Examples | Storage & Lifecycle | Version Control Policy |
| :--- | :--- | :--- | :--- |
| **Code** | Application logic, routing, domain rules, state machines. | Source files (`.cs`, `.py`, `.ts`, `.java`). | Committed to Git. |
| **Configuration** | Model names, temperature, port numbers, timeouts, batch sizes, feature toggles. | `appsettings.json`, YAML files, environment variables. | Committed as safe defaults; overridden per environment. |
| **Secrets** | API keys, database credentials, OAuth client secrets, encryption keys. | Environment variables, Secret Store, Vault. | **Strictly Forbidden in Git**. Managed via `.env.example`. |
| **Prompts** | System prompts, few-shot examples, prompt templates. | External template files (`.txt`, `.j2`, `.mustache`) or versioned prompt registries. | Committed and version-controlled with change history. |

---

## 3. Strongly Typed Configuration & Startup Validation (Fail-Fast)

Applications must never access raw, unvalidated string keys from environment variables deep inside business logic (e.g., `os.getenv("MODEL_NAME")` scattered throughout the codebase).

### Startup Validation Rule
All configuration values must be bound to strongly typed models and validated at application startup. If any required configuration is missing, malformed, or out of range, the application must **fail fast and terminate immediately** with an explicit error message detailing what is missing.

### Idiomatic Implementation Standards

#### Python (Pydantic `BaseSettings`)
```python
from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", pattern=r"^(development|staging|production)$")
    ollama_endpoint: HttpUrl = Field(default="http://localhost:11434")
    model_name: str = Field(default="llama3.2:3b", min_length=1)
    inference_timeout_seconds: int = Field(default=30, gt=0, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
```

#### .NET (Options Pattern with DataAnnotations)
```csharp
public sealed class LlmOptions
{
    public const string SectionName = "Llm";

    [Required]
    public Uri Endpoint { get; init; } = new("http://localhost:11434");

    [Required, MinLength(1)]
    public string ModelName { get; init; } = "llama3.2:3b";

    [Range(1, 300)]
    public int TimeoutSeconds { get; init; } = 30;
}

// In Program.cs:
builder.Services.AddOptions<LlmOptions>()
    .BindConfiguration(LlmOptions.SectionName)
    .ValidateDataAnnotations()
    .ValidateOnStart(); // Fail fast on startup
```

#### TypeScript (Zod Environment Schema)
```typescript
import { z } from "zod";

const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  OLLAMA_ENDPOINT: z.string().url().default("http://localhost:11434"),
  MODEL_NAME: z.string().min(1).default("llama3.2:3b"),
  TIMEOUT_SECONDS: z.coerce.number().int().positive().max(300).default(30),
});

export const config = EnvSchema.parse(process.env);
```

---

## 4. Sensitive Value Masking & Operational Logging

* **Zero Secret Logging**:
  * Logging frameworks must never output raw configuration dumps that contain API keys, passwords, or Authorization header values.
  * Implement redacting formatters or configuration sanitizers that replace sensitive values with `***REDACTED***` or display only the last 4 characters (`...abcd`).
* **Health Check Masking**:
  * Diagnostics and health-check endpoints (`/health`, `/healthz`, `/metrics`) must report service status (UP/DOWN, latency) without exposing connection strings or credentials.

---

## 5. Standard Environment Template (`.env.example`)

Every reference application and runnable component must provide a documented `.env.example` in its root folder:

```bash
# ==============================================================================
# AI Application Architecture Configuration Template
# Copy this file to .env and adjust values for your local environment.
# ==============================================================================

# Environment Mode: development | staging | production
APP_ENV=development

# Local-First Execution Mode per docs/architecture/local-first.md:
# mode-a (Offline Local) | mode-b (Local-First, default) | mode-c (Cloud-Comparable)
# Note: In-memory test doubles belong to automated unit tests, not runtime execution modes.
AI_EXECUTION_MODE=mode-b

# Local Ollama Configuration (Mode A)
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama3.2:3b
OLLAMA_TIMEOUT_SECONDS=30

# Cloud Fallback Configuration (Optional - for Mode C)
# CLOUD_AI_API_KEY=your-api-key-here
# CLOUD_AI_MODEL=gpt-4o-mini
```
