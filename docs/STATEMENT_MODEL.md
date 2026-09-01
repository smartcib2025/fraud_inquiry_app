# Statement & Interrogation Data Model

## Statement Entity
- `id`: UUID
- `case_id`: UUID / Text Reference
- `person_id`: UUID of interviewee
- `statement_type`: `COMPLAINT`, `VICTIM`, `WITNESS`, `SUSPECT`, `ACCUSED`, `EXPERT`, `OFFICIAL`
- `statement_number`: E.g. `STMT-CASE-142-001`
- `interviewed_by`: Officer name & badge
- `interview_started_at`: Timestamp
- `interview_ended_at`: Timestamp
- `location`: Location of inquiry (e.g. กก.1 บก.ปคบ.)
- `status`: `DRAFT`, `IN_REVIEW`, `RETURNED`, `APPROVED`, `FINAL`
- `version`: Integer version number

## StatementQA Entity
- `id`: UUID
- `statement_id`: UUID
- `sequence`: Integer sequence number
- `question`: Interrogation question
- `answer`: Verbatim recorded response
- `notes`: Officer observation & consistency notes
- `source_reference`: Linked exhibit / evidence ID
