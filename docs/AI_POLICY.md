# CPPD Investigation OS - AI Router & Modeling Policies

This document governs the usage of artificial intelligence (Gemini models) on the platform.

## 1. Model Tier Strategy
To balance operational cost, latency, and reasoning capability, we enforce a strict routing policy:

- **Gemini Flash (Medium)**:
  - Used for standard, high-volume processing tasks:
    - Text classification & labeling
    - Primary entity extraction (identifying phones, names, accounts)
    - Metadata generation
    - Document summarization
- **Gemini Pro (Advanced)**:
  - Used for high-reasoning, synthesis, and correlation tasks:
    - Cross-case pattern synthesis
    - Timeline alignment and chronological contradiction analysis
    - Evidence gap checking
    - Case readiness assessments & supervisor review summaries
- **Antigravity Sandbox (Managed Runtime)**:
  - Used for multi-step analytics, execution of custom scripts on derived datasets, file transformations (e.g. converting nested transaction rows), and large-volume analysis.

## 2. Structured Extraction Constraints
- Gemini prompts MUST use structured JSON schemas for outputs. Free-form text parsing for database inserts is forbidden.
- Output models must define exact fields:
  ```json
  {
    "persons": [],
    "companies": [],
    "phones": [],
    "bank_accounts": [],
    "transactions": [],
    "dates": [],
    "locations": [],
    "allegations": [],
    "evidence_references": []
  }
  ```
- All returned JSON payloads must pass validator schemas before database insertion.

## 3. PII Redaction & Data Protection (DLP)
- Raw statements containing high-sensitivity items must go through a DLP gateway where local processing or strict token redaction masks names and numbers (e.g., `Mr. Somchai` becomes `PERSON_1`) before routing to cloud Gemini services, depending on case security status.
