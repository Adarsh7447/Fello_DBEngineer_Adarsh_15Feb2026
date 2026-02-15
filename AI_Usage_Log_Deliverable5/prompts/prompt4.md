Objective
- Design and implement a PostgreSQL-based integration pipeline that merges data from:
- silver.company_team_members
- public.new_agents

into a new master table:
- public.new_unified_agents

This system must support:

1.Deterministic matching
2.Confidence scoring
3.Multi-value array merging
4.Idempotent execution
5.Manual review flagging


Business Rules
Identity Resolution Hierarchy

Matching priority must follow this exact order:

1.Exact Email Match
If ctm.email exists inside na.email_clean
Confidence Score = 100

2.Exact Phone Match
If ctm.phone exists inside na.phone_digits
Confidence Score = 90

3.Exact Name + Team Match
lower(ctm.name) = lower(na.full_name)
AND ctm.team_id = na.team_id
Confidence Score = 80

4.Fuzzy Name + Team Match
similarity(ctm.name, na.full_name) > 0.8
Confidence Score = 65
Flag for manual review

5.If no match found → Insert as new record


CREATE TABLE public.new_unified_agents (
    agent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    full_name TEXT,
    designation TEXT,

    emails TEXT[] DEFAULT '{}',
    phone_numbers TEXT[] DEFAULT '{}',

    source_team_id UUID,

    confidence_score INTEGER,
    needs_review BOOLEAN DEFAULT FALSE,

    source_metadata JSONB DEFAULT '{}',

    last_updated TIMESTAMPTZ DEFAULT NOW()
);

Merge Rules
When a match is found:
1.Do NOT overwrite non-null existing values.
2.Append new emails into emails[] without duplicates.
3.Append new phones into phone_numbers[] without duplicates.
4.Preserve existing arrays.
5.Update confidence_score only if new score is higher.
6.Update last_updated timestamp.
7.Set needs_review = TRUE if confidence < 70.


Data Protection Rules
1.Never delete existing array values.
2.Never overwrite full_name unless higher confidence match.
3.Never merge records based on name alone without team match.
4.Prevent duplicate unified records on repeated runs (idempotency required).

Technical Requirements
1.Use pg_trgm extension for fuzzy matching.
2.Use GIN indexes on JSON and array columns where needed.
3.Avoid CROSS JOIN explosion.
4.Use UPSERT logic (ON CONFLICT).
5.Must be re-runnable safely.

Expected Behavior
If:
1.One agent has multiple phones → store all in phone_numbers[]
2.One agent has multiple emails → store all in emails[]
3.Shared email detected across many names → lower confidence + set review flag
4.Script runs twice → no duplicate rows created

Deliverables Required From AI
1.CREATE TABLE statement
2.Index creation
3.Matching CTE logic
4.UPSERT merge query
5.Confidence scoring logic
6.Manual review flag logic
7.Idempotent implementation