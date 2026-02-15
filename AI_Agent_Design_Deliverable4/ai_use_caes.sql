CREATE INDEX idx_agent_team_id
ON public.new_unified_agents(source_team_id);

CREATE INDEX idx_agent_confidence
ON public.new_unified_agents(confidence_score);

CREATE INDEX idx_agent_needs_review
ON public.new_unified_agents(needs_review);

CREATE INDEX idx_agent_designation
ON public.new_unified_agents USING gin (designation gin_trgm_ops);



-- Territory Coverage Intelligence
-- Business Question
-- Do we have enough agent penetration in a specific region or team?

EXPLAIN ANALYZE
SELECT
    source_team_id AS team_id,
    COUNT(1) AS total_agents,

    COUNT(1) FILTER (
        WHERE confidence_score >= 80
    ) AS high_confidence_agents,

    ROUND(
        COUNT(1) FILTER (WHERE confidence_score >= 80)::numeric
        / NULLIF(COUNT(*), 0), 2
    ) AS high_confidence_ratio,

    COUNT(1) FILTER (
        WHERE COALESCE(array_length(emails, 1), 0) > 0
          AND COALESCE(array_length(phone_numbers, 1), 0) > 0
    ) AS complete_contacts,

    ROUND(
        COUNT(1) FILTER (
            WHERE COALESCE(array_length(emails, 1), 0) > 0
              AND COALESCE(array_length(phone_numbers, 1), 0) > 0
        )::numeric
        / NULLIF(COUNT(1), 0), 2
    ) AS contact_completeness_ratio,

    ROUND(
        (
            COUNT(1) FILTER (WHERE confidence_score >= 80) * 0.6 +
            COUNT(1) FILTER (
                WHERE COALESCE(array_length(emails, 1), 0) > 0
                  AND COALESCE(array_length(phone_numbers, 1), 0) > 0
            ) * 0.4
        )::numeric
        / NULLIF(COUNT(1), 0), 2
    ) AS coverage_score

FROM public.new_unified_agents
GROUP BY source_team_id
ORDER BY coverage_score DESC;

-- Explain ANALYZE RESULT 

[
  {
    "QUERY PLAN": "Sort  (cost=2423.96..2435.03 rows=4428 width=136) (actual time=24.758..25.022 rows=4659 loops=1)"
  },
  {
    "QUERY PLAN": "  Sort Key: (round(((((count(1) FILTER (WHERE (confidence_score >= 80)))::numeric * 0.6) + ((count(1) FILTER (WHERE ((COALESCE(array_length(emails, 1), 0) > 0) AND (COALESCE(array_length(phone_numbers, 1), 0) > 0))))::numeric * 0.4)) / (NULLIF(count(1), 0))::numeric), 2)) DESC"
  },
  {
    "QUERY PLAN": "  Sort Method: quicksort  Memory: 536kB"
  },
  {
    "QUERY PLAN": "  ->  HashAggregate  (cost=1901.18..2155.79 rows=4428 width=136) (actual time=17.402..22.589 rows=4659 loops=1)"
  },
  {
    "QUERY PLAN": "        Group Key: source_team_id"
  },
  {
    "QUERY PLAN": "        Batches: 1  Memory Usage: 721kB"
  },
  {
    "QUERY PLAN": "        ->  Seq Scan on new_unified_agents  (cost=0.00..1062.48 rows=33548 width=75) (actual time=0.010..3.694 rows=33548 loops=1)"
  },
  {
    "QUERY PLAN": "Planning Time: 0.833 ms"
  },
  {
    "QUERY PLAN": "Execution Time: 25.597 ms"
  }
]

-- 2. High-Value Outreach Target Builder
-- Business Question
-- Who are the most reliable, verified agents we can target?

EXPLAIN ANALYZE
SELECT
    agent_id,
    full_name,
    designation,
    emails,
    phone_numbers,
    confidence_score
