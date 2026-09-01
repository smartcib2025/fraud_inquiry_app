-- Phase 8: Official Documents & Warrants Schema

CREATE TABLE IF NOT EXISTS case_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL DEFAULT 'OFFICIAL_LETTER',
    document_number TEXT,
    title TEXT NOT NULL,
    template_id TEXT,
    template_version TEXT DEFAULT '1.0',
    status TEXT DEFAULT 'DRAFT',
    classification TEXT DEFAULT 'INTERNAL',
    current_version INT DEFAULT 1,
    created_by UUID REFERENCES profiles(id),
    assigned_reviewer TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    finalized_by TEXT,
    finalized_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_warrant_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    target_type TEXT DEFAULT 'PREMISES',
    target_location TEXT NOT NULL,
    target_person_id UUID REFERENCES people(id),
    purpose TEXT NOT NULL,
    facts_supporting_request TEXT NOT NULL,
    evidence_ids JSONB DEFAULT '[]',
    legal_basis TEXT DEFAULT 'ป.วิ.อ. มาตรา 69, 70',
    urgency TEXT DEFAULT 'HIGH',
    status TEXT DEFAULT 'DRAFT',
    prepared_by UUID REFERENCES profiles(id),
    reviewed_by TEXT,
    approved_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS arrest_warrant_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    target_person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    identity_status TEXT DEFAULT 'VERIFIED',
    facts_supporting_request TEXT NOT NULL,
    evidence_ids JSONB DEFAULT '[]',
    legal_basis TEXT DEFAULT 'ป.วิ.อ. มาตรา 66',
    risk_factors TEXT,
    status TEXT DEFAULT 'DRAFT',
    prepared_by UUID REFERENCES profiles(id),
    reviewed_by TEXT,
    approved_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
