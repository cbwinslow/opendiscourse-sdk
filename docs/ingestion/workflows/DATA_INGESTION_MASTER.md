# OpenDiscourse Data Ingestion Master Workflow

This is the master guide for ingesting legislative and government data into your OpenDiscourse SQL database. Follow this guide to set up a complete data ingestion pipeline covering federal and state legislative data.

## Overview

OpenDiscourse supports data ingestion from three major sources:

1. **Congress.gov API** - Federal legislative data (bills, votes, members)
2. **GovInfo.gov API** - Federal government publications and documents
3. **OpenStates API** - State-level legislative data (50 states + territories)

## Table of Contents

- [Quick Start Guide](#quick-start-guide)
- [Complete Setup Workflow](#complete-setup-workflow)
- [Data Source Overview](#data-source-overview)
- [Database Schema](#database-schema)
- [Maintenance and Updates](#maintenance-and-updates)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Quick Start Guide

### Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.13+ installed
- [ ] PostgreSQL 14+ installed with pgvector extension
- [ ] Database created (name: `opendiscourse`)
- [ ] Git repository cloned locally
- [ ] Virtual environment activated

### 30-Minute Quick Setup

If you want to get started quickly with sample data:

```bash
# 1. Set up environment
cd /path/to/opendiscourse
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure database
cp .env.example .env
# Edit .env with your database credentials

# 3. Create database and tables
createdb opendiscourse
psql -d opendiscourse -f govinfo/sql/001_create_tables.sql
psql -d opendiscourse -f govinfo/sql/002_indexes.sql

# 4. Get API keys (do these in parallel while waiting for approval)
# - Congress.gov: https://api.congress.gov/sign-up/
# - GovInfo.gov: https://www.govinfo.gov/developers/api
# - OpenStates: https://openstates.org/api/

# 5. Set environment variables
export CONGRESS_API_KEY="your_congress_key"
export GOVINFO_API_KEY="your_govinfo_key"
export OPENSTATES_API_KEY="your_openstates_key"

# 6. Test with small data samples
python congress_api_ingest.py --source congress --congress 118 --bill-type hr --limit 5
python congress_api_ingest.py --source govinfo --collection BILLS --limit 5

# 7. Verify data
psql -d opendiscourse -c "SELECT COUNT(*) FROM govinfo.bills;"
```

## Complete Setup Workflow

### Phase 1: Environment Setup (30 minutes)

#### 1.1 Install Dependencies

```bash
# Navigate to project root
cd /path/to/opendiscourse

# Create and activate virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python --version  # Should show 3.13+
pip list | grep -E "psycopg2|sqlalchemy|requests"
```

#### 1.2 Configure Database

```bash
# Create PostgreSQL database
createdb opendiscourse

# Verify connection
psql -d opendiscourse -c "SELECT version();"

# Enable pgvector extension (if needed for embeddings)
psql -d opendiscourse -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

#### 1.3 Set Up Configuration Files

```bash
# Copy example configuration
cp .env.example .env

# Edit .env file with your settings
nano .env  # or use your preferred editor
```

Required `.env` variables:
```ini
# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/opendiscourse
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=opendiscourse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# API Keys (you'll add these in Phase 2)
CONGRESS_API_KEY=
GOVINFO_API_KEY=
OPENSTATES_API_KEY=
```

### Phase 2: API Key Registration (1-2 days for approval)

Register for API keys from all three sources. This can take 1-2 days for approval.

#### 2.1 Congress.gov API Key

1. Visit: https://api.congress.gov/sign-up/
2. Fill out the registration form
3. Receive key via email (usually within hours)
4. Add to `.env`: `CONGRESS_API_KEY=your_key_here`

#### 2.2 GovInfo.gov API Key

1. Visit: https://www.govinfo.gov/developers/api
2. Click "Request an API Key"
3. Fill out the form
4. Receive key via email (usually within 24 hours)
5. Add to `.env`: `GOVINFO_API_KEY=your_key_here`

#### 2.3 OpenStates API Key

1. Visit: https://openstates.org/api/
2. Sign up or log in
3. Get key from your dashboard (instant)
4. Add to `.env`: `OPENSTATES_API_KEY=your_key_here`

**Pro Tip:** While waiting for API keys, proceed with Phase 3 (Database Setup).

### Phase 3: Database Setup (15 minutes)

#### 3.1 Run SQL Migrations

```bash
# Navigate to project root
cd /path/to/opendiscourse

# Run table creation script
psql -d opendiscourse -f govinfo/sql/001_create_tables.sql

# Run indexes script
psql -d opendiscourse -f govinfo/sql/002_indexes.sql
```

#### 3.2 Verify Database Schema

```sql
-- Connect to database
psql -d opendiscourse

-- Check schema was created
\dn

-- List all tables in govinfo schema
\dt govinfo.*

-- Check a few key tables
\d govinfo.bills
\d govinfo.members
\d govinfo.votes

-- Exit
\q
```

You should see approximately 35+ tables including:
- `govinfo.packages`
- `govinfo.bills`
- `govinfo.bill_actions`
- `govinfo.members`
- `govinfo.votes`
- `govinfo.committees`
- And many more...

### Phase 4: Data Ingestion (Variable time)

Once you have your API keys, start ingesting data. We recommend starting with small samples.

#### 4.1 Test Congress.gov Ingestion

Start with a small test to verify everything works:

```bash
# Test with 5 recent House bills
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type hr \
  --limit 5

# Check results
psql -d opendiscourse -c "SELECT bill_id, bill_number FROM govinfo.bills LIMIT 5;"
```

If successful, proceed with larger ingestion:

```bash
# Ingest all House bills from 118th Congress
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type hr

# Ingest Senate bills
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type s
```

**See detailed guide:** [CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md)

#### 4.2 Test GovInfo.gov Ingestion

Test with a small sample:

```bash
# Test with 5 recent bills
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date 2024-01-01 \
  --limit 5

# Check results
psql -d opendiscourse -c "SELECT package_id, title FROM govinfo.packages LIMIT 5;"
```

If successful, ingest more collections:

```bash
# Ingest recent bills
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date 2024-01-01 \
  --limit 100

# Ingest Congressional Record
python congress_api_ingest.py \
  --source govinfo \
  --collection CREC \
  --start-date 2024-01-01 \
  --limit 50

# Ingest Federal Register
python congress_api_ingest.py \
  --source govinfo \
  --collection FR \
  --start-date 2024-01-01 \
  --limit 50
```

**See detailed guide:** [GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md)

#### 4.3 Test OpenStates Ingestion

Create and run a test script for your state:

```python
# Create: test_openstates.py
import os
from opendiscourse.ingestion.membership_ingestion import fetch_openstates_legislators

STATE = "ny"  # Change to your state
SESSION = "2023-2024"
API_KEY = os.getenv("OPENSTATES_API_KEY")

legislators = fetch_openstates_legislators(STATE, SESSION, API_KEY)
if legislators:
    print(f"Successfully fetched {len(legislators)} legislators from {STATE}")
else:
    print("Failed to fetch legislators")
```

Run the test:

```bash
python test_openstates.py
```

For full OpenStates ingestion, follow the detailed guide.

**See detailed guide:** [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)

### Phase 5: Verification (15 minutes)

After ingestion, verify your data:

```sql
-- Connect to database
psql -d opendiscourse

-- Count records by type
SELECT 'Packages' as type, COUNT(*) as count FROM govinfo.packages
UNION ALL
SELECT 'Bills', COUNT(*) FROM govinfo.bills
UNION ALL
SELECT 'Bill Actions', COUNT(*) FROM govinfo.bill_actions
UNION ALL
SELECT 'Members', COUNT(*) FROM govinfo.members
UNION ALL
SELECT 'Votes', COUNT(*) FROM govinfo.votes
UNION ALL
SELECT 'Committees', COUNT(*) FROM govinfo.committees;

-- Check data quality
-- Recent bills
SELECT bill_id, bill_type, bill_number, introduced_date
FROM govinfo.bills
ORDER BY introduced_date DESC
LIMIT 10;

-- Members with most bill sponsorships
SELECT m.full_name, COUNT(bc.bill_id) as bill_count
FROM govinfo.members m
JOIN govinfo.bill_cosponsors bc ON m.member_id = bc.member_id
GROUP BY m.member_id, m.full_name
ORDER BY bill_count DESC
LIMIT 10;

-- Recent votes
SELECT v.vote_id, v.vote_question, v.vote_date, vt.total_yes, vt.total_no
FROM govinfo.votes v
LEFT JOIN govinfo.vote_totals vt ON v.vote_id = vt.vote_id
ORDER BY v.vote_date DESC
LIMIT 10;
```

## Data Source Overview

### Congress.gov API

**Best for:**
- Federal bills and resolutions
- Congressional members
- Bill status and actions
- Basic vote information

**Data Covered:**
- All Congresses (historical and current)
- House and Senate bills
- Member information
- Committee assignments

**Update Frequency:** Daily

**Rate Limits:** Moderate (specific limits not publicly documented)

### GovInfo.gov API

**Best for:**
- Full-text government documents
- Multiple document formats (XML, HTML, PDF)
- Bulk data downloads
- Detailed bill status XML files
- Historical documents

**Data Covered:**
- Congressional bills and documents
- Federal Register
- Code of Federal Regulations
- Congressional Record
- Public laws
- And 100+ other collections

**Update Frequency:** Daily

**Rate Limits:** 1,000 requests/hour (registered keys)

### OpenStates API

**Best for:**
- State legislative data
- State legislators
- State bills and resolutions
- State-level votes
- Committee information

**Data Covered:**
- All 50 states + DC and territories
- Current and historical sessions
- Legislator information
- Bill tracking

**Update Frequency:** Daily (varies by state)

**Rate Limits:** 100 requests/minute (free tier)

## Database Schema

### Key Tables

The OpenDiscourse database uses the `govinfo` schema with the following main tables:

#### Legislative Documents
- `govinfo.packages` - Document packages from GovInfo
- `govinfo.bills` - Bill details (federal and state)
- `govinfo.bill_actions` - Legislative actions on bills
- `govinfo.bill_summaries` - Bill summaries
- `govinfo.bill_versions` - Different text versions of bills
- `govinfo.bill_subjects` - Subject classifications

#### People and Organizations
- `govinfo.members` - Legislators (federal and state)
- `govinfo.committees` - Legislative committees
- `govinfo.memberships` - Committee memberships
- `govinfo.member_terms` - Service terms
- `govinfo.parties` - Political parties

#### Voting
- `govinfo.votes` - Vote records
- `govinfo.vote_ballots` - Individual member votes
- `govinfo.vote_totals` - Vote tallies
- `govinfo.member_votes` - Member voting records
- `govinfo.member_attendance` - Attendance records

#### Metadata
- `govinfo.collections` - GovInfo collection definitions
- `govinfo.congresses` - Congress sessions
- `govinfo.sessions` - Legislative sessions
- `govinfo.chambers` - Legislative chambers

### Table Relationships

```
packages (1) ----< (M) bills
bills (1) ----< (M) bill_actions
bills (1) ----< (M) bill_summaries
bills (1) ----< (M) bill_versions
bills (M) >----< (M) members (via bill_cosponsors)
bills (M) >----< (M) committees (via bill_committees)
votes (1) ----< (M) vote_ballots
votes (M) >----< (M) members (via vote_ballots)
members (1) ----< (M) member_terms
members (M) >----< (M) committees (via memberships)
```

## Maintenance and Updates

### Automated Updates

Set up cron jobs for regular data updates:

```bash
# Edit crontab
crontab -e

# Add these entries (adjust times as needed)

# Congress.gov - Daily at 2 AM
0 2 * * * cd /path/to/opendiscourse && /path/to/.venv/bin/python congress_api_ingest.py --source congress --congress 118 >> /var/log/congress_ingest.log 2>&1

# GovInfo.gov - Daily at 3 AM
0 3 * * * cd /path/to/opendiscourse && /path/to/.venv/bin/python congress_api_ingest.py --source govinfo --collection BILLS --start-date $(date -d '1 day ago' +\%Y-\%m-\%d) >> /var/log/govinfo_ingest.log 2>&1

# OpenStates - Daily at 4 AM
0 4 * * * cd /path/to/opendiscourse && /path/to/.venv/bin/python ingest_openstates_bills.py >> /var/log/openstates_ingest.log 2>&1
```

### Incremental Updates

For efficiency, only fetch new/updated records:

```bash
# Get bills updated in the last day
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date $(date -d '1 day ago' +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d)
```

### Database Maintenance

Regular maintenance tasks:

```sql
-- Vacuum and analyze tables monthly
VACUUM ANALYZE govinfo.bills;
VACUUM ANALYZE govinfo.members;
VACUUM ANALYZE govinfo.votes;

-- Refresh materialized views
REFRESH MATERIALIZED VIEW govinfo.bill_summary_latest;

-- Check database size
SELECT 
    schemaname,
    pg_size_pretty(SUM(pg_total_relation_size(schemaname||'.'||tablename))::bigint) as size
FROM pg_tables
WHERE schemaname = 'govinfo'
GROUP BY schemaname;

-- Identify tables needing attention
SELECT 
    schemaname || '.' || tablename as table,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    n_live_tup as rows
FROM pg_stat_user_tables
WHERE schemaname = 'govinfo'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
LIMIT 10;
```

## Best Practices

### 1. Start Small, Scale Up

Always test with small data samples before running large ingestions:

```bash
# Good: Test with --limit 10
python congress_api_ingest.py --source congress --congress 118 --limit 10

# Then: Scale up gradually
python congress_api_ingest.py --source congress --congress 118 --limit 100

# Finally: Run full ingestion (no limit)
python congress_api_ingest.py --source congress --congress 118
```

### 2. Monitor Resource Usage

```bash
# Monitor disk space
df -h

# Monitor PostgreSQL connections
psql -d opendiscourse -c "SELECT count(*) FROM pg_stat_activity;"

# Monitor table sizes
psql -d opendiscourse -c "
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size('govinfo.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'govinfo'
ORDER BY pg_total_relation_size('govinfo.'||tablename) DESC
LIMIT 10;
"
```

### 3. Handle Errors Gracefully

The ingestion scripts include error handling, but monitor logs:

```bash
# Create logs directory
mkdir -p /var/log/opendiscourse

# Tail logs in real-time
tail -f /var/log/congress_ingest.log
tail -f /var/log/govinfo_ingest.log
tail -f /var/log/openstates_ingest.log
```

### 4. Backup Regularly

```bash
# Backup database
pg_dump opendiscourse | gzip > opendiscourse_backup_$(date +%Y%m%d).sql.gz

# Backup to remote location
pg_dump opendiscourse | gzip | aws s3 cp - s3://your-bucket/backups/opendiscourse_$(date +%Y%m%d).sql.gz
```

### 5. Version Your Data

Track ingestion runs for reproducibility:

```sql
-- Create an ingestion log table
CREATE TABLE IF NOT EXISTS govinfo.ingestion_log (
    log_id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    records_processed INTEGER,
    records_success INTEGER,
    records_failed INTEGER,
    parameters JSONB,
    notes TEXT
);

-- Log each ingestion run
INSERT INTO govinfo.ingestion_log (
    source, parameters, records_processed, records_success, records_failed
) VALUES (
    'congress_api',
    '{"congress": 118, "bill_type": "hr"}'::jsonb,
    100, 95, 5
);
```

### 6. Optimize Queries

Create indexes for common queries:

```sql
-- Add custom indexes based on your usage patterns
CREATE INDEX IF NOT EXISTS idx_bills_title_search 
ON govinfo.bills USING gin(to_tsvector('english', title));

CREATE INDEX IF NOT EXISTS idx_members_name_search
ON govinfo.members USING gin(to_tsvector('english', full_name));

CREATE INDEX IF NOT EXISTS idx_bill_actions_chamber_date
ON govinfo.bill_actions(chamber_code, action_date);
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Can't Connect to Database

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
1. Verify PostgreSQL is running: `systemctl status postgresql`
2. Check DATABASE_URL in `.env`
3. Verify credentials: `psql -d opendiscourse -U postgres`
4. Check pg_hba.conf for connection permissions

#### Issue: API Key Errors

**Symptoms:**
```
Error: API key not configured
Error: 401 Unauthorized
```

**Solutions:**
1. Verify environment variables: `echo $CONGRESS_API_KEY`
2. Check `.env` file has correct keys
3. Reload environment: `source .env`
4. Verify key is valid on API provider's website

#### Issue: Slow Ingestion

**Symptoms:**
- Ingestion takes hours
- System becomes unresponsive

**Solutions:**
1. Use `--limit` parameter for smaller batches
2. Run ingestion during off-peak hours
3. Increase rate limit delays
4. Check network connectivity
5. Monitor database performance

#### Issue: Duplicate Records

**Symptoms:**
```
ERROR: duplicate key value violates unique constraint
```

**Solutions:**
1. Database schema includes `ON CONFLICT` clauses
2. If errors persist, check for corrupt data
3. Consider adding `UPSERT` logic for updates
4. Review ingestion logs for duplicate runs

#### Issue: Out of Disk Space

**Symptoms:**
```
ERROR: could not extend file
```

**Solutions:**
1. Check disk space: `df -h`
2. Clean up old log files
3. Vacuum database: `VACUUM FULL`
4. Consider archiving old data
5. Add more disk space

### Getting Help

If you encounter issues not covered here:

1. **Check detailed guides:**
   - [CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md)
   - [GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md)
   - [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)

2. **Review existing documentation:**
   - [BULK_INGESTION_README.md](../../BULK_INGESTION_README.md)
   - Repository README.md

3. **Check test cases:**
   - `tests/test_congress_ingestion.py`

4. **API Documentation:**
   - Congress.gov API: https://api.congress.gov/
   - GovInfo API: https://www.govinfo.gov/developers/
   - OpenStates API: https://docs.openstates.org/

## Summary

You now have a complete data ingestion pipeline for OpenDiscourse! Here's what you've accomplished:

✅ Set up the database with proper schema
✅ Registered for all three API keys
✅ Configured ingestion scripts
✅ Ingested federal legislative data (Congress.gov)
✅ Ingested government documents (GovInfo.gov)
✅ Ingested state legislative data (OpenStates)
✅ Set up automated updates
✅ Implemented monitoring and maintenance

### Next Steps

1. **Explore Your Data:** Run queries to analyze the ingested data
2. **Build Applications:** Use the data in your own applications
3. **Add Custom Processing:** Extend the ingestion pipeline with custom logic
4. **Set Up Analytics:** Create dashboards and visualizations
5. **Enable Search:** Implement full-text search across all documents
6. **Add RAG Capabilities:** Integrate with LLMs for question-answering

### Recommended Reading Order

1. Start with this master guide (you're here!)
2. Follow [CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md) for federal data
3. Follow [GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md) for documents
4. Follow [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md) for state data
5. Review [BULK_INGESTION_README.md](../../BULK_INGESTION_README.md) for examples

## Appendix

### Useful SQL Queries

```sql
-- Get ingestion statistics
SELECT 
    'Total Bills' as metric, COUNT(*) as value FROM govinfo.bills
UNION ALL
    SELECT 'Total Members', COUNT(*) FROM govinfo.members
UNION ALL
    SELECT 'Total Votes', COUNT(*) FROM govinfo.votes
UNION ALL
    SELECT 'Total Actions', COUNT(*) FROM govinfo.bill_actions
UNION ALL
    SELECT 'Total Committees', COUNT(*) FROM govinfo.committees;

-- Find most active legislators
SELECT m.full_name, m.party_code, m.state,
       COUNT(DISTINCT bc.bill_id) as bills_cosponsored,
       COUNT(DISTINCT mv.vote_id) as votes_cast
FROM govinfo.members m
LEFT JOIN govinfo.bill_cosponsors bc ON m.member_id = bc.member_id
LEFT JOIN govinfo.member_votes mv ON m.member_id = mv.member_id
GROUP BY m.member_id, m.full_name, m.party_code, m.state
ORDER BY bills_cosponsored DESC
LIMIT 20;

-- Analyze legislative activity by month
SELECT 
    DATE_TRUNC('month', introduced_date) as month,
    COUNT(*) as bills_introduced
FROM govinfo.bills
WHERE introduced_date IS NOT NULL
GROUP BY DATE_TRUNC('month', introduced_date)
ORDER BY month DESC
LIMIT 12;
```

### Environment Variables Reference

Complete list of environment variables:

```ini
# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=opendiscourse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# API Keys
CONGRESS_API_KEY=your_congress_key
GOVINFO_API_KEY=your_govinfo_key
OPENSTATES_API_KEY=your_openstates_key

# Optional: Supabase (if using)
SUPABASE_URL=http://localhost:54321
SUPABASE_SERVICE_ROLE_KEY=your_key
```

### File Locations Reference

Important files and directories:

```
opendiscourse/
├── congress_api_ingest.py          # Main ingestion script
├── govinfo/
│   └── scripts/
│       └── ingest_govinfo.py       # Advanced GovInfo ingestion
├── scripts/
│   ├── govinfo_ingestor.py         # GovInfo with NLP
│   └── data_ingestion/
│       └── source_ingestion_tasks.py  # OpenStates integration
├── govinfo/sql/
│   ├── 001_create_tables.sql       # Database schema
│   └── 002_indexes.sql             # Database indexes
├── opendiscourse/
│   ├── ingestion/
│   │   └── membership_ingestion.py # OpenStates legislators
│   └── db/
│       └── database.py             # Database connection
├── docs/
│   └── workflows/                  # This directory!
│       ├── DATA_INGESTION_MASTER.md
│       ├── CONGRESS_GOV_API_INGESTION.md
│       ├── GOVINFO_API_INGESTION.md
│       └── OPENSTATES_API_INGESTION.md
└── tests/
    └── test_congress_ingestion.py  # Test suite
```

---

**Last Updated:** 2024
**Version:** 1.0
**Maintainers:** OpenDiscourse Team
