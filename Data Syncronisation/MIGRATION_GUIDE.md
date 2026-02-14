# Migration Guide

Guide for migrating from manual setup to automated deployment pipeline.

## Overview

This guide helps you transition from the manual Supabase setup process to the automated Python-based deployment pipeline.

## What Changed?

### Before (Manual Process)
1. Manually run each DDL file in Supabase SQL Editor
2. Manually load CSV files using `\copy` commands
3. Manually execute functions in specific order
4. Track deployment status manually
5. No automated verification

### After (Automated Pipeline)
1. Single command deploys everything: `python deploy.py --full`
2. Automated CSV loading with error handling
3. Functions executed in correct dependency order
4. Deployment logs and reports generated automatically
5. Built-in verification and validation

## Migration Steps

### Step 1: Backup Existing Data (If Applicable)

```bash
# If you have existing data, backup first
pg_dump -h YOUR_HOST -U postgres -d postgres -t public.new_unified_agents > backup.sql
pg_dump -h YOUR_HOST -U postgres -d postgres -t public.unified_company_member >> backup.sql
```

### Step 2: Set Up New Pipeline

```bash
cd "Data Syncronisation"

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit with your database credentials
nano .env
```

### Step 3: Choose Migration Strategy

#### Strategy A: Fresh Deployment (Recommended for New Databases)

```bash
# Deploy everything from scratch
python deploy.py --full
```

#### Strategy B: Incremental Migration (For Existing Databases)

```bash
# Step 1: Deploy DDL only (will skip if tables exist)
python deploy.py --ddl-only

# Step 2: Load new data
python deploy.py --data-only

# Step 3: Verify
python scripts/verify_deployment.py
```

#### Strategy C: Force Recreate (⚠️ DELETES EXISTING DATA)

```bash
# Only use if you want to start fresh
python deploy.py --full --force-recreate
```

### Step 4: Verify Migration

```bash
# Run verification script
python scripts/verify_deployment.py

# Check deployment report
cat logs/deployment_report.json
```

### Step 5: Test Pipeline Execution

```bash
# Run data processing pipeline
python scripts/run_pipeline.py

# Verify results
python -c "
from utils.db_manager import DatabaseManager
from utils.config import ConfigManager
config = ConfigManager()
db = DatabaseManager(config.database_url)
with db.get_cursor(dict_cursor=True) as cursor:
    cursor.execute('SELECT COUNT(*) as count FROM public.new_unified_agents')
    print(f\"Total unified agents: {cursor.fetchone()['count']:,}\")
"
```

## Comparison: Old vs New Workflow

### Old Manual Workflow

```bash
# 1. Connect to database
psql -h YOUR_HOST -p 5432 -U postgres -d postgres

# 2. Run DDL files one by one
\i DDL/CREATE_unified_company_member.sql
\i DDL/CREATE_new_agents.sql
\i DDL/CREATE_new_unified_agents.sql

# 3. Load CSV files
\copy raw_company_info FROM '/path/to/CSVs/raw_company_info.csv' WITH (FORMAT csv, HEADER true);
\copy new_agents FROM '/path/to/CSVs/new_agents.csv' WITH (FORMAT csv, HEADER true);

# 4. Create functions
\i FUNCTIONS/helper_functions.sql
\i FUNCTIONS/run_unified_member_pipeline.SQL
\i FUNCTIONS/run_unified_merge_batch.sql

# 5. Run pipeline
SELECT public.run_unified_merge_batch();

# 6. Manually verify
SELECT * FROM public.new_unified_agents LIMIT 10;
```

### New Automated Workflow

```bash
# Single command does everything
python deploy.py --full

# Automated verification
python scripts/verify_deployment.py
```

## Feature Mapping

| Old Manual Process | New Automated Pipeline |
|-------------------|------------------------|
| Manual DDL execution | `deploy.py --ddl-only` |
| Manual CSV loading | `deploy.py --data-only` |
| Manual function creation | Included in `--ddl-only` |
| Manual pipeline execution | `scripts/run_pipeline.py` |
| Manual verification | `scripts/verify_deployment.py` |
| No deployment logs | Automatic logs in `logs/` |
| No error handling | Comprehensive error handling |
| No rollback support | Transaction-based with rollback |

## Benefits of New Pipeline

1. **Consistency**: Same deployment process every time
2. **Speed**: 10x faster than manual process
3. **Reliability**: Automated error handling and rollback
4. **Auditability**: Complete deployment logs and reports
5. **Repeatability**: Deploy to multiple environments easily
6. **Verification**: Built-in validation checks
7. **Documentation**: Self-documenting through logs

## Common Migration Scenarios

### Scenario 1: New Supabase Project

```bash
# Fresh deployment
python deploy.py --full
```

### Scenario 2: Existing Project, Update Schema

```bash
# Deploy DDL changes only
python deploy.py --ddl-only --no-verify

# Run pipeline to process data
python scripts/run_pipeline.py
```

### Scenario 3: Reload Data

```bash
# Clear and reload data
python deploy.py --full --force-recreate
```

### Scenario 4: Multiple Environments

```bash
# Development
python deploy.py --full --env-file .env.dev

# Staging
python deploy.py --full --env-file .env.staging

# Production
python deploy.py --full --env-file .env.prod
```

## Troubleshooting Migration

### Issue: "Table already exists"

**Solution**: Use `--data-only` to skip DDL or `--force-recreate` to drop and recreate

```bash
python deploy.py --data-only
```

### Issue: "CSV file not found"

**Solution**: Ensure CSV files are in correct location

```bash
ls -la ../Supabase_replicate/CSVs/
# Should show: raw_company_info.csv, new_agents.csv
```

### Issue: "Function does not exist"

**Solution**: Re-deploy functions

```bash
python deploy.py --ddl-only
```

### Issue: "Connection refused"

**Solution**: Check DATABASE_URL in .env

```bash
# Test connection
python -c "from utils.config import ConfigManager; print(ConfigManager().database_url)"
```

## Rollback Plan

If migration fails:

1. **Restore from backup** (if you created one):
   ```bash
   psql -h YOUR_HOST -U postgres -d postgres < backup.sql
   ```

2. **Or start fresh**:
   ```bash
   python deploy.py --full --force-recreate
   ```

## Post-Migration Checklist

- [ ] All tables exist and have data
- [ ] All functions are callable
- [ ] Pipeline executes successfully
- [ ] Data quality checks pass
- [ ] Deployment logs saved for audit
- [ ] Team trained on new deployment process
- [ ] Documentation updated
- [ ] Old manual scripts archived

## Next Steps

1. **Automate Regular Runs**: Schedule `scripts/run_pipeline.py` with cron/scheduler
2. **Monitor Logs**: Set up log monitoring for `logs/` directory
3. **CI/CD Integration**: Integrate `deploy.py` into your CI/CD pipeline
4. **Multi-Environment**: Create separate `.env` files for each environment
5. **Backup Strategy**: Implement automated backups before deployments

## Support

For issues during migration:
1. Check `logs/deployment_report.json` for details
2. Run with `--log-level DEBUG` for verbose output
3. Review `DEPLOYMENT_CHECKLIST.md` for step-by-step guidance
4. Consult `README.md` for full documentation
