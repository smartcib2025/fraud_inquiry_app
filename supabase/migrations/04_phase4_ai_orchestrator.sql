-- Phase 4: AI Orchestrator & Multi-Agent Schema

CREATE TABLE IF NOT EXISTS ai_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    requested_by UUID REFERENCES profiles(id),
    agent_type TEXT NOT NULL,
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    prompt_version TEXT NOT NULL,
    input_source_ids JSONB DEFAULT '[]',
    data_classification TEXT DEFAULT 'CONFIDENTIAL',
    status TEXT DEFAULT 'SUCCEEDED',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    token_usage JSONB DEFAULT '{}',
    cost_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES ai_executions(id) ON DELETE CASCADE,
    case_id UUID REFERENCES cases(id) ON DELETE CASCADE,
    analysis_type TEXT NOT NULL,
    result_json JSONB NOT NULL,
    summary TEXT NOT NULL,
    confidence NUMERIC(3, 2) DEFAULT 0.90,
    review_status TEXT DEFAULT 'REQUIRES_REVIEW',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prompt_registry (
    prompt_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL,
    version TEXT NOT NULL,
    language TEXT DEFAULT 'th',
    system_prompt TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
