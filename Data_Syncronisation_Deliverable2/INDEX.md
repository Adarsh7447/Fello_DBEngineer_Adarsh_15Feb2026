# Documentation Index

Quick navigation to all documentation files.

## 🚀 Getting Started

1. **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in 5 minutes
2. **[README.md](README.md)** - Complete documentation and usage guide
3. **[setup.sh](setup.sh)** - Automated setup script

## 📋 Deployment Guides

- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Step-by-step deployment checklist
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migrate from manual to automated process
- **[deploy.py](deploy.py)** - Main deployment script

## 🏗️ Architecture & Design

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Executive summary and overview

## 🔧 Configuration

- **[.env.example](.env.example)** - Environment variable template
- **[requirements.txt](requirements.txt)** - Python dependencies
- **[.gitignore](.gitignore)** - Git ignore patterns

## 📦 Core Components

### Utilities (`utils/`)
- **[db_manager.py](utils/db_manager.py)** - Database connection manager
- **[config.py](utils/config.py)** - Configuration management

### Deployers (`deployer/`)
- **[sql_deployer.py](deployer/sql_deployer.py)** - SQL deployment orchestrator
- **[data_loader.py](deployer/data_loader.py)** - CSV data loader

### Scripts (`scripts/`)
- **[verify_deployment.py](scripts/verify_deployment.py)** - Deployment verification
- **[run_pipeline.py](scripts/run_pipeline.py)** - Pipeline execution

### ETL (`etl/`)
- **[gold_unified_agents_pipeline.py](etl/gold/gold_unified_agents_pipeline.py)** - Unified agents ETL

## 📊 SQL Assets (in `../Supabase_replicate/`)

### DDL
- `CREATE_company_info_raw.sql` - Raw company data table
- `CREATE_unified_company_member.sql` - Normalized member table
- `CREATE_new_agents.sql` - Agent data table
- `CREATE_unified_merge_logs.sql` - Pipeline logs table
- `CREATE_new_unified_agents.sql` - Master unified table

### Functions
- `helper_functions.sql` - Utility functions
- `run_unified_member_pipeline.SQL` - Member processing
- `run_unified_merge_batch.sql` - Merge and unification

### Triggers
- `TRG_new_unified_agents.sql` - Auto-update triggers

### RLS
- `RLS_enable_rls.sql` - Row Level Security policies

## 📝 Usage Examples

### Quick Commands

```bash
# Full deployment
python deploy.py --full

# DDL only
python deploy.py --ddl-only

# Data only
python deploy.py --data-only

# Verify deployment
python scripts/verify_deployment.py

# Run pipeline
python scripts/run_pipeline.py

# Help
python deploy.py --help
```

## 🎯 Common Tasks

| Task | Command | Documentation |
|------|---------|---------------|
| First-time setup | `./setup.sh` | [QUICKSTART.md](QUICKSTART.md) |
| Deploy to new DB | `python deploy.py --full` | [README.md](README.md) |
| Update schema | `python deploy.py --ddl-only` | [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) |
| Reload data | `python deploy.py --data-only` | [README.md](README.md) |
| Verify setup | `python scripts/verify_deployment.py` | [README.md](README.md) |
| Run ETL | `python scripts/run_pipeline.py` | [README.md](README.md) |
| Migrate from manual | Follow guide | [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) |

## 🔍 Troubleshooting

1. Check [README.md](README.md) - Troubleshooting section
2. Review `logs/deployment_report.json`
3. Run with `--log-level DEBUG`
4. Check [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

## 📂 Project Structure

```
Data Syncronisation/
├── 📄 Documentation
│   ├── INDEX.md (this file)
│   ├── README.md
│   ├── QUICKSTART.md
│   ├── MIGRATION_GUIDE.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── PROJECT_SUMMARY.md
│   └── ARCHITECTURE.md
│
├── 🔧 Configuration
│   ├── .env.example
│   ├── requirements.txt
│   └── .gitignore
│
├── 🚀 Entry Points
│   ├── deploy.py
│   └── setup.sh
│
├── 📦 Core Code
│   ├── utils/
│   ├── deployer/
│   ├── scripts/
│   └── etl/
│
└── 📊 Logs
    └── logs/
```

## 🎓 Learning Path

### For New Users
1. Read [QUICKSTART.md](QUICKSTART.md)
2. Run `./setup.sh`
3. Execute `python deploy.py --full`
4. Review [README.md](README.md) for details

### For Migrating Users
1. Read [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. Follow migration steps
3. Use [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### For Developers
1. Review [ARCHITECTURE.md](ARCHITECTURE.md)
2. Study code in `utils/` and `deployer/`
3. Read [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

### For DevOps
1. Read [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)
2. Review [README.md](README.md) - CI/CD section
3. Study `deploy.py` command-line options

## 🔗 External Resources

- **Supabase Documentation**: https://supabase.com/docs
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **Python psycopg2**: https://www.psycopg.org/docs/

## 📞 Support

For issues or questions:
1. Check relevant documentation above
2. Review `logs/deployment_report.json`
3. Run with `--log-level DEBUG`
4. Consult [README.md](README.md) troubleshooting section

## ✅ Quick Reference Card

```
┌─────────────────────────────────────────────────────────┐
│              Quick Reference Card                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Setup:        ./setup.sh                              │
│  Deploy:       python deploy.py --full                 │
│  Verify:       python scripts/verify_deployment.py     │
│  Pipeline:     python scripts/run_pipeline.py          │
│  Help:         python deploy.py --help                 │
│                                                         │
│  Config:       .env (create from .env.example)         │
│  Logs:         logs/deployment_report.json             │
│  Docs:         README.md                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2024  
**Version**: 1.0
