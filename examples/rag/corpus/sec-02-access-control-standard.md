---
id: sec-02
title: Access Control and Credential Standard
department: security
category: standard
version: 3.0
---

# Access Control and Credential Standard

## 1. Authentication Requirements
Access to production systems, code repositories, and cloud control planes requires strong multi-factor authentication (MFA). Hardware security keys (FIDO2/WebAuthn) are mandatory for all administrative privileges.

## 2. Password and Key Lifecycle
* **Password Complexity**: Passwords must contain a minimum of **16 characters**, incorporating uppercase letters, lowercase letters, numbers, and symbols.
* **Session Token Duration**: Web application session tokens and API bearer tokens must have a maximum lifetime of **8 hours**. Refresh tokens must be rotated upon each grant and expire after 24 hours of inactivity.
* **SSH Key Rotation**: Developer SSH keys used for infrastructure access must be rotated every **90 days**. Deprecated key algorithms (DSA, RSA < 3072 bits) are strictly prohibited.

## 3. Least Privilege and Elevation
Direct root access is disabled. All operational maintenance must use temporary role-based access control (RBAC) elevation bounded by a maximum time window of 2 hours, requiring ticket authorization.
