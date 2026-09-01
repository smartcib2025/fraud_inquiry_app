-- Phase 11: Supervisor Review, Command Approval & Case Governance Schema

CREATE TABLE IF NOT EXISTS supervisor_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    review_type TEXT DEFAULT 'INVESTIGATION_REPORT',
    review_level TEXT DEFAULT 'SUPERINTENDENT',
    submitted_by UUID REFERENCES profiles(id),
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_reviewer UUID REFERENCES profiles(id),
    status TEXT DEFAULT 'SUBMITTED',
    case_snapshot_id TEXT NOT NULL,
    report_version_id UUID REFERENCES investigation_reports(id),
    quality_review_id UUID REFERENCES case_review_runs(id),
    decision TEXT,
    decision_reason TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS supervisor_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID REFERENCES supervisor_reviews(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    comment TEXT NOT NULL,
    severity TEXT DEFAULT 'MEDIUM',
    status TEXT DEFAULT 'OPEN',
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS supervisor_directions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    review_id UUID REFERENCES supervisor_reviews(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    direction_type TEXT NOT NULL DEFAULT 'OBTAIN_EVIDENCE',
    priority TEXT DEFAULT 'HIGH',
    issued_by TEXT NOT NULL,
    issued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    assigned_to UUID REFERENCES profiles(id),
    due_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'ISSUED',
    completion_note TEXT,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE IF NOT EXISTS governance_approval_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    resource_version TEXT NOT NULL,
    resource_hash TEXT NOT NULL,
    requested_by UUID REFERENCES profiles(id),
    approver_role TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING',
    decision_reason TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS governance_recusals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID REFERENCES supervisor_reviews(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    recused_user_id UUID REFERENCES profiles(id),
    conflict_reason TEXT NOT NULL,
    reassigned_reviewer_id UUID REFERENCES profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS governance_delegations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    delegated_by UUID REFERENCES profiles(id),
    delegated_to UUID REFERENCES profiles(id),
    scope TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    authority_limit TEXT NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS case_closure_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    requested_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    report_version_id UUID REFERENCES investigation_reports(id),
    status TEXT DEFAULT 'PENDING_SUPERVISOR_APPROVAL',
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
