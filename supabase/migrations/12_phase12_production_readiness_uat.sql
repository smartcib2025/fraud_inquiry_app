-- Phase 12: Production Readiness & UAT Defect Schema

CREATE TABLE IF NOT EXISTS uat_test_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_id TEXT NOT NULL,
    tester_role TEXT NOT NULL,
    status TEXT DEFAULT 'PASSED',
    executed_by TEXT NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS uat_defects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    defect_id TEXT UNIQUE NOT NULL,
    test_case TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'LOW',
    description TEXT NOT NULL,
    status TEXT DEFAULT 'FIXED',
    fixed_version TEXT,
    retest_result TEXT DEFAULT 'PASSED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS production_release_certifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    release_version TEXT NOT NULL,
    status TEXT DEFAULT 'APPROVED_FOR_PILOT',
    approved_by TEXT NOT NULL,
    approval_role TEXT NOT NULL,
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);
