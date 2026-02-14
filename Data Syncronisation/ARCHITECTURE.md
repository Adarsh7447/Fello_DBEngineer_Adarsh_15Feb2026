# System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Synchronization Pipeline                │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Developer  │────────▶│  deploy.py   │────────▶│   Database   │
│              │         │              │         │  (Supabase)  │
└──────────────┘         └──────────────┘         └──────────────┘
                                │
                                │
                    ┌───────────┼───────────┐
                    │           │           │
                    ▼           ▼           ▼
            ┌──────────┐ ┌──────────┐ ┌──────────┐
            │   SQL    │ │   Data   │ │  Config  │
            │ Deployer │ │  Loader  │ │ Manager  │
            └──────────┘ └──────────┘ └──────────┘
                    │           │           │
                    └───────────┼───────────┘
                                │
                                ▼
                        ┌──────────────┐
                        │ DB Manager   │
                        │ (Connection  │
                        │   Pooling)   │
                        └──────────────┘
```

## Component Architecture

### 1. Entry Point Layer

```
deploy.py
├── Command-line argument parsing
├── Environment configuration
├── Logging setup
├── Orchestration logic
└── Report generation
```

### 2. Orchestration Layer

```
deployer/
├── sql_deployer.py
│   ├── DDL deployment
│   ├── Function deployment
│   ├── Trigger deployment
│   ├── RLS deployment
│   └── Verification
│
└── data_loader.py
    ├── CSV loading
    ├── Pipeline execution
    ├── Statistics collection
    └── Error handling
```

### 3. Utility Layer

```
utils/
├── db_manager.py
│   ├── Connection pooling
│   ├── Transaction management
│   ├── Query execution
│   └── Helper methods
│
└── config.py
    ├── Environment variables
    ├── Configuration validation
    └── Multi-environment support
```

## Data Flow

### Deployment Flow

```
1. User runs: python deploy.py --full
                    │
                    ▼
2. Load configuration from .env
                    │
                    ▼
3. Initialize database connection pool
                    │
                    ▼
4. Deploy SQL components
   ├── DDL (Tables, Indexes)
   ├── Functions
   ├── Triggers
   └── RLS Policies
                    │
                    ▼
5. Verify deployment
   ├── Check tables exist
   ├── Check functions exist
   └── Validate structure
                    │
                    ▼
6. Load CSV data
   ├── raw_company_info.csv → bronze.company_info_raw
   └── new_agents.csv → public.new_agents
                    │
                    ▼
7. Execute data pipeline
   ├── run_unified_member_pipeline()
   └── run_unified_merge_batch()
                    │
                    ▼
8. Generate deployment report
   └── logs/deployment_report.json
```

### Data Processing Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Data Processing Pipeline                 │
└─────────────────────────────────────────────────────────────┘

CSV Files
    │
    ├── raw_company_info.csv
    │        │
    │        ▼
    │   bronze.company_info_raw (Raw JSONB data)
    │        │
    │        ▼
    │   run_unified_member_pipeline()
    │        │
    │        ▼
    │   public.unified_company_member (Normalized)
    │        │
    │        └──────┐
    │               │
    └── new_agents.csv
             │
             ▼
        public.new_agents
             │
             └──────┐
                    │
                    ▼
            run_unified_merge_batch()
                    │
                    ├── Match by email (confidence: 100)
                    ├── Match by phone (confidence: 90)
                    ├── Match by name+team (confidence: 80)
                    └── Fuzzy name match (confidence: 60)
                    │
                    ▼
        public.new_unified_agents (Master table)
                    │
                    ├── High confidence (>70): Auto-merged
                    └── Low confidence (≤70): Flagged for review
```

## Database Schema Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Database Schemas                      │
└─────────────────────────────────────────────────────────────┘

bronze (Raw Data)
└── company_info_raw
    ├── research_uuid (PK)
    ├── team_id
    ├── website
    ├── team_members (JSONB array)
    └── timestamps

public (Processed Data)
├── unified_company_member
│   ├── id (PK)
│   ├── research_uuid (FK)
│   ├── team_id
│   ├── member_name
│   ├── email_normalized (array)
│   ├── phone_normalized (array)
│   ├── record_hash (unique)
│   └── processed (flag)
│
├── new_agents
│   ├── supabase_uuid (PK)
│   ├── full_name
│   ├── email_clean (JSONB array)
│   ├── phone_digits (JSONB array)
│   ├── team_id
│   └── social_links (JSONB)
│
├── new_unified_agents (Master)
│   ├── agent_id (PK)
│   ├── full_name
│   ├── emails (array)
│   ├── phone_numbers (array)
│   ├── source_team_id
│   ├── confidence_score (0-100)
│   ├── needs_review (boolean)
│   └── timestamps
│
└── unified_merge_logs
    ├── id (PK)
    ├── started_at
    ├── finished_at
    ├── total_processed
    ├── status
    └── error_message
