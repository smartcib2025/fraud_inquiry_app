# Evidence Integrity & Hash Verification Standard

## 1. Cryptographic Hash Engine
- Primary Algorithm: **SHA-256** (FIPS 180-4)
- Secondary / Archival: **SHA-512**
- Verification Points: On upload, custody transfer, periodic integrity check, and export.

## 2. Tamper Alarms & Security Events
If an exhibit file's calculated hash differs from `expected_hash`:
1. HTTP 409 Conflict / Security Alert returned.
2. `EVIDENCE.HASH.MISMATCH` event appended to immutable audit log.
3. Automated lock-down on export capabilities for the compromised exhibit.
