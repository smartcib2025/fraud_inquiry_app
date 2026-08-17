-- CPPD Investigation OS - Row Level Security (RLS) Policies (Phase 1)

-- Enable RLS on core tables
ALTER TABLE public.cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.case_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.victims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.witnesses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.suspects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.statements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chain_of_custody ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.investigation_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_events ENABLE ROW LEVEL SECURITY;

-- Helper function to retrieve the current user's profile and check roles
CREATE OR REPLACE FUNCTION public.get_current_user_role()
RETURNS TEXT AS $$
DECLARE
    role_name TEXT;
BEGIN
    -- Query the user_roles table based on the authenticated Supabase user ID
    SELECT role_id INTO role_name
    FROM public.user_roles
    WHERE user_id = auth.uid()
    LIMIT 1;
    
    RETURN role_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.get_current_user_unit()
RETURNS TEXT AS $$
DECLARE
    unit_name TEXT;
BEGIN
    SELECT org_unit INTO unit_name
    FROM public.profiles
    WHERE id = auth.uid()
    LIMIT 1;
    
    RETURN unit_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 1. Policies for public.cases
-- Commander: Can select all cases
CREATE POLICY commander_all_cases ON public.cases
    FOR SELECT
    USING (public.get_current_user_role() = 'commander');

-- Supervisor: Can view all cases owned by their organizational unit
CREATE POLICY supervisor_unit_cases ON public.cases
    FOR SELECT
    USING (
        public.get_current_user_role() = 'supervisor' 
        AND owning_unit = public.get_current_user_unit()
    );

-- Investigator: Can view cases only if they are a member of the case
CREATE POLICY investigator_assigned_cases ON public.cases
    FOR SELECT
    USING (
        public.get_current_user_role() = 'investigator'
        AND EXISTS (
            SELECT 1 FROM public.case_members 
            WHERE case_members.case_id = cases.id 
            AND case_members.user_id = auth.uid()
        )
    );

-- Write/Update Policies for public.cases
CREATE POLICY supervisor_commander_write_cases ON public.cases
    FOR ALL
    USING (
        public.get_current_user_role() IN ('supervisor', 'commander')
    );

CREATE POLICY investigator_write_assigned_cases ON public.cases
    FOR UPDATE
    USING (
        public.get_current_user_role() = 'investigator'
        AND EXISTS (
            SELECT 1 FROM public.case_members 
            WHERE case_members.case_id = cases.id 
            AND case_members.user_id = auth.uid()
        )
    );


-- 2. Policies for case subjects (victims, witnesses, suspects)
-- Grant select access based on case access
CREATE POLICY select_victims ON public.victims
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = victims.case_id
        )
    );

CREATE POLICY select_witnesses ON public.witnesses
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = witnesses.case_id
        )
    );

CREATE POLICY select_suspects ON public.suspects
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = suspects.case_id
        )
    );

-- 3. Policies for evidence & custody logs
CREATE POLICY select_evidence ON public.evidence
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = evidence.case_id
        )
    );

CREATE POLICY select_chain_of_custody ON public.chain_of_custody
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.evidence
            JOIN public.cases ON cases.id = evidence.case_id
            WHERE evidence.id = chain_of_custody.evidence_id
        )
    );

-- 4. Policies for statements
CREATE POLICY select_statements ON public.statements
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = statements.case_id
        )
    );

-- 5. Policies for tasks
CREATE POLICY select_tasks ON public.investigation_tasks
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM public.cases
            WHERE cases.id = investigation_tasks.case_id
        )
    );

CREATE POLICY update_tasks ON public.investigation_tasks
    FOR UPDATE
    USING (
        assigned_to = auth.uid()
        OR public.get_current_user_role() IN ('supervisor', 'commander')
    );

-- 6. Audit Triggers Setup
CREATE OR REPLACE FUNCTION public.log_audit_change()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.audit_events (user_id, action, table_name, record_id, query_details)
    VALUES (
        auth.uid(),
        TG_OP,
        TG_TABLE_NAME,
        COALESCE(NEW.id::text, OLD.id::text),
        'Executed database ' || TG_OP || ' operation'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add audit triggers to critical tables
CREATE TRIGGER audit_cases_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.cases
    FOR EACH ROW EXECUTE FUNCTION public.log_audit_change();

CREATE TRIGGER audit_evidence_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.evidence
    FOR EACH ROW EXECUTE FUNCTION public.log_audit_change();

CREATE TRIGGER audit_statements_trigger
    AFTER INSERT OR UPDATE OR DELETE ON public.statements
    FOR EACH ROW EXECUTE FUNCTION public.log_audit_change();
