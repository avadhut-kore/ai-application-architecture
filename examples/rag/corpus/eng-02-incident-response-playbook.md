---
id: eng-02
title: Incident Response and Severity Playbook
department: engineering
category: playbook
version: 2.0
---

# Incident Response and Severity Playbook

## 1. Severity Classification
Production incidents are categorized into four standardized severity tiers:
* **Severity 1 (Sev-1: Critical Outage)**: Complete customer-facing service disruption, data loss risk, or security breach.
* **Severity 2 (Sev-2: Major Degradation)**: High-impact service degradation affecting greater than 20% of users without full outage.
* **Severity 3 (Sev-3: Minor Impairment)**: Partial functionality defect with an available operational workaround.
* **Severity 4 (Sev-4: Low/Cosmetic)**: Non-critical defect, typo, or minor administrative cosmetic issue.

## 2. Escalation SLAs and Timelines
Response teams must acknowledge and begin incident triage within explicit time windows:
* **Sev-1 Incident SLA**: Initial response within **15 minutes**, continuous hourly executive communication updates.
* **Sev-2 Incident SLA**: Initial response within **1 hour**, updates every 4 hours until mitigated.
* **Post-Mortem Timeline**: A blameless post-mortem root cause analysis (RCA) must be published within **72 hours** of Sev-1 or Sev-2 incident resolution.
