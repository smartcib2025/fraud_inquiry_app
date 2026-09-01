-- Phase 2: Case Workspace & Investigation Workflow Schema

CREATE TABLE IF NOT EXISTS investigation_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT DEFAULT 'FACT_TO_PROVE',
    priority TEXT DEFAULT 'HIGH',
    status TEXT DEFAULT 'OPEN',
    source TEXT DEFAULT 'INVESTIGATOR',
    created_by UUID REFERENCES profiles(id),
    assigned_to UUID REFERENCES profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statement_qas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID REFERENCES statements(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    notes TEXT,
    source_reference UUID REFERENCES evidence(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    evidence_id UUID REFERENCES evidence(id) ON DELETE CASCADE,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS investigation_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    objective TEXT NOT NULL,
    issues_to_prove TEXT[] DEFAULT '{}',
    required_evidence TEXT[] DEFAULT '{}',
    persons_to_interview TEXT[] DEFAULT '{}',
    agencies_to_contact TEXT[] DEFAULT '{}',
    digital_checks TEXT[] DEFAULT '{}',
    legal_questions TEXT[] DEFAULT '{}',
    outstanding_gaps TEXT[] DEFAULT '{}',
    target_date DATE,
    responsible_investigator TEXT,
    status TEXT DEFAULT 'PLANNED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS legal_elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    issue_id UUID REFERENCES legal_issues(id) ON DELETE CASCADE,
    element_title TEXT NOT NULL,
    supporting_facts TEXT NOT NULL,
    supporting_evidence_ids UUID[] DEFAULT '{}',
    contradictory_evidence_ids UUID[] DEFAULT '{}',
    missing_evidence TEXT,
    review_status TEXT DEFAULT 'SUPPORTED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS case_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    version INTEGER DEFAULT 1,
    author TEXT NOT NULL,
    reviewer TEXT,
    approval_status TEXT DEFAULT 'DRAFT',
    generated_from TEXT DEFAULT 'INVESTIGATOR',
    source_references TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    requested_by UUID REFERENCES profiles(id),
    reviewer_id UUID REFERENCES profiles(id),
    status TEXT DEFAULT 'PENDING',
    comments TEXT,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reviewed_at TIMESTAMP WITH TIME ZONE
);
