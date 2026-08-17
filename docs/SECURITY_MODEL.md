# CPPD Investigation OS - Security Model

This document outlines the security architecture and authorization controls.

## 1. Authentication & Session Security
- **Identity Provider**: Supabase Auth handles user signups, logins, password management, and generates JSON Web Tokens (JWTs).
- **Client Authentication**: Browser dashboard and Slack APIs receive token contexts. No credentials are stored on client machines.

## 2. Row Level Security (RLS)
Supabase enforces access control directly inside the database based on the JWT payload `auth.uid()`.
- **Investigator Role**: Access is restricted to cases matching active listings in the `case_members` junction table.
- **Supervisor Role**: Can view/update all cases that belong to the supervisor's active organizational unit.
- **Commander Role**: Unrestricted read access across all units, read-write access when explicitly designated.

## 3. Google Cloud IAM Policies
- Each service runs with a dedicated service account:
  - `cppd-dashboard-sa`: Dashboard frontend service account.
  - `cppd-slack-sa`: Verifies Slack messages and relays commands.
  - `cppd-mcp-sa`: Accesses database, validates permissions, acts as tool layer.
  - `cppd-ai-sa`: Interfaces with Gemini.
  - `cppd-trigger-sa`: Manages Pub/Sub subscription triggers.
  - `cppd-evidence-sa`: Manages Cloud Storage buckets and evidence vault interfaces.

## 4. Google Secret Manager
- Raw keys, tokens, and DB connection secrets are loaded strictly from Secret Manager at container runtime.
- Never hardcoded in codebase, configuration files, or prompts.
- Keys include: `SUPABASE_SERVICE_ROLE`, `GEMINI_API_KEY`, `SLACK_SIGNING_SECRET`, `SLACK_BOT_TOKEN`.
