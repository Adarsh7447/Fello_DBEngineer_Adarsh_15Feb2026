CREATE TABLE IF NOT EXISTS public.new_agents (
    supabase_uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT,
    first_name TEXT,
    last_name TEXT,    -- Raw collected emails
    email TEXT[] NOT NULL DEFAULT '{}',
    email_clean TEXT[] NOT NULL DEFAULT '{}',
    phone TEXT[] NOT NULL DEFAULT '{}',
    phone_digits TEXT[] NOT NULL DEFAULT '{}',
    team_id UUID,
    social_links JSONB DEFAULT '{}'::jsonb,
    facebook TEXT,
    instagram TEXT,
    social_score TEXT,
    brokerage TEXT,
    crm JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE public.new_agents IS 
    'Master table for agent data from various sources';