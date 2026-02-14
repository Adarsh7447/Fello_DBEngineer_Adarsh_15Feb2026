# 📘 Schema Evolution Strategy

**Change:** Add `agent_specialties text[]`
**Strategy:** ALTER TABLE + Versioned AI View

## 1️⃣ Objective

Introduce a new field:
`agent_specialties text[]`

**Purpose:**
- Support AI-powered specialty matching
- Enable ranking based on expertise categories
- Maintain zero downtime
- Ensure existing AI and backend queries do not break

## 2️⃣ High-Level Strategy

We will follow the **Expand → Isolate → Adopt** model.

- **Step 1 — Expand Schema (Safe Change)**: Add the column directly to the table.
- **Step 2 — Isolate AI via Versioned View**: Move AI read operations to a controlled, versioned view.
- **Step 3 — Adopt in Backend + AI**: Gradually enable the usage of the new field.

## 3️⃣ Migration Plan

### Step 1: Add Column (Non-Breaking)

```sql
ALTER TABLE public.agents
ADD COLUMN IF NOT EXISTS agent_specialties text[] DEFAULT '{}';

-- Optional index (if filtering is expected)
CREATE INDEX IF NOT EXISTS idx_agents_specialties
ON public.agents
USING GIN (agent_specialties);
```

**Why This Is Safe:**
- Nullable with a default empty array.
- No existing query references this column.
- No constraint modification.
- No lock escalation beyond a metadata change.
- **Zero downtime.**

## 4️⃣ AI Read Isolation Strategy

**❌ Current Risk:**
AI agents may be querying the raw table:
`SELECT * FROM new_unified_agents;`
This creates tight schema coupling.

**✅ New Architecture:**
We introduce a versioned "AI Contract" view.

**Version 1 (Existing AI Contract)**
```sql
CREATE OR REPLACE VIEW public.new_unified_agents_ai_v1 AS
SELECT
    agent_id,
    full_name,
    phone_numbers,
    emails,
    designation,
    confidence_score,
    needs_review,
    source_team_id
FROM public.agents;
```
AI agents will be updated to read from `agents_ai_v1`. This freezes the schema for them.

**Version 2 (With Specialties)**
```sql
CREATE VIEW public.agents_ai_v2 AS
SELECT
    agent_id,
    full_name,
    phone_numbers,
    emails,
    designation,
    confidence_score,
    needs_review,
    source_team_id,
    agent_specialties
FROM public.agents;
```
New AI logic can safely use `v2` without impacting existing models.

## 5️⃣ Versioning Strategy

We will version **AI-facing views**, not the core tables.

**Version Naming Convention:**
- `<entity>_ai_v1`
- `<entity>_ai_v2`
- `<entity>_api_v1`

**Rules:**
- Views are **immutable** once released.
- New changes require a new version.
- Deprecation window = 30 days.
- **AI agents must never directly consume tables.**

**Deprecation Workflow:**
1. Announce deprecation of the old view.
2. Monitor usage of the old view.
3. Remove the old view only after usage drops to zero.

## 6️⃣ Schema Dictionary Management

We will maintain a central Data Dictionary.

**Option A — Markdown (Simple)**
- **File:** `/docs/schema_dictionary.md`
- **Example:**
| Field | Type | Nullable | Default | Description | Version |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `id` | `uuid` | No | — | Primary key | `v1` |
| `agent_name` | `text` | No | — | Agent full name | `v1` |
| `agent_specialties` | `text[]` | Yes | `'{}'` | AI specialty tags | `v2` |

**Option B — Database-Driven Dictionary (Advanced)**
Create a dedicated table:
```sql
CREATE TABLE schema_dictionary (
    table_name text,
    column_name text,
    data_type text,
    description text,
    introduced_in_version text,
    deprecated boolean default false,
    created_at timestamptz default now()
);
```
This enables automated documentation generation, schema introspection, and metadata APIs.

## 7️⃣ Backend Transition Plan

- **Phase 1:** Backend continues reading from the `new_unified_agents` table.
- **Phase 2:** Backend read operations switch to `new_unified_agents_ai_v1` or a dedicated API view.
- **Phase 3:** A feature flag enables the backend to start using the `agent_specialties` field.

## 8️⃣ Communication Plan to AI Team

**📢 Change Announcement Template:**

**Subject:** Schema Update – Agents Table (Non-Breaking)

We are introducing a new column: `agent_specialties text[]`.

- **Purpose:** To enable specialty-based AI ranking and filtering.
- **Impact:** **No breaking changes.** Existing AI queries remain functional.
- **Action Required:**
  - Continue using `new_unified_agents_ai_v1` for existing models.
  - Migrate to `new_unified_agents_ai_v2` to leverage the new specialty matching capabilities.
- **Timeline:**
  - Migration Applied: [15-Feb-2026]
  - `v2` Available: [15-Feb-2026]
  - `v1` Deprecation Review: [15-Feb-2026 + 30 days]

## 9️⃣ Monitoring & Validation

After deployment:
- Validate null rates on the new column.
- Monitor query performance.
- Confirm AI agent queries are unaffected.
- Monitor view usage to track adoption of `v2`.

## 🔟 Governance Rules Going Forward

1.  **AI must never query raw tables.** All AI contracts must be versioned views.
2.  Breaking changes require an RFC, a 30-day deprecation notice, and dual-version support.
3.  The schema dictionary must be updated **before** deployment.
4.  All migrations must be committed to Git.

## 1️⃣1️⃣ Why This Strategy Works

- ✔️ Zero downtime
- ✔️ No foreign key, RLS, or AI breakage
- ✔️ Scalable for future changes
- ✔️ Clean separation of concerns (data vs. contract)

## 1️⃣2️⃣ Future-Proofing

If we later need to rename, change, or remove a column, the process is simple:
1.  Create a new AI view version (e.g., `v3`).
2.  Maintain the old view (`v2`).
3.  Announce deprecation.
4.  Safely remove the old view after usage ceases.

### Final Architecture Principle

- **Tables** = Source of truth
- **Views** = Contract layer
- **AI** = Consumer
- **Dictionary** = Governance
