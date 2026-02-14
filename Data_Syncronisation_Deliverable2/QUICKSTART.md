# Quick Start Guide

Get your database up and running in 5 minutes.

## Step 1: Install Dependencies

```bash
cd "Data Syncronisation"
pip install -r requirements.txt
```

## Step 2: Configure Database

```bash
# Copy example environment file
cp .env.example .env

# Edit with your database URL
nano .env
```

Add your database connection string:
```env
DATABASE_URL=postgresql://postgres:your_password@your_host:5432/postgres
```

## Step 3: Deploy Everything

```bash
# Full deployment: DDL + Data + Pipeline
python deploy.py --full
```

That's it! Your database is now set up with:
- ✅ All tables created
- ✅ Functions and triggers deployed
- ✅ RLS policies enabled
- ✅ CSV data loaded
- ✅ Data processing pipeline executed

## Verify Deployment

Check the deployment report:
```bash
cat logs/deployment_report.json
```

## Common Commands

```bash
# Deploy schema only (no data)
python deploy.py --ddl-only

# Load data only (assumes schema exists)
python deploy.py --data-only

# Force recreate (⚠️ deletes existing data)
python deploy.py --full --force-recreate

# Debug mode
python deploy.py --full --log-level DEBUG
```

## Next Steps

- Review `README.md` for detailed documentation
- Check `logs/` directory for deployment logs
- Monitor `public.unified_merge_logs` table for pipeline execution history

## Troubleshooting

**Connection failed?**
- Verify `DATABASE_URL` in `.env`
- Check database is accessible
- Ensure credentials are correct

**CSV files not found?**
- Ensure CSVs exist in `../Supabase_replicate/CSVs/`
- Check file names match: `raw_company_info.csv`, `new_agents.csv`

**Need help?**
- Run with `--log-level DEBUG` for detailed output
- Check `logs/deployment_report.json` for error details
