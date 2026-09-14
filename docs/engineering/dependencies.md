# Third-Party Dependency Governance

This document establishes the dependency evaluation framework, package management rules, license compliance policies, and vulnerability scanning standards for the `ai-application-architecture` repository.

> [!IMPORTANT]
> **Dependency Philosophy: Lean by Default**  
> Every external dependency introduces supply chain risk, transitive complexity, maintenance overhead, and security attack surface. In this repository, we prefer standard library capabilities and direct, transparent HTTP/gRPC clients over bloated, fast-churning orchestration frameworks.

---

## 1. Dependency Evaluation Matrix

Before introducing any new third-party library or package, the introducing engineer or agent must evaluate the package against the following decision matrix:

| Evaluation Dimension | Passing Criteria | Disqualifying Red Flags |
| :--- | :--- | :--- |
| **Maintenance Health** | Active commit activity within the past 3 months; regular semantic releases; responsive issue triage. | Abandoned repository (> 12 months inactive); single-maintainer without enterprise backing. |
| **Architectural Fit** | Solves a complex, non-trivial capability (e.g., ONNX runtime, vector math, cryptographic hashing). | Trivial utility functions (e.g., `is-odd`, `left-pad`) that take fewer than 20 lines of standard library code. |
| **Transitive Weight** | Minimal transitive dependencies (< 5 dependencies preferred). | Deep transitive dependency tree pulling in hundreds of unvetted sub-dependencies. |
| **License Compliance** | Permissive open-source license (MIT, Apache 2.0, BSD 2/3-Clause). | Copyleft or source-available licenses (AGPL, SSPL, BSL, GPL, CC-BY-NC). |
| **Security Track Record** | Zero unpatched High/Critical CVEs; rapid remediation history on reported vulnerabilities. | Chronic unpatched vulnerabilities or unmaintained upstream components. |
| **AI Framework Churn** | Stable API contract with backwards compatibility guarantees. | Frameworks with frequent weekly breaking API changes that wrap simple HTTP calls in heavy abstractions. |

---

## 2. Pinned Lockfiles & Reproducible Builds

Every project or reference application across all supported programming languages must maintain an exact, version-controlled lockfile:

| Language Ecosystem | Primary Tool | Manifest File | Mandatory Lockfile |
| :--- | :--- | :--- | :--- |
| **Python** | `uv` / `pip` | `pyproject.toml` | `uv.lock` |
| **.NET** | NuGet / `dotnet` | `*.csproj` | `packages.lock.json` (LockedMode enabled) |
| **TypeScript / Node** | npm / pnpm | `package.json` | `package-lock.json` or `pnpm-lock.yaml` |
| **Java** | Gradle / Maven | `build.gradle.kts` / `pom.xml` | `gradle.lockfile` or `dependency-locks/` |

### Deterministic Build Rule
CI builds and container image compilation must always execute in strict locked mode (`uv sync --frozen`, `dotnet restore --locked-mode`, `npm ci`, or `./gradlew build --write-locks`). Floating version constraints (`*`, `latest`, `^`) without lockfile pinning are prohibited.

---

## 3. License Compatibility & Approved Open-Source Licenses

Only packages with permissive, business-friendly open-source licenses are permitted in this repository:

### Approved Licenses
* **MIT License**
* **Apache License 2.0**
* **BSD 2-Clause and BSD 3-Clause Licenses**
* **ISC License**
* **Python Software Foundation (PSF) License**

### Strictly Prohibited Licenses
* **GNU Affero General Public License (AGPL)** (All versions)
* **GNU General Public License (GPL)** (All versions)
* **Server Side Public License (SSPL)**
* **Business Source License (BSL / BUSL)**
* **Non-Commercial Licenses** (e.g., CC-BY-NC)
* **Unlicensed / Ambiguous Code** (repositories without an explicit OSI-approved license)

---

## 4. Automated Vulnerability Scanning & Upgrades

1. **Continuous Vulnerability Auditing**:
   * CI pipelines must execute automated dependency audits on every pull request:
     * Python: `uv run pip-audit` or `safety check`
     * .NET: `dotnet list package --vulnerable --include-transitive`
     * TypeScript: `npm audit --audit-level=high`
     * Java: OWASP Dependency-Check or Snyk
2. **Zero High/Critical Vulnerabilities**:
   * Pull requests introducing dependencies with unmitigated High or Critical CVEs are automatically rejected.
3. **Automated Dependabot Updates**:
   * Repository configuration (`.github/dependabot.yml`) must monitor weekly dependency releases and security advisories, creating isolated, targeted PRs for patch updates.
