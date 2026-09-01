# Phase 2 — Case Workspace Specification (กก.1 บก.ปคบ.)

## 1. Overview
The Case Workspace provides an end-to-end investigative hub for police officers and investigators in Division 1 (กก.1 บก.ปคบ.).

## 2. Workspace Navigation (12 Modules)
1. **Overview (ภาพรวมสำนวน)**: Metrics summary (Loss, Evidence count, Open issues, Pending tasks), Narrative summary with immutable version history, and Pre-Trial Case Readiness Index.
2. **Issues (ประเด็นต้องพิสูจน์)**: Investigation issues categorized by financial linkages, physical evidence, and mens rea with strict status tracking (`OPEN`, `IN_PROGRESS`, `RESOLVED`, `ON_HOLD`, `CANCELLED`).
3. **People (บุคคลในคดี & สิทธิ์)**: Master entities for Complainants, Victims, Witnesses, Suspects, Accused, Proxy Directors, and Company entities with contact logs and national IDs.
4. **Statements (คำให้การ & บันทึกสอบปากคำ)**: Structured Q&A interrogation records with sequence numbers, source references, and approval state transitions (`DRAFT` -> `IN_REVIEW` -> `RETURNED` -> `APPROVED` -> `FINAL`).
5. **Evidence (พยานหลักฐาน & ความเชื่อมโยง)**: Evidence vault tracking SHA-256 hashes, physical chain of custody, and non-destructive `EvidenceRelation` mappings (Person, Statement, Event, Issue).
6. **Timeline (ลำดับเหตุการณ์ & สถานะตรวจสอบ)**: Chronological event ledger with verified status badges and AI-audited alibi contradiction detection.
7. **Investigation Plan (แผนการสืบสวนสอบสวน)**: Formal investigation objectives, required evidence list, agencies to contact, and action items with 1-click conversion to tasks.
8. **Tasks (รายการงานสอบสวน)**: Operational task tracker with assignees, due dates, and completion evidence.
9. **Legal Issues (ประเด็นข้อกฎหมาย & Matrix)**: Statutory elements mapped to supporting facts, supporting evidence, contradictory evidence, missing evidence, and review status.
10. **Documents (เอกสารสำนวน & ขออนุมัติ)**: Official police legal document drafts (Summons Warrants, Search Warrants, Accusation Records, Final Investigation Reports) with version history and supervisor sign-offs.
11. **Team (คณะพนักงานสืบสวนสอบสวน)**: Lead Investigator, Co-Investigators, Case Clerks, and Evidence Custodians.
12. **Activity (ประวัติกิจกรรมคดีทั้งหมด)**: Real-time append-only domain activity feed.
