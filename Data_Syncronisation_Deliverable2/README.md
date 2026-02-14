# Production-Grade Data Synchronization Pipeline

A robust, production-ready pipeline for deploying and managing Supabase database infrastructure with automated DDL deployment, data loading, and ETL processing.

## Features

- **Automated Database Setup**: Deploy DDL, functions, triggers, and RLS policies with a single command
- **Data Loading**: Bulk load CSV data into database tables
- **ETL Pipeline**: Automated data processing and transformation
- **Connection Pooling**: Efficient database connection management
- **Comprehensive Logging**: Detailed logging with configurable levels
- **Deployment Reports**: JSON reports for audit and monitoring
- **Idempotent Operations**: Safe to run multiple times
- **Production-Ready**: Error handling, transaction management, and rollback support

## Project Structure

```
Data Syncronisation/
├── deploy.py                 # Main deployment script
├── utils/
│   ├── db_manager.py        # Database connection manager
│   ├── config.py            # Configuration management
│   └── __init__.py
├── deployer/
│   ├── sql_deployer.py      # SQL deployment orchestrator
│   ├── data_loader.py       # CSV data loader
│   └── __init__.py
├── etl/
│   └── gold/
│       └── gold_unified_agents_pipeline.py
├── logs/                     # Deployment logs and reports
├── .env                      # Environment variables (create from .env.example)
├── .env.example             # Example environment configuration
├── requirements.txt         # Python dependencies
└── README.md               # This file

Supabase_replicate/
├── DDL/                     # Table definitions
├── FUNCTIONS/               # Database functions
├── TRIGGERS/                # Database triggers
├── RLS/                     # Row Level Security policies
└── CSVs/                    # Data files
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- PostgreSQL/Supabase database
- Database credentials

### 2. Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your database credentials
nano .env
```

### 3. Configure Environment

Edit `.env` file with your database connection details:

```env
DATABASE_URL=postgresql://postgres:your_password@your_host:5432/postgres
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
ENABLE_RLS=true
LOG_LEVEL=INFO
```

### 4. Deploy Database

#### Full Deployment (Recommended for new databases)

```bash
# Deploy everything: DDL + Data + Pipeline
python deploy.py --full
```

#### DDL Only (Schema setup without data)

```bash
# Deploy tables, functions, triggers, RLS
python deploy.py --ddl-only
```

#### Data Only (Assumes DDL already deployed)

```bash
# Load CSV data and run pipeline
python deploy.py --data-only
```

## Usage Examples

### Complete Setup for New Database

```bash
# Full deployment with verification
python deploy.py --full --log-level DEBUG
```

### Force Recreate (⚠️ CAUTION: Deletes existing data)

```bash
# Drop and recreate all tables
python deploy.py --full --force-recreate
```

### Deploy Without RLS

```bash
# Skip Row Level Security policies
python deploy.py --full --no-rls
```

### Load Data Without Running Pipeline

```bash
# Just load CSVs, don't run processing functions
python deploy.py --data-only --no-pipeline
```

### Custom Log File

```bash
# Save logs to custom location
python deploy.py --full --log-file logs/deploy_$(date +%Y%m%d).log
```

### Using Custom Environment File

```bash
# Use specific environment file
python deploy.py --full --env-file .env.production
```

## Command Line Options

```
Deployment Modes:
  --full              Full deployment: DDL + Data + Pipeline
  --ddl-only          Deploy DDL, Functions, Triggers only (no data)
  --data-only         Load data and run pipeline only (assumes DDL exists)

Options:
  --force-recreate    Drop and recreate tables (USE WITH CAUTION)
  --no-rls            Skip RLS (Row Level Security) deployment
  --no-verify         Skip deployment verification
  --no-pipeline       Load CSVs only, skip pipeline execution

Logging:
  --log-level LEVEL   Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
  --log-file PATH     Log file path (optional)

Output:
  --report-file PATH  Deployment report output file (default: logs/deployment_report.json)

Environment:
  --env-file PATH     Path to .env file (optional)
```

## Deployment Process

The deployment follows this order:

1. **DDL Deployment**
   - `CREATE_company_info_raw.sql`
   - `CREATE_unified_company_member.sql`
   - `CREATE_new_agents.sql`
   - `CREATE_unified_merge_logs.sql`
   - `CREATE_new_unified_agents.sql`

