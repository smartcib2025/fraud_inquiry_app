# Statement & Interview Copilot Architecture

## Modular Statement Copilot Agents
1. **InterviewQuestionAgent**: Formulates core interrogatory topics with legal purpose and source citations.
2. **FollowUpQuestionAgent**: Dynamically evaluates live answers against existing statements and flags missing details.
3. **StatementConsistencyAgent**: Checks for contradictions within the same statement and cross-references against verified case evidence.
4. **StatementCompletenessAgent**: Audits statutory checklists (Identity, Dates, Financial amounts, Damages).
5. **StatementDraftAgent**: Drafts official Thai police statements (`AI-ASSISTED DRAFT -- NOT FINAL`) with explicit `[ข้อมูลยังไม่ครบ / ต้องตรวจสอบ]` tags for unverified items.
