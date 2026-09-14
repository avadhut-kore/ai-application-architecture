# Java & Spring Boot Engineering Standards

This document defines mandatory engineering standards, idiom guidelines, and operational constraints for Java implementations in the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Secondary Enterprise Language Status & Applicability**  
> Apply these standards when Java is selected for a concrete implementation. As established in [`docs/architecture/language-strategy.md`](../architecture/language-strategy.md), Java is an **approved secondary enterprise language**. Java implementations are created **only where JVM enterprise architectural value is demonstrated** (such as Spring Boot enterprise service integrations, event-driven streaming with Kafka, or legacy enterprise core modernisation). Universal translation of all reference applications into Java is deliberately avoided to prevent maintenance bloat.

---

## 1. Runtime Baseline & Tooling

| Concern | Mandatory Standard |
| :--- | :--- |
| **Java Baseline** | Java 21 LTS (Oracle OpenJDK, Eclipse Temurin, or Amazon Corretto). |
| **Framework Baseline** | Spring Boot 3.x+ with Java 21 language features (records, pattern matching, virtual threads). |
| **Build Tool** | Gradle 8.x+ (Kotlin DSL preferred) or Maven 3.9+ with strict wrapper scripts (`gradlew` or `mvnw`). |
| **Dependency Management** | Dependency locking enabled (`dependency-locking` in Gradle or `versions-maven-plugin` with lockfiles). |
| **Static Analysis** | Spotless (formatting), Checkstyle (rules), Error Prone, and Sonar/SpotBugs in CI. |
| **AI Integration** | Spring AI 1.0+ or native REST/HTTP clients for local Ollama/OpenAI-compatible endpoints. |

---

## 2. Idiomatic Java 21 & Code Style

* **Use Modern Language Features**:
  * Prefer `record` types for immutable Data Transfer Objects (DTOs), command objects, and API payloads:
    ```java
    public record ExtractEntityRequest(
        @NotBlank(message = "Document text is required")
        String documentText,
        @NotEmpty(message = "Entity types list must not be empty")
        List<String> entityTypes
    ) {}
    ```
  * Leverage pattern matching for `switch` and `instanceof` to eliminate redundant casting.
  * Use text blocks (`"""`) for structured prompts and documentation fixtures.
* **Virtual Threads (Project Loom)**:
  * For Spring Boot 3.2+, enable virtual threads for synchronous web request dispatching and non-blocking I/O:
    ```yaml
    spring:
      threads:
        virtual:
          enabled: true
    ```
  * Avoid thread-local state leakage and thread pooling when virtual threads are active. Do not pool virtual threads.
* **Null Safety**:
  * Use `@NonNull` and `@Nullable` annotations (`jakarta.annotation` or `org.springframework.lang`).
  * Never return `null` for collections; return `Collections.emptyList()` or `List.of()`.
  * Use `Optional<T>` strictly as a return type for methods that may return no result; do not use `Optional<T>` as method parameters or field types.

---

## 3. Architecture & Dependency Injection

* **Constructor Injection Only**:
  * Field injection (`@Autowired` on private fields) is strictly forbidden. It prevents unit testing without reflection and hides dependency coupling.
  * Use constructor injection with `final` fields, optionally assisted by Lombok's `@RequiredArgsConstructor`:
    ```java
    @Service
    public class DefaultDocumentClassifier implements DocumentClassifier {

        private final LlmInferencePort inferencePort;
        private final ClassificationMetricsPort metricsPort;

        public DefaultDocumentClassifier(
            LlmInferencePort inferencePort,
            ClassificationMetricsPort metricsPort
        ) {
            this.inferencePort = Objects.requireNonNull(inferencePort, "inferencePort must not be null");
            this.metricsPort = Objects.requireNonNull(metricsPort, "metricsPort must not be null");
        }
    }
    ```
* **Ports and Adapters Boundaries**:
  * Core domain entities and use cases must not import Spring web, JPA, or vendor-specific AI client packages.
  * Interface definitions (ports) reside in the application or domain module; adapters (`SpringAiAdapter`, `JpaRepositoryAdapter`) reside in the infrastructure module.

