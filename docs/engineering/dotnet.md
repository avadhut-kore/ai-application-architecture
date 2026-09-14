# .NET / C# Engineering Standard

## 1. Baseline Runtime & Language Strategy

* **Runtime Baseline**: **.NET 8 LTS** (or subsequent supported Long-Term Support releases).
* **Language Baseline**: Modern supported C# versions aligned with the host .NET runtime (e.g., C# 12 on .NET 8).
* **Language Conflation Rule**: Never conflate the .NET runtime version with the C# language version. State runtime and language targets explicitly in project files:
  ```xml
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <LangVersion>latest</LangVersion>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <ImplicitUsings>enable</ImplicitUsings>
  </PropertyGroup>
  ```

---

## 2. Project Organization & Architecture

Follow a clean, modern layout avoiding over-engineered layer proliferation:

```text
src/
├── Company.App.Domain/             # Domain entities, value objects, domain exceptions
├── Company.App.Application/        # Use cases, application ports, commands, queries
├── Company.App.Infrastructure/     # Adapters: EF Core, AI model clients, Redis, HTTP
└── Company.App.Api/                # ASP.NET Core Web API, controllers, endpoints
tests/
├── Company.App.UnitTests/          # Fast, hermetic xUnit tests with in-memory doubles
└── Company.App.IntegrationTests/   # WebApplicationFactory + Testcontainers integration tests
```

---

## 3. Type Safety & C# Language Practices

### 3.1 Nullable Reference Types
* Nullable reference types must be enabled globally (`<Nullable>enable</Nullable>`).
* Treat compiler warnings as errors (`<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`).
* Avoid the null-forgiving operator (`!`) except in generated database context code or test fixture initialization.

### 3.2 Immutability with Records
* Prefer `record` and `record struct` for Data Transfer Objects (DTOs), API contracts, domain events, and immutable value objects:
  ```csharp
  public record GenerateCompletionRequest(
      string Prompt,
      double Temperature = 0.2,
      int MaxTokens = 1024);
  ```

### 3.3 Asynchronous Programming & Cancellation
* All I/O operations must be asynchronous, returning `Task` or `ValueTask`.
* **Mandatory Cancellation**: Every asynchronous method must accept and propagate a `CancellationToken`:
  ```csharp
  public async Task<LlmResponse> CompleteAsync(
      LlmPrompt prompt,
      CancellationToken cancellationToken = default)
  ```
* Avoid `async void` entirely (except UI event handlers). Avoid `.Result` or `.Wait()`, which trigger thread-pool starvation.

---

## 4. Dependency Injection & Configuration

### 4.1 Dependency Injection
* Use native Microsoft Dependency Injection (`Microsoft.Extensions.DependencyInjection`).
* Register dependencies using explicit lifecycles:
  * `AddScoped` for database contexts, unit-of-work services, and request-bound use cases.
  * `AddTransient` for lightweight stateless calculators and validators.
  * `AddSingleton` for connection pools, memory caches, and AI model adapters.
* Avoid global service locator patterns (`IServiceProvider.GetService()` in business logic).

### 4.2 Strongly Typed Configuration & Options Pattern
* Use the Options Pattern (`IOptions<T>`, `IOptionsSnapshot<T>`) for strongly typed configuration.
* Validate configuration on startup using data annotations or FluentValidation:
  ```csharp
  builder.Services.AddOptions<AiProviderOptions>()
      .BindConfiguration("AiProvider")
      .ValidateDataAnnotations()
      .ValidateOnStart();
  ```

---

## 5. Resilience & HTTP Clients

### 5.1 Named / Typed HttpClient
* Never instantiate raw `new HttpClient()` in services.
* Use `IHttpClientFactory` with typed clients to avoid socket exhaustion.

### 5.2 Resilience with Polly
* Wrap outbound AI model calls and external HTTP integrations in resilience pipelines using Microsoft.Extensions.Resilience / Polly:
  * Set explicit timeouts on all outbound calls (e.g., 30-second timeout on model completion).
  * Configure retries with exponential backoff and jitter for transient errors (HTTP 429, 503).
  * Configure circuit breaking to prevent cascading failures during extended provider outages.

---

## 6. Persistence & Data Access Boundaries

* **No Dogmatic EF Core Mandate**: Entity Framework Core is a solid default for relational persistence, but is not mandatory. Dapper or direct ADO.NET is encouraged when raw performance or complex SQL queries justify it.
* **No Redundant Repository Wrappers**: Do not build generic `IRepository<T>` abstractions over EF Core `DbContext` unless multi-database swapping is an explicit architectural requirement. EF Core `DbSet<T>` already implements the repository pattern.
* **Transactions**: Use execution strategies (`IExecutionStrategy`) and explicit transactions for multi-entity transactional boundaries.

---

## 7. Error Handling & Structured Logging

* **No Bare Catch Blocks**: Never catch raw `Exception` without rethrowing or translating into a domain exception.
* **Structured Logging**: Use `ILogger<T>` with high-performance LoggerMessage source generators or semantic templates:
  ```csharp
  [LoggerMessage(EventId = 101, Level = LogLevel.Information, Message = "Model {ModelName} completed in {ElapsedMs}ms with {TotalTokens} tokens.")]
  public static partial void LogModelCompletion(ILogger logger, string modelName, long elapsedMs, int totalTokens);
  ```
* **No PII in Logs**: Never log unredacted customer prompts, API keys, or personal identifiers.

---

## 8. Testing & Static Analysis

* **Unit Testing**: Use `xUnit` with `FluentAssertions` and `NSubstitute` (or `Moq`).
* **Integration Testing**: Use `Microsoft.AspNetCore.Mvc.Testing.WebApplicationFactory<T>` with `Testcontainers` for PostgreSQL/Redis where feasible.
* **Formatting & Analyzers**: Enforce `dotnet format --verify-no-changes` and security analyzers (`Microsoft.CodeAnalysis.NetAnalyzers`) in CI.
