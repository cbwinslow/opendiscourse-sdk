# Open Discourse Wiki - Data Sources

This wiki provides comprehensive documentation for all data sources in the Open Discourse project, including SQL data models, API endpoints, tables, functions, procedures, and Python ingestion functions.

## Table of Contents
- [Overview](#overview)
- [Data Sources](#data-sources)
- [Database Architecture](#database-architecture)
- [Programming Languages](#programming-languages)
- [SQL Functions and Procedures](#sql-functions-and-procedures)
- [Python Ingestion Functions](#python-ingestion-functions)

## Overview

Open Discourse is a comprehensive congressional data ingestion and analysis platform that aggregates legislative data from multiple government APIs:
- **congress.gov**: Official congressional member information
- **govinfo.gov**: Government documents and publications
- **openstates.org**: State legislature data across all US states

The system uses incremental ingestion with checkpoint tracking, SHA-256 fingerprinting for duplicate detection, and real-time monitoring capabilities.

## Data Sources

### 1. [GovInfo](WIKI_GOVINFO.md)
**Base URL**: https://api.govinfo.gov
**API Key**: GOVINFO_API_KEY (required)
**Coverage**: Federal legislation, congressional documents, committee information
**Primary Ingestion Script**: `scripts/ingest_govinfo_incremental.py`

### 2. [Congress](WIKI_CONGRESS.md)
**Base URL**: https://api.congress.gov/v3
**API Key**: CONGRESS_API_KEY (required)
**Coverage**: Congressional members, voting records, biographical data
**Primary Ingestion Script**: `scripts/ingest_congress_incremental.py`

### 3. [OpenStates](WIKI_OPENSTATES.md)
**Base URL**: https://v3.openstates.org
**API Key**: OPENSTATES_API_KEY (required)
**Coverage**: State legislature data, bills, votes, committees
**Primary Ingestion Script**: `scripts/ingest_openstates_incremental.py`

## Database Architecture

### Core Schemas
- **congress**: Federal congressional data (members, bills, votes, committees)
- **govinfo**: Government documents and publications
- **openstates**: State legislative data
- **incremental**: Ingestion tracking and checkpoint management

### Key Features
- **Incremental Ingestion**: Resume interrupted processes with checkpoint tracking
- **Fingerprinting**: Duplicate detection via SHA-256 hashing
- **Session Management**: Audit trails and error tracking
- **Batch Processing**: Configurable batch sizes with UPSERT operations

## Programming Languages

### Primary Languages
- **Python**: Main ingestion scripts, data processing, API clients
- **SQL**: Database schema, functions, procedures, queries
- **PostgreSQL**: Primary database system with extensions (pgcrypto, UUID generation)

### Key Python Libraries
- `requests`: HTTP API clients
- `psycopg2`: PostgreSQL database connectivity
- `python-dotenv`: Environment variable management
- `hashlib`: Content fingerprinting and SHA-256 operations

## SQL Functions and Procedures

### Incremental Ingestion System (migrations/014_incremental_ingestion_tracking.sql)
```sql
-- Core checkpoint management
incremental.get_or_create_checkpoint()
incremental.update_checkpoint_progress()
incremental.is_record_processed()

-- Session tracking
incremental.start_ingestion_session()
incremental.complete_ingestion_session()
incremental.get_next_ingestion_params()
```

### Data Verification Functions (migrations/006_member_verification_functions.sql)
```sql
-- Congress data analytics
congress.get_member_count_by_congress()
congress.get_unique_member_count()
congress.get_party_distribution()
congress.get_longest_serving_members()
congress.check_member_data_completeness()
congress.get_congress_summary()
```

### Data Verification Procedures (migrations/005_member_verification_procedures.sql)
```sql
-- Data quality procedures
congress.get_member_statistics()
congress.check_data_quality()
congress.clean_duplicate_terms()
congress.get_member_career_summary()
```

## Python Ingestion Functions

### Base Ingestion Pattern
All ingestion scripts follow a consistent pattern:

1. **Initialization**: API key validation, database connection setup
2. **Checkpoint Management**: Resume from last position
3. **Batch Processing**: Fetch, normalize, and insert data in batches
4. **Progress Tracking**: Update checkpoints after each batch
5. **Session Management**: Start and complete ingestion sessions

### Key Functions
- `get_next_ingestion_params()`: Resume from checkpoint
- `create_checkpoint()`: Initialize new ingestion
- `update_checkpoint_progress()`: Track progress
- `is_record_processed()`: Check for duplicates via fingerprinting
- `normalize_*_data()`: Transform API data to database format
- `insert_*_batch()`: Bulk database insertion with UPSERT
- `start_ingestion_session()`: Begin audit session
- `complete_ingestion_session()`: Finalize audit session
