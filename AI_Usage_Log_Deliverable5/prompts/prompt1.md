Create a production-ready Python ETL repository for a Supabase-based data synchronization system.

Project Objective:
Build a modular ETL pipeline that synchronizes and transforms data across Bronze, Silver, and Gold schemas in Supabase (PostgreSQL). The project must follow clean architecture principles and be scalable.

Project Requirements:

1️⃣ Create the following folder structure:

etl/
│
├── bronze/
│   ├── __init__.py
│   ├── bronze_loader.py
│
├── silver/
│   ├── __init__.py
│   ├── silver_transform.py
│
├── gold/
│   ├── __init__.py
│   ├── gold_mastering.py
│
├── audit/
│   ├── __init__.py
│   ├── audit_logger.py
│
├── utils/
│   ├── __init__.py
│   ├── db.py
│   ├── helpers.py
│
├── etl_config.py
├── main.py
├── requirements.txt
├── README.md
├── .env
├── .env.sample
├── .gitignore

2️⃣ Database Connection

- Use SQLAlchemy + psycopg2
- Connection must read credentials from environment variables
- Enforce sslmode="require" for Supabase
- Use connection pooling
- Create reusable engine inside utils/db.py

Environment variables required:

SUPABASE_HOST=
SUPABASE_PORT=5432
SUPABASE_DB=postgres
SUPABASE_USER=postgres
SUPABASE_PASSWORD=

3️⃣ etl_config.py

- Store schema names (bronze, silver, gold)
- Store batch_size
- Store logging level
- Store retry configuration

4️⃣ Audit System

- Create an audit logging utility that logs:
    - job_name
    - start_time
    - end_time
    - records_processed
    - status
    - error_message

- Should be able to log into:
    - console
    - file
    - optionally a database audit table

5️⃣ Bronze Layer

- bronze_loader.py should:
    - Pull data from Supabase source tables
    - Insert into bronze schema
    - Support idempotent loads
    - Include logging

6️⃣ Silver Layer

- silver_transform.py should:
    - Clean and normalize data
    - Deduplicate
    - Use transaction handling
    - Log transformation stats

7️⃣ Gold Layer

- gold_mastering.py should:
    - Perform entity resolution
    - Merge records
    - Create master tables
    - Be deterministic and idempotent

8️⃣ main.py

- Should orchestrate ETL flow:
    run_bronze()
    run_silver()
    run_gold()

- Include proper exception handling

9️⃣ requirements.txt must include:

sqlalchemy
psycopg2-binary
python-dotenv
pandas
loguru

🔟 .env.sample must contain placeholder values.

11️⃣ .gitignore must exclude:

.env
__pycache__/
*.pyc
*.log

12️⃣ README.md must include:

- Project overview
- Setup instructions
- How to create virtual environment
- How to configure .env
- How to run ETL
- Example command
- Architecture diagram (ASCII tree)

Additional Requirements:

- Use type hints
- Follow PEP8
- Modular design
- No hardcoded credentials
- Production-grade logging
- Clear separation of concerns
- Use context managers for DB connections
- Code must be scalable and clean

Output complete repository structure with working boilerplate code.


