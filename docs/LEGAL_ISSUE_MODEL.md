# Legal Issue & Element Matrix Model

## LegalIssue Entity
- `id`: UUID
- `case_id`: UUID
- `title`: Legal charge title
- `law_reference`: Statute (e.g. ป.อ., พ.ร.บ.คอมพิวเตอร์ฯ, พ.ร.บ.เครื่องสำอาง)
- `section_reference`: Specific section (e.g. ม.343, ม.14(1))
- `issue_description`: Summary of statutory violation

## LegalElement Matrix
- `id`: UUID
- `issue_id`: UUID
- `element_title`: Essential statutory element
- `supporting_facts`: Verified facts in evidence
- `supporting_evidence_ids`: Array of exhibit IDs
- `contradictory_evidence_ids`: Array of contradictory exhibit IDs
- `missing_evidence`: Specific missing forensic gaps
- `review_status`: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `NOT_SUPPORTED`, `CONTRADICTED`, `REQUIRES_REVIEW`
