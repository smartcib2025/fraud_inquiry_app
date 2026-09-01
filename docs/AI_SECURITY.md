# AI Security & Prompt Injection Defense

## Defensive Controls
1. **Untrusted Evidence Isolation**: Seized digital text and OCR documents are parsed strictly as raw payload.
2. **Structured JSON Output**: All agent responses must conform to Pydantic schemas with mandatory classification tags (`FACT`, `CLAIM`, `INFERENCE`, `CONFLICT`, `EVIDENCE_GAP`, `REQUIRES_HUMAN_REVIEW`).
3. **Zero Secret Leakage**: No API keys or session tokens are stored in AI execution records.
