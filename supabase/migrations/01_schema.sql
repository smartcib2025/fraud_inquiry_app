-- CPPD Investigation OS - Database Schema Migrations (Phase 1)
-- Enables UUID and pgcrypto extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Profiles & Roles Setup
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    org_unit TEXT NOT NULL, -- e.g., 'Financial Crimes', 'Cyber Division'
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.roles (
    id TEXT PRIMARY KEY, -- 'investigator', 'supervisor', 'commander'
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.user_roles (
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    role_id TEXT REFERENCES public.roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 2. Case Structure
CREATE TABLE IF NOT EXISTS public.cases (
    id TEXT PRIMARY KEY, -- CPPD-2026-XXXX format
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'open', -- 'open', 'under_review', 'closed'
    owning_unit TEXT NOT NULL,
    sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.case_members (
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    assignment_role TEXT NOT NULL DEFAULT 'viewer', -- 'lead', 'co-lead', 'viewer'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (case_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.case_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    assigned_by UUID REFERENCES public.profiles(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS public.case_status_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by UUID REFERENCES public.profiles(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Case Subjects / Inhabitants
CREATE TABLE IF NOT EXISTS public.victims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    address TEXT,
    loss_amount DECIMAL(15, 2),
    intake_source TEXT DEFAULT 'portal', -- 'portal', 'walk_in', 'referral'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.witnesses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    relationship_to_victim TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.suspects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    id_number TEXT, -- national id or passport
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Statements
CREATE TABLE IF NOT EXISTS public.statements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    subject_id UUID NOT NULL, -- references either victim, witness, or suspect
    subject_type TEXT NOT NULL, -- 'victim', 'witness', 'suspect'
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    transcript TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.statement_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID REFERENCES public.statements(id) ON DELETE CASCADE,
    transcript TEXT NOT NULL,
    modified_by UUID REFERENCES public.profiles(id),
    modified_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

-- 5. Evidence & Custody
CREATE TABLE IF NOT EXISTS public.evidence (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    type TEXT NOT NULL, -- 'document', 'audio', 'video', 'forensic_image', 'data_export'
    file_hash TEXT UNIQUE NOT NULL, -- SHA-256
    status TEXT DEFAULT 'sealed', -- 'sealed', 'opened', 'released'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.evidence_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES public.evidence(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL, -- relative storage path
    file_type TEXT NOT NULL, -- 'original', 'derived'
    mime_type TEXT,
    size_bytes BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.chain_of_custody (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES public.evidence(id) ON DELETE CASCADE,
    action TEXT NOT NULL, -- 'received', 'released', 'transferred', 'destroyed'
    handler_id UUID REFERENCES public.profiles(id),
    partner_org TEXT, -- if transferred externally
    purpose TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    hash_verified BOOLEAN DEFAULT TRUE
);

-- 6. Knowledge Graph (Entities & Relationships)
CREATE TABLE IF NOT EXISTS public.entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL, -- 'PERSON', 'PHONE', 'BANK_ACCOUNT', 'EMAIL', 'COMPANY', 'ADDRESS'
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.entity_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    identifier_type TEXT NOT NULL, -- 'phone_number', 'national_id', 'bank_account_number', 'email_address', 'tax_id'
    value TEXT NOT NULL,
    UNIQUE(identifier_type, value)
);

CREATE TABLE IF NOT EXISTS public.entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    target_entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL, -- 'OWNS', 'TRANSFERRED_TO', 'DIRECTOR_OF', 'CONTACTED', 'SHARED_ADDRESS'
    confidence DECIMAL(3, 2) DEFAULT 1.00,
    source_evidence_id UUID REFERENCES public.evidence(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.case_entities (
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    entity_id UUID REFERENCES public.entities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (case_id, entity_id)
);

-- 7. Financial Transactions
CREATE TABLE IF NOT EXISTS public.bank_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bank_name TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_name TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    source_account_id UUID REFERENCES public.bank_accounts(id),
    target_account_id UUID REFERENCES public.bank_accounts(id),
    amount DECIMAL(15, 2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'THB',
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    reference_number TEXT,
    evidence_id UUID REFERENCES public.evidence(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Workflow Tasks & Audits
CREATE TABLE IF NOT EXISTS public.investigation_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    assigned_to UUID REFERENCES public.profiles(id),
    status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'in_progress', 'completed', 'verified'
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.trigger_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL, -- 'VICTIM_REGISTERED', etc.
    payload JSONB NOT NULL,
    status TEXT DEFAULT 'pending', -- 'pending', 'processed', 'failed'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS public.audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID, -- NULL if system action
    action TEXT NOT NULL, -- e.g. 'SELECT', 'UPDATE', 'VIEW_EVIDENCE'
    table_name TEXT,
    record_id TEXT,
    query_details TEXT,
    logged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Communications & Digital Artifacts
CREATE TABLE IF NOT EXISTS public.communications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    channel TEXT NOT NULL, -- 'LINE_CHAT', 'PHONE_CALL', 'SMS', 'FACEBOOK', 'EMAIL', 'BANK_MEMO'
    sender_identifier TEXT NOT NULL,
    recipient_identifier TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    content_text TEXT,
    raw_payload JSONB,
    evidence_id UUID REFERENCES public.evidence(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 10. AI Analyses & Evidence Gaps (Isolated from Original Evidence)
CREATE TABLE IF NOT EXISTS public.ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    agent_name TEXT NOT NULL, -- e.g., 'FinancialTransactionAgent', 'LegalMappingAgent'
    analysis_type TEXT NOT NULL, -- 'TIMELINE_CONTRADICTION', 'EVIDENCE_GAP', 'STRUCTURING_ANALYSIS', 'INTERVIEW_PLAN'
    fact_tags JSONB NOT NULL DEFAULT '[]'::jsonb, -- Array of [{tag: 'FACT'|'CLAIM'|'INFERENCE'|'CONFLICT'|'EVIDENCE_GAP', text: '...', source_evidence_id: '...'}]
    findings_summary TEXT NOT NULL,
    confidence_score DECIMAL(3, 2) DEFAULT 0.90,
    review_status TEXT NOT NULL DEFAULT 'REQUIRES_HUMAN_REVIEW', -- 'VERIFIED', 'PARTIALLY_VERIFIED', 'MISMATCH', 'NOT_VERIFIED', 'REQUIRES_CHECK', 'REQUIRES_HUMAN_REVIEW'
    reviewed_by UUID REFERENCES public.profiles(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    investigator_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 11. Investigation Documents & Warrants (Version-Controlled)
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id TEXT REFERENCES public.cases(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL, -- 'SUMMONS_WARRANT', 'SEARCH_WARRANT', 'ACCUSATION_RECORD', 'FINAL_REPORT', 'BRIEFING'
    title TEXT NOT NULL,
    version INT NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'AI_DRAFT', -- 'AI_DRAFT', 'INVESTIGATOR_REVIEW', 'REVISED', 'APPROVED', 'FINAL'
    content_markdown TEXT NOT NULL,
    created_by TEXT NOT NULL,
    approved_by UUID REFERENCES public.profiles(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
