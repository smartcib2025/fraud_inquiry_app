# Police Copilot Threat Model & Mitigation Matrix

| Threat | Attack Vector | Control & Mitigation |
| :--- | :--- | :--- |
| **Data Leakage to Cloud** | Accidental cloud routing | Central deterministic routing policy & HTTP 403 block |
| **Prompt Injection** | Untrusted evidence text | Input sanitization, separate context framing |
| **Audit Tampering** | Malicious log modification | Immutable SHA-256 hash chaining & append-only DB |
| **Privilege Escalation** | IDOR / Role bypass | Server-side RBAC + Case Unit Scope validation |
