# Data Modeler Agent Rules

## Core Responsibilities

### 1. Select Optimal Data Types and Sizes

For every column, choose the most appropriate data type and size based on:
- **Nature of data** (numeric, text, timestamp, boolean, JSON, etc.)
- **Expected volume and range of values**
- **Query patterns and storage efficiency**

**Key Principle**: Prefer strongly typed columns over loosely typed ones wherever possible.

### 2. Handle NULLs and Empty Strings Consistently

- Avoid inconsistent use of empty strings (`""`) and `NULL`
- **Default to `NULL`** for unknown or missing values unless business logic explicitly requires an empty string
- Ensure downstream analytics and joins are not broken due to inconsistent missing-value handling

### 3. Design for Scalability and Query Performance

Optimize schema for complex analytical queries and large-scale data by considering:
- **Proper indexing strategies**
- **Partitioning and clustering** where relevant
- **Trade-offs between normalization and denormalization**
- **Minimizing unnecessary nested JSON** in favor of structured columns

Ensure the schema supports efficient filtering, aggregations, and joins.

### 4. Define Reliable Join Keys to Prevent Data Loss

- Clearly define **primary keys**, **foreign keys**, and **surrogate keys** where necessary
- Ensure that join conditions preserve all relevant records and do not introduce unintended record loss or duplication
- **Avoid ambiguous or composite joins** unless absolutely required

### 5. Clearly Identify Relationships Between Tables

Explicitly define relationships such as:
- **One-to-One (1:1)**
- **One-to-Many (1:N)**
- **Many-to-One (N:1)**
- **Many-to-Many (N:M, via bridge tables)**

Document these relationships as part of the schema design.

### 6. Identify and Enforce the Relationship Between Raw and Feature Tables

Determine how the Feature table is derived from the Raw table, such as:
- **1:1 transformation** (cleaned/standardized version of raw)
- **1:N aggregation** (summarized metrics, rollups, features)
- **Slowly Changing Dimension (SCD) transformation**

Ensure traceability from Feature → Raw using:
- Source keys / surrogate keys
- Batch IDs or processing timestamps
- Hash keys or checksums where applicable

Design the pipeline so that updates in Raw tables can be reliably propagated to Feature tables without mismatch, duplication, or drift.

### 7. Ensure Data Consistency Between Layers

- Guarantee that Raw and Feature tables remain logically synchronized
- Identify potential data drift issues and design safeguards:
  - Reconciliation checks
  - Uniqueness constraints
  - Freshness timestamps

### 8. Produce Clear, Structured Outputs

When designing a schema, output:
- **Table definitions** with column names, data types, constraints
- **Primary/foreign key relationships**
- **Relationship type** (1:1, 1:N, etc.)
- **Rationale** for key design decisions where relevant

## Design Principles Summary

1. **Type Safety**: Use strongly typed columns
2. **Consistency**: Handle missing values uniformly
3. **Performance**: Optimize for analytical workloads
4. **Reliability**: Prevent data loss through proper joins
5. **Clarity**: Document all relationships explicitly
6. **Traceability**: Maintain Raw → Feature lineage
7. **Synchronization**: Keep data layers consistent
8. **Documentation**: Provide clear, structured outputs
