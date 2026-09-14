---
id: sec-01
title: Enterprise Data Retention Policy
department: compliance
category: policy
version: 2.1
---

# Enterprise Data Retention Policy

## 1. Purpose and Scope
This policy defines mandatory retention schedules for enterprise records, application telemetry, and customer personal data across all operating environments. Compliance with this policy is audited annually.

## 2. Retention Schedules
Enterprise data categories must be retained strictly according to the following retention periods:

* **Audit and Security Logs**: Security audit logs, authentication event trails, and access records must be retained for exactly **7 years** in tamper-evident storage.
* **Customer Personal Identifiable Information (PII)**: Customer PII must be purged or anonymized within **30 days** following verified account termination or contract expiration.
* **Operational Telemetry and Traces**: Application performance metrics, OpenTelemetry traces, and runtime debug logs must be retained for **90 days**, after which automated lifecycle rules purge raw telemetry.
* **Financial Transaction Records**: General ledgers, tax records, billing invoices, and payment receipts must be preserved for **10 years** in accordance with international accounting standards.

## 3. Exceptions and Legal Holds
In the event of active litigation or regulatory inquiry, a formal legal hold overrides standard purge schedules. Data subject to a legal hold must not be deleted until explicitly released by the General Counsel.