FROM public.new_unified_agents
WHERE confidence_score >= 80
  AND needs_review = false
  AND array_length(emails, 1) > 0
  AND array_length(phone_numbers, 1) > 0
ORDER BY confidence_score DESC;

-- Explain ANALYZE RESULT 
[
  {
    "QUERY PLAN": "Index Scan Backward using idx_unified_agents_confidence on new_unified_agents  (cost=0.29..243.97 rows=13 width=106) (actual time=2.348..8.772 rows=1236 loops=1)"
  },
  {
    "QUERY PLAN": "  Index Cond: (confidence_score >= 80)"
  },
  {
    "QUERY PLAN": "  Filter: ((NOT needs_review) AND (array_length(emails, 1) > 0) AND (array_length(phone_numbers, 1) > 0))"
  },
  {
    "QUERY PLAN": "  Rows Removed by Filter: 688"
  },
  {
    "QUERY PLAN": "Planning Time: 1.542 ms"
  },
  {
    "QUERY PLAN": "Execution Time: 8.893 ms"
  }
]

-- 3. Team Influence Scoring
-- Since each agent maps to source_team_id:
-- Business Question
-- Which teams are influential based on agent density?
Explain analyze
SELECT
    source_team_id AS team_id,
    COUNT(1) AS total_agents,
    COUNT(1) FILTER (
        WHERE designation ILIKE '%Broker%'
           OR designation ILIKE '%Owner%'
    ) AS decision_makers,
    ROUND(
        COUNT(1) FILTER (
            WHERE designation ILIKE '%Broker%'
               OR designation ILIKE '%Owner%'
        )::numeric / NULLIF(COUNT(*), 0),
        2
    ) AS decision_maker_ratio,
    COUNT(1) FILTER (
        where array_length(emails, 1) > 0 AND array_length(phone_numbers, 1) > 0
    ) AS complete_contacts,
    ROUND(
        (
            COUNT(1) * 0.5 +
            COUNT(1) FILTER (
                WHERE designation ILIKE '%Broker%'
                   OR designation ILIKE '%Owner%'
            ) * 0.3 +
            COUNT(1) FILTER (
                where array_length(emails, 1) > 0 AND array_length(phone_numbers, 1) > 0
            ) * 0.2
        )::numeric,
        2
    ) AS influence_score
FROM public.new_unified_agents
GROUP BY source_team_id
ORDER BY influence_score DESC;

-- Explain ANALYZE RESULT 
[
  {
    "QUERY PLAN": "Sort  (cost=2452.48..2463.55 rows=4428 width=104) (actual time=68.440..68.718 rows=4659 loops=1)"
  },
  {
    "QUERY PLAN": "  Sort Key: (round(((((count(1))::numeric * 0.5) + ((count(1) FILTER (WHERE ((designation ~~* '%Broker%'::text) OR (designation ~~* '%Owner%'::text))))::numeric * 0.3)) + ((count(1) FILTER (WHERE ((array_length(emails, 1) > 0) AND (array_length(phone_numbers, 1) > 0))))::numeric * 0.2)), 2)) DESC"
  },
  {
    "QUERY PLAN": "  Sort Method: quicksort  Memory: 520kB"
  },
  {
    "QUERY PLAN": "  ->  HashAggregate  (cost=1985.05..2184.31 rows=4428 width=104) (actual time=61.320..66.261 rows=4659 loops=1)"
  },
  {
    "QUERY PLAN": "        Group Key: source_team_id"
  },
  {
    "QUERY PLAN": "        Batches: 1  Memory Usage: 721kB"
  },
  {
    "QUERY PLAN": "        ->  Seq Scan on new_unified_agents  (cost=0.00..1062.48 rows=33548 width=88) (actual time=0.012..3.977 rows=33548 loops=1)"
  },
  {
    "QUERY PLAN": "Planning Time: 0.807 ms"
  },
  {
    "QUERY PLAN": "Execution Time: 69.289 ms"
  }
]

