# Case Study: Zero-Downtime Primary Key Migration

**Scenario:** Renaming a Primary Key (`user_id` to `patient_id`) in a live production database serving Power BI analytics.

## 1. The Challenge: The Ripple Effect of a Primary Key

In a previous project, a critical business requirement emerged to rename the `user_id` column to `patient_id` for semantic clarity and to align with healthcare data standards. However, this was not a simple rename operation.

-   **Widespread Dependencies**: `user_id` was the Primary Key in the main `users` table and was referenced as a Foreign Key in dozens of downstream tables (e.g., `appointments`, `prescriptions`, `visits`).
-   **Live Analytics**: Production Power BI reports and dashboards were directly dependent on this key for all joins and data models.
-   **High Risk of Failure**: A direct `ALTER TABLE ... RENAME COLUMN` would instantly invalidate all foreign key constraints, breaking the entire data model and causing catastrophic failure for both the backend application and all Power BI reports.
-   **Unacceptable Downtime**: The required "big bang" approach of taking the system offline to fix all dependencies was not a viable option for a production environment.

## 2. The Strategy: The "Expand, Migrate, Contract" Model

To avoid downtime and mitigate risk, we adopted a phased approach known as the "Expand, Migrate, Contract" pattern. This strategy allows for incremental changes without breaking existing functionality at any step.

1.  **Expand (Non-Breaking)**: Introduce the new schema elements (`patient_id`, `patients` table) *in parallel* with the old ones. The system now supports both old and new structures.
2.  **Migrate (Incremental)**: Gradually shift data and application logic to use the new structures. This phase involves backfilling data and implementing dual-writing in the application layer.
3.  **Contract (Cleanup)**: Once all consumers (backend, Power BI) have fully migrated to the new schema, safely remove the old, now-unused structures (`user_id`).

## 3. Step-by-Step Implementation Plan

### Phase 1: Expand — Adding the New Schema (Zero Downtime)

This phase was designed to be completely non-disruptive.

1.  **Create the New Canonical Table**: A new `patients` table was created to be the future source of truth. The old `users` table was marked for deprecation.

    ```sql
    CREATE TABLE patients (
        patient_id BIGINT PRIMARY KEY,
        -- other patient-specific columns...
    );
    ```

2.  **Add Nullable Foreign Key Columns**: A new, *nullable* `patient_id` column was added to all dependent tables. Making it nullable was crucial to prevent locking and validation errors on a live table with millions of rows.

    ```sql
    ALTER TABLE appointments
    ADD COLUMN patient_id BIGINT NULL;

    ALTER TABLE prescriptions
    ADD COLUMN patient_id BIGINT NULL;
    -- ... repeated for all dependent tables
    ```

At the end of this phase, the schema was expanded, but application and report logic remained completely unchanged and fully functional.

### Phase 2: Migrate — The Gradual Transition

This was the most critical phase, involving both data and application changes.

1.  **Backfill Data**: A one-off script was executed during a low-traffic period to populate the new structures.

    ```sql
    -- Step A: Populate the new patients table from the old users table.
    INSERT INTO patients (patient_id, ...)
    SELECT user_id, ... FROM users;

    -- Step B: Backfill the new patient_id column in all dependent tables.
    UPDATE appointments a
    SET patient_id = u.user_id
    FROM users u
    WHERE a.user_id = u.user_id;
    -- ... repeated for all dependent tables
    ```

2.  **Implement Dual Writing**: The backend application's data access layer was modified. When a new user was created or updated, the logic would now write to **both** the old `users` table and the new `patients` table. This ensured data consistency between the old and new schemas during the transition period.

3.  **Migrate Consumers (Backend & Power BI)**:
    -   **Backend**: A feature flag was introduced. When enabled, the backend would read from and join on the new `patient_id` column instead of `user_id`.
    -   **Power BI**: A new version of the data source was created in Power BI. This new version used `patient_id` for all relationships. The BI team could validate the new reports against the old ones without impacting production dashboards.

4.  **Enforce Constraints**: Once the backfill was complete and dual-writing was live, we could safely add `NOT NULL` and `FOREIGN KEY` constraints to the `patient_id` columns.

### Phase 3: Contract — Cleaning Up the Old Schema

This phase was initiated only after confirming that no systems were reading from the old `user_id` columns.

1.  **Remove Dual-Writing Logic**: The application code was simplified to only write to the new `patients` table and `patient_id` columns.

2.  **Drop Old Columns**: The `user_id` columns from all dependent tables were safely dropped.

    ```sql
    ALTER TABLE appointments DROP COLUMN user_id;
    ```

3.  **Decommission Old Table**: Finally, the now-obsolete `users` table was archived and dropped.

## 4. Key Outcomes & Benefits

-   **Zero Downtime**: The entire migration was performed on a live production system without any service interruption.
-   **Reduced Risk**: The phased approach allowed for validation at every step, eliminating the risk of a "big bang" failure.
-   **Maintainability**: The final schema is semantically correct and easier for new developers and stakeholders to understand.
-   **Reversibility**: At any point during Phase 1 or 2, the process could have been safely rolled back without data loss.
-   **Parallel Work**: The BI team could work on migrating their reports in parallel with the backend team's migration, accelerating the overall project timeline.
