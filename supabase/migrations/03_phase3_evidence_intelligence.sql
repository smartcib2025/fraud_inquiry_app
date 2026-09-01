-- Phase 3: Evidence Intelligence & Chain of Custody Schema

CREATE TABLE IF NOT EXISTS evidence_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES evidence(id) ON DELETE CASCADE,
    artifact_type TEXT DEFAULT 'ORIGINAL',
    parent_file_id UUID REFERENCES evidence_files(id),
    object_key TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    stored_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    extension TEXT NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256 TEXT NOT NULL,
    sha512 TEXT,
    storage_provider TEXT DEFAULT 'CPPD_SECURE_STORAGE',
    storage_bucket TEXT DEFAULT 'cppd-evidence-vault',
    uploaded_by UUID REFERENCES profiles(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    scan_status TEXT DEFAULT 'CLEAN',
    integrity_status TEXT DEFAULT 'VERIFIED',
    is_primary BOOLEAN DEFAULT TRUE,
    is_immutable BOOLEAN DEFAULT TRUE,
    metadata_json JSONB DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS custody_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES evidence(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL,
    from_user_id TEXT NOT NULL,
    to_user_id TEXT NOT NULL,
    from_location TEXT NOT NULL,
    to_location TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    witnessed_by TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT NOT NULL,
    seal_number TEXT,
    condition_before TEXT,
    condition_after TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS evidence_integrity_checks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id UUID REFERENCES evidence(id) ON DELETE CASCADE,
    check_type TEXT NOT NULL,
    expected_hash TEXT NOT NULL,
    actual_hash TEXT NOT NULL,
    result TEXT NOT NULL,
    performed_by UUID REFERENCES profiles(id),
    performed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tool_name TEXT NOT NULL,
    tool_version TEXT NOT NULL,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS evidence_gaps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    investigation_issue_id UUID REFERENCES investigation_issues(id),
    legal_element_id UUID REFERENCES legal_elements(id),
    description TEXT NOT NULL,
    required_evidence_type TEXT NOT NULL,
    priority TEXT DEFAULT 'HIGH',
    status TEXT DEFAULT 'OPEN',
    assigned_to UUID REFERENCES profiles(id),
    due_at TIMESTAMP WITH TIME ZONE,
    resolved_by_evidence_id UUID REFERENCES evidence(id)
);
