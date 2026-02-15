# FELLO Project

## Overview
This repository contains multiple deliverables for the FELLO project, including data synchronization, database management, and AI agent integration components. Each subdirectory represents a separate deliverable with its own functionality and purpose.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Deliverable Details](#deliverable-details)
   - [Data Synchronization (Deliverable 2)](#data-synchronization-deliverable-2)
   - [Supabase Replication](#supabase-replication)
   - [AI Agent Design (Deliverable 4)](#ai-agent-design-deliverable-4)
3. [Getting Started](#getting-started)
4. [Dependencies](#dependencies)
5. [Contributing](#contributing)
6. [License](#license)

## Project Structure
```
FELLO/
├── Data_Syncronisation_Deliverable2/  # Data synchronization implementation
├── Supabase_replicate/                # Supabase database setup and replication
└── AI_Agent_Design_Deliverable4/      # AI agent integration and MCP implementation
```

## Deliverable Details

### Data Synchronization (Deliverable 2)
**Location:** `Data_Syncronisation_Deliverable2/`

This component handles the synchronization of data between different data sources and the unified database. It includes:
- Database connection management
- SQL deployment utilities
- Data loading and transformation
- Schema verification

**Key Files:**
- `deployer/sql_deployer.py` - Handles SQL script deployment
- `deployer/data_loader.py` - Manages data loading from various sources
- `utils/db_manager.py` - Database connection and utility functions

### Supabase Replication
**Location:** `Supabase_replicate/`

Contains database schema definitions, setup scripts, and replication configurations for Supabase.

**Key Directories:**
- `DDL/` - Database schema definitions
- `FUNCTIONS/` - Database functions and stored procedures
- `TRIGGERS/` - Database triggers
- `CSVs/` - Sample data files

**Setup Guide:**
Refer to `SETUP_GUIDE.md` for detailed setup instructions.

### AI Agent Design (Deliverable 4)
**Location:** `AI_Agent_Design_Deliverable4/`

Implementation of the Model Context Protocol (MCP) for AI agent integration, specifically for the `new_unified_agents` table.

**Key Files:**
- `mcp_new_unified_agents_expose.md` - Detailed MCP documentation
- Integration examples and API specifications

## Getting Started

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Supabase CLI (for local development)
- Node.js (for n8n workflows, if applicable)

### Installation
1. Clone the repository
   ```bash
   git clone <repository-url>
   cd FELLO
   ```

2. Set up Python environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configure environment variables
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## Dependencies
- Python packages: See `requirements.txt` in each deliverable directory
- Database: PostgreSQL with required extensions
- Additional tools:
  - n8n (for workflow automation)
  - Supabase CLI (for local development)

## Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support
For support, please contact [Your Contact Information] or open an issue in the repository.
