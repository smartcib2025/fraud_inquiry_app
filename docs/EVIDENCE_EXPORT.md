# Evidence Export & Controlled Manifest Specification

## 1. Evidence Package Manifest (`manifest.json`)
Every exported case bundle generates an encrypted/signed manifest containing:
- `export_package_id`: Unique transmittal bundle identifier.
- `case_id`: Official case reference number.
- `exporting_officer`: Full name, rank, and police ID.
- `recipient`: Court / Prosecutor / External Agency.
- `purpose`: Legal justification for transmittal.
- `manifest_items`:
  - `evidence_id`
  - `title`
  - `sha256`
  - `size_bytes`
  - `classification`
