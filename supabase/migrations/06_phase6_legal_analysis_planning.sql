-- Phase 6: Legal Analysis & Investigation Planning Schema

CREATE TABLE IF NOT EXISTS laws (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    title_th TEXT NOT NULL,
    title_en TEXT,
    jurisdiction TEXT DEFAULT 'THAILAND',
    effective_from DATE,
    effective_to DATE,
    status TEXT DEFAULT 'ACTIVE',
    source_reference TEXT,
    version TEXT DEFAULT '1.0'
);

CREATE TABLE IF NOT EXISTS legal_provisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    law_id UUID REFERENCES laws(id) ON DELETE CASCADE,
    section TEXT NOT NULL,
    subsection TEXT,
    title TEXT NOT NULL,
    text_reference TEXT,
    effective_from DATE,
    effective_to DATE
);

CREATE TABLE IF NOT EXISTS case_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    fact_text TEXT NOT NULL,
    fact_type TEXT DEFAULT 'FACT',
    verification_status TEXT DEFAULT 'NOT_VERIFIED',
    source_type TEXT DEFAULT 'EVIDENCE',
    source_ids JSONB DEFAULT '[]',
    created_by UUID REFERENCES profiles(id),
    reviewed_by UUID REFERENCES profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legal_element_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    legal_element_id UUID REFERENCES legal_elements(id) ON DELETE CASCADE,
    legal_issue_id UUID REFERENCES legal_issues(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'SUPPORTED',
    supporting_fact_ids JSONB DEFAULT '[]',
    supporting_evidence_ids JSONB DEFAULT '[]',
    contradictory_evidence_ids JSONB DEFAULT '[]',
    missing_fact_description TEXT,
    analyst_comment TEXT,
    reviewed_by TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS human_legal_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    decided_by TEXT NOT NULL,
    decided_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    related_resource TEXT
);
