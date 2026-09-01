-- Phase 9: Quality Control & Case Reviewer Schema

CREATE TABLE IF NOT EXISTS case_review_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    review_type TEXT DEFAULT 'FULL',
    status TEXT DEFAULT 'COMPLETED',
    requested_by UUID REFERENCES profiles(id),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ruleset_version TEXT DEFAULT 'v1.0-standard',
    summary JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS case_review_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_run_id UUID REFERENCES case_review_runs(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'MEDIUM',
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    source_reference_ids JSONB DEFAULT '[]',
    affected_resource_type TEXT,
    affected_resource_id TEXT,
    status TEXT DEFAULT 'OPEN',
    recommended_action TEXT,
    created_by TEXT DEFAULT 'CaseReviewerAgent',
    reviewed_by TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMP WITH TIME ZONE,
    false_positive_reason TEXT,
    accepted_risk_reason TEXT,
    authorized_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS supervisor_review_packages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    report_id UUID REFERENCES investigation_reports(id),
    status TEXT DEFAULT 'SUBMITTED_TO_SUPERVISOR',
    submitted_by TEXT NOT NULL,
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    readiness_summary TEXT DEFAULT 'READY_FOR_SUPERVISOR_REVIEW',
    notes TEXT
);
