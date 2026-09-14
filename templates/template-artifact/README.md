# Tier 4 Template Artifact: [Archetype Name]

> [!CAUTION]
> **Scaffolding Archetype Notice**  
> This artifact is a **Tier 4 Template / Scaffold**. It is designed strictly to accelerate development and establish consistent structure.  
> **It must NEVER be cited as a production-ready implementation, deployable application, or evidence of production architecture until independently completed and verified under a higher tier.**

---

## 1. Archetype Purpose

* **Target Output**: [Describe what kind of artifact this template scaffolds; e.g. a microservice, a standalone pattern, an evaluation runner].
* **Scaffolding Rationale**: [Explain the boilerplate or standard conventions codified by this template].

---

## 2. Directory Layout & Included Files

```text
[template-name]/
├── artifact.json                  # Baseline manifest template
├── README.md                      # Documentation template
└── [additional scaffolding files] # Baseline code, configuration stubs, or test harnesses
```

---

## 3. How to Use This Template

1. **Copy Scaffolding**: Copy the template directory to your destination location.
2. **Rename Identifiers**: Replace all placeholder tokens (`[application-name]`, `[package_name]`) with target project names.
3. **Update Manifest**: Edit `artifact.json` with the appropriate tier (1, 2, or 3), status (`planned`), and taxonomy classifications.
4. **Resolve Prompts**: Fulfill all instructional markdown prompts with concrete domain requirements and architecture specifications.
5. **Implement & Test**: Develop domain logic, tests, and evaluation suites per repository engineering standards.
6. **Validate**: Run `python3 scripts/validate.py` to ensure structural and contract compliance.

---

## 4. Quality Gate Checklist (Scaled for Tier 4)

Per [QUALITY-GATES.md](../../QUALITY-GATES.md):
- [ ] **Gate B (Local-First)**: Contains safe, local defaults; zero hardcoded cloud URLs or credentials.
- [ ] **Gate H (Documentation)**: Clear usage instructions, archetype layout, and prominent non-production notice.
