# CPPD Investigation OS - Database Schema Specification

This document details the relational structure of the database.

## 1. Schema Tables

### Core Users & Roles
- `profiles`: Holds investigator profiles (name, email, organization unit, status).
- `roles`: Defined roles within CPPD (Investigator, Supervisor, Commander).
- `user_roles`: Maps profiles to their roles.

### Case Structure
- `cases`: The root investigation record containing unique case IDs, owning unit, sensitive tags, and state.
- `case_members`: Links user profiles to cases with explicit role assignments (Lead, Co-Lead, Viewer).
- `case_assignments`: Formal investigator assignment timeline.
- `case_status_history`: Tracks transitions of the case state.

### Case Subjects & Records
- `victims`: Case victim information, claimed loss details, intake method.
- `witnesses`: Witness names and relationship to suspects/victims.
- `suspects`: Suspect identity data, active addresses.
- `statements`: Transcription and semantic summary of recorded statements.
- `statement_versions`: Auditable history of modifications to statement transcripts.

### Evidence & Custody
- `evidence`: Registry of physical and digital artifacts, distinct between original vault reference and derived files.
- `evidence_files`: Maps actual stored blobs (derived vs original).
- `chain_of_custody`: Immutable history of possession changes, custody verification, and location transfers.

### Entity & Knowledge Graph
- `entities`: Generalized node list representing actors or properties (e.g. PERSON, PHONE, BANK_ACCOUNT).
- `entity_identifiers`: Links entities to unique keys (e.g. ID numbers, phone strings, account numbers).
- `entity_relationships`: Edges in the knowledge graph (e.g. OWNS, TRANSFERRED_TO).
- `case_entities`: Connects entities to relevant cases.

### Financial Intelligence
- `bank_accounts`: Specific accounts detected.
- `transactions`: Log of funds transfers, amounts, timestamps, and counterparties.

### Workflow & AI Logging
- `investigation_tasks`: Actionable tasks assigned to investigators.
- `trigger_events`: Pub/Sub event records.
- `audit_events`: System-wide audit log for compliance.
