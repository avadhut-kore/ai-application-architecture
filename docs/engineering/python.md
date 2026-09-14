# Python Engineering Standard

## 1. Baseline Runtime & Tooling Strategy

Python is the repository's **primary language for AI-native services, RAG pipelines, agent loops, and evaluation harnesses**.

* **Runtime Baseline**: **Python 3.11+** (leveraging substantial runtime performance improvements, exception groups, and enhanced typing).
* **Package & Environment Manager**: **`uv`** (or standard `venv` + `pip-tools`).
  * *Rationale for `uv`*: Extremely fast deterministic dependency resolution, native lockfile support, and hermetic virtual environment creation.
* **Linter & Formatter**: **`ruff`**.
  * *Rationale for `ruff`*: Consolidates Flake8, Black, isort, and Bandit rules into a single high-performance tool.
* **Static Type Checker**: **`mypy`** configured in strict mode (`--strict`).
* **Test Runner**: **`pytest`** with `pytest-asyncio` and `pytest-cov`.

---

## 2. Project Organization & Packaging

Every Python reference application in `apps/` must use a clean standard packaging layout:

```text
apps/<app-name>/
├── pyproject.toml              # Project dependencies, tool configuration (ruff, mypy, pytest)
├── uv.lock                     # Deterministic lockfile (ensures identical builds)
├── .env.example                # Configuration template (zero secrets)
│
├── src/
│   └── app_name/               # Top-level importable Python package
│       ├── __init__.py
│       ├── domain/             # Entities, value objects, domain exceptions
│       ├── application/        # Use cases, ports, workflow orchestrators
│       └── infrastructure/     # Adapters: Ollama client, PostgreSQL repo, FastAPI
│
├── tests/
│   ├── conftest.py             # Shared fixtures and mock providers
│   ├── unit/                   # Fast, deterministic unit tests (mock doubles)
│   └── integration/            # Container and local provider integration tests
│
└── eval/                       # Continuous AI Evaluation
    ├── eval_dataset.jsonl      # Versioned benchmark scenarios
    └── eval_runner.py          # Automated evaluation scoring script
```

---

## 3. Strict Type Hinting & Validation

### 3.1 Strict Typing with Mypy
* All functions, methods, and module interfaces must specify type annotations for all parameters and return types.
* `mypy` strict mode must be enabled in `pyproject.toml`:
  ```toml
  [tool.mypy]
  python_version = "3.11"
  strict = true
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = true
  ```

### 3.2 Runtime Schema Enforcement with Pydantic v2
* All structured external inputs (HTTP requests, environment settings, and **AI model structured responses**) must be validated using **Pydantic v2** models.
* Use `model_config = ConfigDict(frozen=True, extra="forbid")` on DTOs and value objects to enforce immutability and prevent unexpected payload pollution:
  ```python
  from pydantic import BaseModel, ConfigDict, Field

  class ExtractInvoiceResponse(BaseModel):
      model_config = ConfigDict(frozen=True, extra="forbid")

      invoice_number: str = Field(..., min_length=1)
      total_amount: float = Field(..., gt=0.0)
      currency: str = Field(..., pattern=r"^[A-Z]{3}$")
  ```

---

## 4. Asynchronous Programming Standards

* All I/O-bound operations (LLM provider requests, database queries, vector similarity searches, external HTTP calls) must use native Python `asyncio`.
* Avoid blocking operations in async contexts:
  * Do **not** use `time.sleep()`; use `asyncio.sleep()`.
  * Do **not** use standard `requests`; use `httpx.AsyncClient` or `aiohttp`.
* Always pass explicit timeouts to network clients to prevent worker thread hang:
  ```python
  async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=5.0)) as client:
      response = await client.post(...)
  ```

---

## 5. Configuration & Secrets Management

* Use `pydantic-settings` (`BaseSettings`) for application configuration.
* All configuration must be loaded from environment variables and validated at startup.
* Never commit `.env` files or API keys.

---

## 6. Error Handling & Custom Exceptions

* Define an explicit domain exception hierarchy inheriting from a common base:
  ```python
  class AppBaseException(Exception):
      """Base exception for all application domain errors."""

  class SchemaValidationError(AppBaseException):
      """Raised when model output fails structural validation."""

  class ProviderUnavailableError(AppBaseException):
      """Raised when upstream AI provider is unreachable or times out."""
  ```
* Never write bare `except:` or `except Exception: pass`. Always log the exception context or re-raise.

---

## 7. Testing Standards

* **Unit Tests (`tests/unit/`)**:
  * Must be deterministic, isolated, and fast ($< 5\text{ seconds}$ for the entire unit suite).
  * Must use mock test doubles for `ILlmClient` and database repositories.
* **Integration Tests (`tests/integration/`)**:
  * Verify real serialization and HTTP interactions against local Ollama and local databases.
* **AI Evaluations (`eval/`)**:
  * Run against real local models using `eval_dataset.jsonl`.
