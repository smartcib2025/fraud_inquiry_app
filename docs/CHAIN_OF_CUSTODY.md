# Chain of Custody Standard Operating Procedure (กก.1 บก.ปคบ.)

## 1. Principle of Traceability
Every physical and digital exhibit in Division 1 must provide an unbroken historical record from the moment of seizure to court presentation.

## 2. Custody Event Lifecycle
- `RECEIVED`: Initial seizure or citizen submission.
- `REGISTERED`: Exhibit officially recorded with SHA-256 hash stamp.
- `SEALED`: Enclosed in tamper-evident evidence envelope with seal number.
- `TRANSFERRED`: Relinquished from one custodian to another with witness sign-off.
- `SUBMITTED_FOR_ANALYSIS`: Dispatched to external forensic labs (e.g. กรมวิทยาศาสตร์การแพทย์, สถาบันนิติวิทยาศาสตร์).
- `CHECKED_OUT` / `CHECKED_IN`: Temporary withdrawal for interrogation or court hearing.
- `COURT_SUBMISSION`: Final transmittal to the Public Prosecutor or Criminal Court.

## 3. Immutability
Custody logs are strictly append-only. Corrections require superseding entries and generate audit events.