-- 4. Agent Seniority & Role Intelligence
-- Business Question
-- How many decision-makers do we have?
EXPLAIN analyze
SELECT
    CASE
        WHEN designation ILIKE '%Broker%'
          OR designation ILIKE '%Owner%'
          OR designation ILIKE '%Attorney%'
          OR designation ILIKE '%Broker-in-Charge%'
        THEN 'Decision_Maker'

        WHEN designation ILIKE '%Realtor%'
        THEN 'Influencer'

        WHEN designation IS NULL
        THEN 'Unclassified'

        ELSE 'Individual_Agent'
    END AS role_category,
    COUNT(1) AS agent_count
FROM public.new_unified_agents
GROUP BY role_category
ORDER BY agent_count DESC;

-- Explain ANALYZE RESULT 
[
  {
    "QUERY PLAN": "Sort  (cost=1957.63..1967.03 rows=3762 width=40) (actual time=107.632..107.634 rows=4 loops=1)"
  },
  {
    "QUERY PLAN": "  Sort Key: (count(1)) DESC"
  },
  {
    "QUERY PLAN": "  Sort Method: quicksort  Memory: 25kB"
  },
  {
    "QUERY PLAN": "  ->  HashAggregate  (cost=1649.57..1734.22 rows=3762 width=40) (actual time=107.588..107.612 rows=4 loops=1)"
  },
  {
    "QUERY PLAN": "        Group Key: CASE WHEN ((designation ~~* '%Broker%'::text) OR (designation ~~* '%Owner%'::text) OR (designation ~~* '%Attorney%'::text) OR (designation ~~* '%Broker-in-Charge%'::text)) THEN 'Decision_Maker'::text WHEN (designation ~~* '%Realtor%'::text) THEN 'Influencer'::text WHEN (designation IS NULL) THEN 'Unclassified'::text ELSE 'Individual_Agent'::text END"
  },
  {
    "QUERY PLAN": "        Batches: 1  Memory Usage: 217kB"
  },
  {
    "QUERY PLAN": "        ->  Seq Scan on new_unified_agents  (cost=0.00..1481.83 rows=33548 width=32) (actual time=0.052..99.823 rows=33548 loops=1)"
  },
  {
    "QUERY PLAN": "Planning Time: 0.697 ms"
  },
  {
    "QUERY PLAN": "Execution Time: 107.885 ms"
  }
]

-- 5. Data Trust & Reliability Dashboard
-- How reliable is our master dataset? How many new agents are added to master dataset.

SELECT
    COUNT(1) AS total_agents,

    ROUND(
        COUNT(1) FILTER (WHERE confidence_score >= 80)::numeric
        / NULLIF(COUNT(1), 0) * 100, 2
    ) AS high_confidence_percentage,

    ROUND(
        COUNT(1) FILTER (WHERE needs_review = true)::numeric
        / NULLIF(COUNT(1), 0) * 100, 2
    ) AS needs_review_percentage,

    ROUND(
        COUNT(1) FILTER (
            WHERE COALESCE(array_length(emails, 1), 0) = 0
        )::numeric
        / NULLIF(COUNT(1), 0) * 100, 2
    ) AS missing_email_percentage,

    ROUND(
        COUNT(1) FILTER (
            WHERE COALESCE(array_length(phone_numbers, 1), 0) = 0
        )::numeric
        / NULLIF(COUNT(1), 0) * 100, 2
    ) AS missing_phone_percentage

FROM public.new_unified_agents;

-- Explain ANALYZE RESULT 
[
  {
    "QUERY PLAN": "Aggregate  (cost=1901.18..1901.25 rows=1 width=136) (actual time=13.351..13.352 rows=1 loops=1)"
  },
  {
    "QUERY PLAN": "  ->  Seq Scan on new_unified_agents  (cost=0.00..1062.48 rows=33548 width=60) (actual time=0.014..3.544 rows=33548 loops=1)"
  },
  {
    "QUERY PLAN": "Planning Time: 0.765 ms"
  },
  {
    "QUERY PLAN": "Execution Time: 13.465 ms"
  }
]


