# Deterministic AI Provider & Model Routing Policy

## Data Classification Matrix
- `PUBLIC` / `INTERNAL`: Can route to Approved Cloud AI or Local CPPD AI Node.
- `CONFIDENTIAL` / `RESTRICTED`: Strictly routes to Local CPPD AI Node only. Cloud AI is blocked with HTTP 403.
- **Fail-Safe**: If Local AI is down, Restricted requests are denied securely (Zero Cloud Fallback).
