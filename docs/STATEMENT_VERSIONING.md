# Statement Versioning & Review Specification

## Immutability of Statement Versions
- Every revision generates a new `StatementVersion` (`v1.0`, `v2.0`).
- Previous versions cannot be overwritten.
- Supervisor returns (`RETURNED`) or approvals (`APPROVED`) are tracked with officer timestamp and audit logs.