```

## Deployment Sequence Diagram

```
Developer    deploy.py    SQLDeployer    DataLoader    Database
    │            │             │              │            │
    │──run──────▶│             │              │            │
    │            │             │              │            │
    │            │──init──────▶│              │            │
    │            │             │              │            │
    │            │             │──DDL────────────────────▶│
    │            │             │◀─────────────────────────│
    │            │             │              │            │
    │            │             │──Functions──────────────▶│
    │            │             │◀─────────────────────────│
    │            │             │              │            │
    │            │             │──Triggers───────────────▶│
    │            │             │◀─────────────────────────│
    │            │             │              │            │
    │            │             │──RLS────────────────────▶│
    │            │             │◀─────────────────────────│
    │            │             │              │            │
    │            │──verify────▶│              │            │
    │            │◀────ok──────│              │            │
    │            │             │              │            │
    │            │──────────────init─────────▶│            │
    │            │             │              │            │
    │            │             │              │──CSV──────▶│
    │            │             │              │◀───────────│
    │            │             │              │            │
    │            │             │              │──Pipeline─▶│
    │            │             │              │◀───────────│
    │            │             │              │            │
    │            │◀──────────report───────────│            │
    │◀─success───│             │              │            │
```

## Connection Pool Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Connection Pool Manager                   │
└─────────────────────────────────────────────────────────────┘

Application Threads
    │   │   │   │
    ▼   ▼   ▼   ▼
┌─────────────────────┐
│  Connection Pool    │
│  (ThreadedPool)     │
│                     │
│  ┌───┐ ┌───┐ ┌───┐ │
│  │ C │ │ C │ │ C │ │  C = Connection
│  └───┘ └───┘ └───┘ │
│  ┌───┐ ┌───┐       │
│  │ C │ │ C │       │
│  └───┘ └───┘       │
└─────────────────────┘
         │
         ▼
    PostgreSQL
     Database

Features:
- Min connections: 1
- Max connections: 10
- Thread-safe
- Auto-reconnect
- Connection reuse
```

## Error Handling Flow

```
Operation Start
    │
    ▼
Try Block
    │
    ├─Success──────────────────┐
    │                          │
    └─Exception                │
         │                     │
         ▼                     │
    Catch Block               │
         │                     │
         ├─Log Error           │
         ├─Rollback Txn        │
         ├─Update Status       │
         └─Raise Exception     │
                               │
                               ▼
                          Finally Block
                               │
                               ├─Close Cursor
                               ├─Return Connection
                               └─Generate Report
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Security Layers                         │
└─────────────────────────────────────────────────────────────┘

1. Environment Variables
   └── Credentials never hardcoded
   └── .env file (gitignored)

2. Connection Security
   └── SSL/TLS support
   └── Connection pooling limits
   └── Timeout configuration

3. SQL Injection Prevention
   └── Parameterized queries
   └── No string concatenation
   └── Input validation

4. Row Level Security (RLS)
   └── Optional RLS policies
   └── Table-level security
   └── User-based access control

5. Transaction Isolation
   └── ACID compliance
   └── Automatic rollback
   └── Deadlock prevention
```

## Logging Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Logging System                          │
└─────────────────────────────────────────────────────────────┘

Application Code
    │
    ├─────────────────┬─────────────────┐
    │                 │                 │
    ▼                 ▼                 ▼
Console Handler   File Handler    JSON Reporter
    │                 │                 │
    ▼                 ▼                 ▼
  stdout         logs/*.log    deployment_report.json

Log Levels:
- DEBUG: Detailed diagnostic info
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages

Log Format:
TIMESTAMP | LEVEL | MODULE | MESSAGE
```

## Scalability Considerations

### Horizontal Scaling
- Connection pooling supports multiple workers
- Stateless design allows parallel execution
- Independent deployment per environment

### Vertical Scaling
- Configurable batch sizes
- Adjustable connection pool size
- Memory-efficient streaming for large CSVs

### Performance Optimization
- Bulk COPY for data loading
- Indexed columns for fast lookups
- GIN indexes for array searches
- Materialized views (future)

## Monitoring Points

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Points                         │
└─────────────────────────────────────────────────────────────┘

1. Deployment Metrics
   ├── Deployment duration
   ├── Success/failure rate
   ├── Scripts executed count
   └── Error frequency

2. Data Quality Metrics
   ├── Row counts per table
   ├── Confidence score distribution
   ├── Records needing review
   └── Duplicate detection rate

3. Performance Metrics
   ├── Query execution time
   ├── Connection pool utilization
   ├── CSV load speed
   └── Pipeline execution time

4. System Metrics
   ├── Database connection count
   ├── Memory usage
   ├── Disk I/O
   └── CPU utilization
```

## Extension Points

### Adding New Tables
1. Create DDL in `Supabase_replicate/DDL/`
2. Add to `DEPLOYMENT_ORDER` in `sql_deployer.py`
3. Update verification in `verify_deployment.py`

### Adding New Functions
1. Create SQL in `Supabase_replicate/FUNCTIONS/`
2. Add to `DEPLOYMENT_ORDER` in `sql_deployer.py`
3. Update verification checks

### Adding New Data Sources
1. Add CSV to `Supabase_replicate/CSVs/`
2. Update `CSV_TABLE_MAPPING` in `data_loader.py`
3. Create corresponding DDL

### Custom Pipeline Steps
1. Create new script in `scripts/`
2. Import utilities from `utils/`
3. Follow logging patterns
4. Add to documentation

---

**Architecture Version**: 1.0  
**Last Updated**: 2024  
**Status**: Production Ready
