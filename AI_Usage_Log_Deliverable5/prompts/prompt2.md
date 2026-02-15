I have been provided two CSV files:

1. companyinfo.csv → Contains research/raw data collected externally.
2. new_agents.csv → Contains master data for agents already in our production system.

Business Context:
Our company builds intelligent agents that trigger emails and perform automated actions for real estate agents based on their database.

We receive periodic research data (companyinfo.csv) and want to enrich our existing master dataset (new_agents.csv) using this incoming data.

Objective:
Design a production-ready data matching and enrichment strategy to:

1. Identify and define the relationship between the two datasets.
2. Determine robust join keys.
3. Handle partial matches and fuzzy matching.
4. Prevent false positives.
5. Support scalable, concurrent production workloads.

Reference Document:
Use the file located at:
`/Users/adarshbadjate/code/Data Syncronisation/Deliverables/Task1.md`

Deliverables Required:

1. Schema Analysis
   - Analyze both CSV structures.
   - Identify potential primary keys and candidate matching attributes.

2. Join Key Strategy
   - Define strong match keys (exact match).
   - Define secondary match keys (partial/fuzzy match).
   - Rank match confidence levels.

3. Matching Logic Design
   - Exact match rules (email, phone, UUID, etc.)
   - Domain-level matching (email domain, website)
   - Name similarity (handle spelling variations)
   - Handle missing/null values
   - Deduplication strategy

4. Partial Match Handling
   - Define fuzzy matching thresholds.
   - Define tie-breaking rules.
   - Avoid incorrect merges.
   - Handle multiple candidates.

5. Production-Ready Design
   - Idempotent enrichment strategy.
   - Deterministic matching.
   - Audit logging of match decisions.
   - Conflict resolution logic.
   - Support concurrent processing.

6. Output
   - Clear explanation of matching architecture.
   - Suggested SQL logic or Python-based approach.
   - Confidence scoring framework.
   - Recommended data model changes if needed.

The solution must be production-grade, scalable, and suitable for real-time or batch synchronization pipelines.
