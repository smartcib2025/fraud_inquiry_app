# CPPD Investigation OS - Model Context Protocol (MCP) Tool Contracts

This document defines the interface of tools exposed to agents via the MCP gateway.

## 1. Exposed Tools

### `get_case`
- **Description**: Retrieves full metadata for a given case, including details, assigned investigators, and status.
- **Parameters**:
  - `case_id` (string, required)
- **Output**: JSON payload representing case, members, and summary stats.

### `search_evidence`
- **Description**: Searches evidence catalog by keyword, type, or date range.
- **Parameters**:
  - `case_id` (string, required)
  - `query` (string, optional)
  - `type` (string, optional)
- **Output**: Array of matching evidence records.

### `search_entity`
- **Description**: Searches the entity database for matching identifiers (e.g. phone numbers, bank accounts, names).
- **Parameters**:
  - `query` (string, required)
- **Output**: Array of matching entities and the cases they are linked to.

### `find_related_cases`
- **Description**: Finds cases containing matching identifiers to identify potential cross-case patterns.
- **Parameters**:
  - `entity_id` (string, required)
- **Output**: Array of case links and confidence scoring.

### `get_transactions`
- **Description**: Retrieves transactions associated with a given bank account or case.
- **Parameters**:
  - `account_id` (string, optional)
  - `case_id` (string, optional)
- **Output**: Array of transaction nodes and flow linkages.

### `create_task`
- **Description**: Creates a new investigation task.
- **Parameters**:
  - `case_id` (string, required)
  - `title` (string, required)
  - `description` (string, optional)
  - `assigned_to` (string, optional)
  - `due_date` (string, optional)
- **Output**: The generated task record.
