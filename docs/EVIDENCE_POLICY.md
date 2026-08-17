# CPPD Investigation OS - Evidence Handling and Vault Policy

This document details policies regarding file storage, custody, and modification.

## 1. Storage Partitioning
Storage folders in Supabase / Google Cloud Storage must follow a strict folder boundary structure:
- `cases/CASE_ID/originals/`: The original files exactly as uploaded.
- `cases/CASE_ID/derived/`: Working copies, OCR text files, downscaled image/video files, and metadata sheets.
- `cases/CASE_ID/exports/`: Compiled PDF report briefings or packages.

## 2. Integrity and Immutability
- **Hash Checks**: Upon upload, the evidence gateway MUST immediately compute the SHA-256 hash. This value is recorded in `evidence.file_hash` and logged in the immutable `chain_of_custody` ledger.
- **Write Restrictions**: Under no circumstances does an AI model or automated agent possess write permission to files inside the `originals/` folder. All outputs must be saved to the `derived/` folder.
- **Audit Ledger**: Any read access, export, or transfer of original files must write a row to the database `audit_events` or `chain_of_custody` tables.
