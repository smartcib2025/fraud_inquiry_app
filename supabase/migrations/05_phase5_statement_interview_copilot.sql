-- Phase 5: Statement & Interview Copilot Schema

CREATE TABLE IF NOT EXISTS interview_preparations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    statement_id UUID REFERENCES statements(id) ON DELETE CASCADE,
    person_id UUID REFERENCES people(id),
    objective TEXT NOT NULL,
    issues_to_cover JSONB DEFAULT '[]',
    known_facts JSONB DEFAULT '[]',
    relevant_evidence_ids JSONB DEFAULT '[]',
    prepared_by UUID REFERENCES profiles(id),
    ai_assisted BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS interview_questions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID REFERENCES statements(id) ON DELETE CASCADE,
    sequence INT NOT NULL,
    question_type TEXT DEFAULT 'OPEN',
    topic TEXT NOT NULL,
    question_text TEXT NOT NULL,
    purpose TEXT NOT NULL,
    source_reference_ids JSONB DEFAULT '[]',
    generated_by TEXT DEFAULT 'HUMAN',
    status TEXT DEFAULT 'ASKED',
    asked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS statement_answers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID REFERENCES statements(id) ON DELETE CASCADE,
    question_id UUID REFERENCES interview_questions(id),
    sequence INT NOT NULL,
    answer_text TEXT NOT NULL,
    answer_type TEXT DEFAULT 'VERBATIM',
    recorded_by UUID REFERENCES profiles(id),
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

CREATE TABLE IF NOT EXISTS statement_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    statement_id UUID REFERENCES statements(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    content_text TEXT NOT NULL,
    changed_by UUID REFERENCES profiles(id),
    change_reason TEXT,
    review_status TEXT DEFAULT 'DRAFT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