2. **Functions Deployment**
   - `helper_functions.sql`
   - `run_unified_member_pipeline.SQL`
   - `run_unified_merge_batch.sql`

3. **Triggers Deployment**
   - `TRG_new_unified_agents.sql`

4. **RLS Deployment** (optional)
   - `RLS_enable_rls.sql`

5. **Data Loading** (optional)
   - Load CSV files into tables
   - Run data processing pipeline

6. **Verification**
   - Verify all tables exist
   - Verify all functions exist
   - Check row counts

## Database Schema

### Tables

- **bronze.company_info_raw**: Raw company information
- **public.unified_company_member**: Normalized company member data
- **public.new_agents**: Agent data from various sources
- **public.unified_merge_logs**: Pipeline execution logs
- **public.new_unified_agents**: Unified master agent table

### Key Functions

- **array_merge_unique()**: Merge and deduplicate text arrays
- **update_last_updated_column()**: Auto-update timestamp trigger function
- **run_unified_member_pipeline()**: Process raw company data
- **run_unified_merge_batch()**: Merge and unify agent data

## Monitoring and Logs

### Deployment Reports

After each deployment, a JSON report is generated in `logs/deployment_report.json`:

```json
{
  "deployment_id": "deploy_20260214_233000",
  "status": "success",
  "total_duration_seconds": 45.23,
  "sql_deployment": {
    "ddl_count": 5,
    "function_count": 3,
    "trigger_count": 1
  },
  "data_pipeline": {
    "statistics": {
      "unified_agents_count": 1250,
      "needs_review_count": 45
    }
  }
}
```

### Log Files

Logs are written to console and optionally to file:

```bash
# View logs in real-time
tail -f logs/deployment.log

# Search for errors
grep ERROR logs/deployment.log
```

## Troubleshooting

### Connection Issues

```bash
# Test database connection
python -c "from utils.db_manager import DatabaseManager; import os; from dotenv import load_dotenv; load_dotenv(); db = DatabaseManager(); print('✓ Connected' if db.test_connection() else '✗ Failed')"
```

### Missing Environment Variables

```
Error: DATABASE_URL not set in environment
Solution: Create .env file with DATABASE_URL
```

### Table Already Exists

```
Error: Table already exists
Solution: Use --force-recreate flag (CAUTION: deletes data) or skip DDL with --data-only
```

### CSV File Not Found

```
Error: CSV file not found
Solution: Ensure CSV files exist in ../Supabase_replicate/CSVs/
```

## Advanced Usage

### Programmatic Deployment

```python
from utils.db_manager import DatabaseManager
from utils.config import ConfigManager
from deployer.sql_deployer import SQLDeployer
from deployer.data_loader import DataLoader
from pathlib import Path

# Initialize
config = ConfigManager()
db_manager = DatabaseManager(config.database_url)

# Deploy SQL
sql_deployer = SQLDeployer(db_manager, Path('../Supabase_replicate'))
result = sql_deployer.deploy_all(force_recreate=False, enable_rls=True)

# Load data
data_loader = DataLoader(db_manager, Path('../Supabase_replicate/CSVs'))
pipeline_result = data_loader.run_data_pipeline()

# Cleanup
db_manager.close()
```

### Custom ETL Pipeline

```python
from etl.gold.gold_unified_agents_pipeline import run_pipeline

# Run incremental pipeline
result = run_pipeline(setup_ddl=False, force_recreate=False)
print(f"Processed {result['total_records']} records")
```

## Best Practices

1. **Always backup before using --force-recreate**
2. **Use --ddl-only first for new databases to verify schema**
3. **Test with --log-level DEBUG in development**
4. **Keep deployment reports for audit trail**
5. **Use environment-specific .env files (.env.dev, .env.prod)**
6. **Monitor logs directory size and rotate logs periodically**

## Security

- Never commit `.env` file to version control
- Use service role keys only in secure environments
- Enable RLS in production (`ENABLE_RLS=true`)
- Restrict database user permissions appropriately
- Use SSL connections for production databases

## Contributing

When adding new tables or functions:

1. Add DDL to `Supabase_replicate/DDL/`
2. Update `DEPLOYMENT_ORDER` in `deployer/sql_deployer.py`
3. Add CSV mapping in `deployer/data_loader.py` if needed
4. Test deployment with `--ddl-only` first
5. Update this README

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review deployment report JSON
3. Enable DEBUG logging for detailed output
4. Verify environment variables are set correctly

## License

Internal use only.
