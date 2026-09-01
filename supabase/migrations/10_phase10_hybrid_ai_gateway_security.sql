-- Phase 10: Hybrid AI Gateway & Production Security Schema

CREATE TABLE IF NOT EXISTS ai_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'LOCAL',
    endpoint TEXT NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    allowed_classifications JSONB DEFAULT '["PUBLIC", "INTERNAL"]',
    allowed_capabilities JSONB DEFAULT '["chat"]',
    allowed_models JSONB DEFAULT '[]',
    region TEXT DEFAULT 'THAILAND',
    data_retention_policy TEXT DEFAULT 'ZERO_RETENTION',
    training_policy TEXT DEFAULT 'ZERO_TRAINING',
    health_status TEXT DEFAULT 'HEALTHY',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id TEXT UNIQUE NOT NULL,
    provider_id TEXT REFERENCES ai_providers(provider_id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    model_version TEXT DEFAULT '1.0',
    capabilities JSONB DEFAULT '["chat"]',
    context_limit INT DEFAULT 128000,
    classification_limit TEXT DEFAULT 'INTERNAL',
    status TEXT DEFAULT 'APPROVED',
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_by TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS security_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL DEFAULT 'MEDIUM',
    actor_user_id UUID REFERENCES profiles(id),
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    ip_address TEXT,
    details TEXT NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
