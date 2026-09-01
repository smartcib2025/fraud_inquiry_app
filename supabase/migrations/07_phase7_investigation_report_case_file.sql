-- Phase 7: Investigation Report & Case File Schema

CREATE TABLE IF NOT EXISTS investigation_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    report_type TEXT NOT NULL DEFAULT 'INVESTIGATION_REPORT',
    title TEXT NOT NULL,
    template_id TEXT,
    template_version TEXT DEFAULT '1.0',
    status TEXT DEFAULT 'DRAFT',
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

CREATE TABLE IF NOT EXISTS report_sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES investigation_reports(id) ON DELETE CASCADE,
    section_code TEXT NOT NULL,
    title TEXT NOT NULL,
    sequence INT NOT NULL,
    content TEXT NOT NULL,
    content_type TEXT DEFAULT 'NARRATIVE',
    generated_by TEXT DEFAULT 'HUMAN',
    review_status TEXT DEFAULT 'DRAFT',
    locked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    report_id UUID REFERENCES investigation_reports(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content_snapshot JSONB NOT NULL,
    created_by UUID REFERENCES profiles(id),
    change_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS document_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id),
    report_id UUID REFERENCES investigation_reports(id),
    format TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    exported_by TEXT NOT NULL,
    exported_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    purpose TEXT,
    recipient TEXT
);
