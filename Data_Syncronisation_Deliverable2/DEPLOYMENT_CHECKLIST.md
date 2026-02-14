# Deployment Checklist

Use this checklist when deploying to a new database.

## Pre-Deployment

- [ ] Python 3.8+ installed
- [ ] Database credentials available
- [ ] Network access to database verified
- [ ] Backup of existing database (if applicable)
- [ ] CSV files present in `../Supabase_replicate/CSVs/`

## Setup

- [ ] Clone/download repository
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file from `.env.example`
- [ ] Configure `DATABASE_URL` in `.env`
- [ ] Test database connection

## Deployment Steps

### Option 1: Full Automated Deployment

```bash
# Run complete deployment
python deploy.py --full

# Verify deployment
python scripts/verify_deployment.py
```

### Option 2: Step-by-Step Deployment

```bash
# Step 1: Deploy DDL only
python deploy.py --ddl-only

# Step 2: Verify schema
python scripts/verify_deployment.py

# Step 3: Load data and run pipeline
python deploy.py --data-only

# Step 4: Final verification
python scripts/verify_deployment.py
```

## Post-Deployment Verification

- [ ] All tables created
  - [ ] bronze.company_info_raw
  - [ ] public.unified_company_member
  - [ ] public.new_agents
  - [ ] public.unified_merge_logs
  - [ ] public.new_unified_agents

- [ ] All functions created
  - [ ] array_merge_unique()
  - [ ] update_last_updated_column()
  - [ ] run_unified_member_pipeline()
  - [ ] run_unified_merge_batch()

- [ ] Triggers active
  - [ ] trg_unified_agents_update_timestamp

- [ ] RLS enabled (if configured)

- [ ] Data loaded
  - [ ] CSV data imported
  - [ ] Pipeline executed successfully
  - [ ] new_unified_agents populated

## Verification Queries

```sql
-- Check table row counts
SELECT 'company_info_raw' as table_name, COUNT(*) FROM bronze.company_info_raw
UNION ALL
SELECT 'unified_company_member', COUNT(*) FROM public.unified_company_member
UNION ALL
SELECT 'new_agents', COUNT(*) FROM public.new_agents
UNION ALL
SELECT 'new_unified_agents', COUNT(*) FROM public.new_unified_agents;

-- Check data quality
SELECT 
    COUNT(*) as total_agents,
    SUM(CASE WHEN needs_review THEN 1 ELSE 0 END) as needs_review,
    ROUND(AVG(confidence_score), 2) as avg_confidence
FROM public.new_unified_agents;

-- Check pipeline logs
SELECT * FROM public.unified_merge_logs ORDER BY started_at DESC LIMIT 5;
```

## Troubleshooting

### Connection Issues
```bash
# Test connection
python -c "from utils.db_manager import DatabaseManager; from utils.config import ConfigManager; from dotenv import load_dotenv; load_dotenv(); config = ConfigManager(); db = DatabaseManager(config.database_url); print('✓ Connected' if db.test_connection() else '✗ Failed')"
```

### Deployment Failed
```bash
# Check logs
cat logs/deployment_report.json

# Re-run with debug logging
python deploy.py --full --log-level DEBUG --log-file logs/debug.log
```

### Data Issues
```bash
# Re-run pipeline only
python scripts/run_pipeline.py

# Check for errors in merge logs
# Query: SELECT * FROM unified_merge_logs WHERE status = 'failed';
```

## Rollback Procedure

If deployment fails and you need to rollback:

```bash
# Option 1: Drop all tables (if safe to do so)
python deploy.py --full --force-recreate

# Option 2: Manual cleanup
# Connect to database and run:
# DROP TABLE IF EXISTS public.new_unified_agents CASCADE;
# DROP TABLE IF EXISTS public.unified_merge_logs CASCADE;
# DROP TABLE IF EXISTS public.new_agents CASCADE;
# DROP TABLE IF EXISTS public.unified_company_member CASCADE;
# DROP TABLE IF EXISTS bronze.company_info_raw CASCADE;
```

## Production Deployment Notes

- [ ] Use production database credentials
- [ ] Enable RLS: `ENABLE_RLS=true` in `.env`
- [ ] Save deployment report for audit
- [ ] Monitor logs during deployment
- [ ] Schedule regular pipeline runs if needed
- [ ] Set up monitoring/alerting for pipeline failures
- [ ] Document any custom configurations

## Sign-Off

- Deployed by: _______________
- Date: _______________
- Database: _______________
- Deployment ID: _______________
- Status: _______________
- Notes: _______________