---

## 4. Input Validation & Exception Handling

* **Bean Validation**:
  * Validate all external incoming DTOs using `jakarta.validation.constraints` (`@Valid`, `@NotNull`, `@Size`, `@Pattern`).
  * Fail fast at controller entry points before passing payloads into domain services.
* **Domain Exception Hierarchy**:
  * Define explicit checked or unchecked domain exceptions rooted in a base class (e.g., `AiArchitectureDomainException`).
  * Never swallow exceptions. Log with context or wrap with custom domain exceptions preserving root cause.
* **RFC 7807 / RFC 9457 Problem Details**:
  * Implement centralized exception handling using `@RestControllerAdvice` returning `ProblemDetail`:
    ```java
    @RestControllerAdvice
    public class GlobalExceptionHandler {

        @ExceptionHandler(ModelTimeoutException.class)
        public ProblemDetail handleModelTimeout(ModelTimeoutException ex) {
            ProblemDetail problem = ProblemDetail.forStatusAndDetail(
                HttpStatus.GATEWAY_TIMEOUT,
                ex.getMessage()
            );
            problem.setTitle("AI Inference Timeout");
            problem.setProperty("timestamp", Instant.now());
            return problem;
        }
    }
    ```

---

## 5. Persistence & Transactions (JPA / Relational)

* **Explicit Transaction Boundaries**:
  * Annotate service-layer entry points with `@Transactional(readOnly = true)` by default, overriding with `@Transactional` on write operations.
  * Never place `@Transactional` on repository interfaces or controller endpoints.
* **Avoid N+1 Queries**:
  * Use JOIN FETCH queries or Entity Graphs (`@NamedEntityGraph`) when loading entity relationships.
  * Validate persistence performance using query logging or datasource assertion proxies in tests.
* **Database Migrations**:
  * All database schema changes must be version-controlled using Flyway or Liquibase migrations (`src/main/resources/db/migration`).
  * Hibernate `ddl-auto` must be set to `validate` or `none` in production configurations; never `update` or `create-drop`.

---

## 6. Testing & Quality Verification

* **Unit Testing**:
  * Use **JUnit 5** (`org.junit.jupiter.api.*`) and **AssertJ** for fluent, readable assertions.
  * Use **Mockito** (`org.mockito`) strictly for external boundaries (e.g., HTTP clients, remote inference ports).
* **Integration Testing with Testcontainers**:
  * Test persistence and messaging adapters against real containerized services (PostgreSQL, Redis, Kafka, Ollama) using Testcontainers:
    ```java
    @Testcontainers
    @SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
    class DocumentStoreIntegrationTest {

        @Container
        static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

        @DynamicPropertySource
        static void configureProperties(DynamicPropertyRegistry registry) {
            registry.add("spring.datasource.url", postgres::getJdbcUrl);
            registry.add("spring.datasource.username", postgres::getUsername);
            registry.add("spring.datasource.password", postgres::getPassword);
        }
    }
    ```
* **AI Evaluation Tests**:
  * Deterministic assertions verify API contracts, JSON parsing, and fallbacks.
  * Non-deterministic evaluation suites evaluate generation accuracy, grounding, and latency against `eval_dataset.jsonl` using automated scoring runners.

---

## 7. Anti-Patterns & Prohibitions

1. **No `@Autowired` Field Injection**: Always use constructor injection.
2. **No Unbounded Reactive Monoliths**: If reactive programming (Project Reactor/WebFlux) is used, ensure backpressure is bounded and thread transitions do not leak contexts. Prefer Java 21 virtual threads with standard synchronous Spring MVC unless reactive streaming is strictly required.
3. **No Catch-All Swallowing**: Never write `catch (Exception e) {}` or `catch (Throwable t) {}` without logging or rethrowing.
4. **No Schema Auto-Creation in Production**: Never use `hibernate.hbm2ddl.auto = update`.
5. **No Speculative Universal Ports**: Do not implement a Java version of an existing Python or .NET application unless it provides distinct JVM architectural or enterprise integration demonstration value.
