# AI Orchestrator Specification

## Orchestrator Responsibilities
- **Authentication & RBAC**: Verifies investigator's case assignment.
- **Classification Routing**: Automatically blocks external Cloud AI providers when analyzing `RESTRICTED` or sensitive cases.
- **Prompt Isolation**: System instructions and untrusted evidence data are strictly partitioned.
- **Execution Tracking**: Appends token usage, latency, model version, and audit events to `ai_executions`.
