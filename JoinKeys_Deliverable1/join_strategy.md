# Deliverable 1: Entity Mapping & Matching Strategy

**Prepared By:** Adarsh Badjate
**Date:** 15-Feb-2026

## 1. Objective

This document details the production-grade entity resolution framework designed to unify raw, semi-structured research data with a structured master agent dataset. The strategy involves a two-step process: first flattening the raw data into a relational format, and then applying a hierarchical, team-scoped matching model to ensure accurate data consolidation.

## 2. Architectural Solution: Data Flattening

The primary challenge is the `team_members` JSONB array within the raw `public.company_info_raw` table. Direct joins on nested JSON are inefficient and not scalable. To solve this, a Silver Layer table, `public.unified_company_member`, was created to hold a structured, relational version of this data.

### Transformation Process (`run_unified_member_pipeline`)

1.  **Unnesting (Explosion)**: The `jsonb_array_elements()` function is used to "explode" the `team_members` array. Each JSON object representing an agent becomes a separate row in the result set.

2.  **Cleaning & Normalization**: For each new row, the following transformations are applied:
    *   **Contact Normalization**: Email and phone strings are parsed, split by common delimiters, and converted into standardized `TEXT[]` arrays.
    *   **Data Cleaning**: Whitespace is trimmed, and emails are lowercased to ensure consistency.
    *   **Phone Standardization**: All non-numeric characters are stripped from phone numbers.

3.  **Deduplication**: A deterministic `record_hash` is generated via `md5()` on the core attributes. This hash is used with an `ON CONFLICT DO NOTHING` clause to ensure the flattening process is idempotent and does not create duplicate entries in the `unified_company_member` table.

This flattening step is the essential prerequisite for performing efficient and reliable relational joins.

## 3. Final Join Key Strategy (Hierarchical Matching Model)

With the data flattened, the `run_unified_merge_batch` function joins the Silver layer (`public.unified_company_member`) with the master data (`public.new_agents`).

**A critical aspect of this strategy is that all matching is pre-filtered by `team_id`.** The `LEFT JOIN` is performed `ON ucm.team_id = na.team_id`, meaning the hierarchical matching engine only compares records that already belong to the same team. This dramatically reduces the risk of false positives.

### Revised Hierarchical Matching Logic

The engine evaluates potential matches in priority order and stops at the first satisfied condition.

| Priority | Effective Match Type | Confidence | SQL Logic |
| :--- | :--- | :--- | :--- |
| **1** | **Email + Team** | `100` | `ucm.email_normalized && na.email_clean AND ucm.team_id = na.team_id` |
| **2** | **Phone + Team** | `90` | `ucm.phone_normalized && na.phone_digits AND ucm.team_id = na.team_id` |
| **3** | **Exact Name + Team** | `80` | `lower(ucm.member_name) = lower(na.full_name) AND ucm.team_id = na.team_id` |
| **4** | **Fuzzy Name + Team** | `60` | `similarity(ucm.member_name, na.full_name) > 0.8 AND ucm.team_id = na.team_id` |

### Confidence Tiers & Review Workflow

This team-scoped model provides a clear and reliable workflow for data governance.

| Tier | Match Type | Confidence | Manual Review Required |
| :--- | :--- | :--- | :--- |
| **Exact** | Email + Team | `100` | No |
| **High** | Phone + Team | `90` | No |
| **Medium** | Name + Team | `80` | No |
| **Low** | Fuzzy Name + Team | `60` | **Yes** |
| **New** | No Match Found | `0` | **Yes** |

Records with a confidence score of 60 or less are automatically flagged (`needs_review = true`) for manual verification, ensuring that only high-confidence matches are fully automated.

## 4. Conclusion

This two-part strategy effectively solves the challenge of integrating semi-structured data. By first **flattening** the JSON into a relational format and then applying a **team-scoped hierarchical matching model**, the framework achieves:

-   **High Accuracy**: Pre-scoping matches by `team_id` is the most significant factor in preventing false merges.
-   **Scalability**: The process avoids inefficient JSON operations in favor of optimized relational joins.
-   **Auditable Governance**: The confidence scoring and review flags provide a clear system for managing data quality.

The resulting pipeline is a robust, production-grade solution for accurate master data consolidation.
