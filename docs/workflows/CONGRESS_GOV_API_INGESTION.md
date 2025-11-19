# Congress.gov API Data Ingestion Workflow

This guide provides step-by-step instructions for ingesting data from the Congress.gov API (api.congress.gov) into your SQL database.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Step 1: API Key Setup](#step-1-api-key-setup)
- [Step 2: Database Setup](#step-2-database-setup)
- [Step 3: Data Ingestion](#step-3-data-ingestion)
- [Step 4: Verification](#step-4-verification)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

## Prerequisites

Before starting, ensure you have:
- Python 3.13+ installed
- PostgreSQL 14+ with pgvector extension
- Access to your PostgreSQL database
- Internet connection for API access

## Step 1: API Key Setup

### 1.1 Obtain API Key

1. Visit the Congress.gov API sign-up page: https://api.congress.gov/sign-up/
2. Fill out the registration form with your information
3. You will receive your API key via email (usually within minutes)

### 1.2 Configure API Key

Set your API key as an environment variable:

```bash
# Linux/macOS
export CONGRESS_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set CONGRESS_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:CONGRESS_API_KEY="your_api_key_here"
```

Or add it to your `.env` file in the project root:

```bash
echo "CONGRESS_API_KEY=your_api_key_here" >> .env
```

## Step 2: Database Setup

### 2.1 Run SQL Migrations

Execute the SQL migration files in order to create the necessary tables and indexes:

```bash
# Navigate to the project root
cd /path/to/opendiscourse

# Run the table creation script
psql -h localhost -U postgres -d opendiscourse -f govinfo/sql/001_create_tables.sql

# Run the indexes script
psql -h localhost -U postgres -d opendiscourse -f govinfo/sql/002_indexes.sql
```

**Alternative using Python:**

```bash
python -c "
from opendiscourse.db.database import init_db
init_db()
"
```

### 2.2 Verify Database Schema

Check that the tables were created successfully:

```sql
-- Connect to your database
psql -h localhost -U postgres -d opendiscourse

-- List tables in the govinfo schema
\dt govinfo.*

-- You should see tables like:
-- govinfo.bills
-- govinfo.bill_actions
-- govinfo.bill_summaries
-- govinfo.members
-- govinfo.votes
-- etc.
```

## Step 3: Data Ingestion

### 3.1 Choose Your Ingestion Method

The repository provides the `congress_api_ingest.py` script for bulk data ingestion from Congress.gov.

### 3.2 Basic Ingestion Examples

#### Example 1: Ingest Recent House Bills (HR)

```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type hr \
  --limit 10
```

**Parameters:**
- `--source congress`: Specifies Congress.gov API as the data source
- `--congress 118`: The 118th Congress (2023-2024)
- `--bill-type hr`: House of Representatives bills
- `--limit 10`: Limit to 10 bills (for testing)

#### Example 2: Ingest Senate Bills (S)

```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type s \
  --limit 50
```

#### Example 3: Ingest All Bills from a Congress

```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --limit 100
```

**Note:** Remove `--limit` to ingest all available bills (this may take a significant amount of time).

### 3.3 Available Bill Types

- `hr` - House Bills
- `s` - Senate Bills
- `hjres` - House Joint Resolutions
- `sjres` - Senate Joint Resolutions
- `hconres` - House Concurrent Resolutions
- `sconres` - Senate Concurrent Resolutions
- `hres` - House Simple Resolutions
- `sres` - Senate Simple Resolutions

### 3.4 Understanding the Ingestion Process

The ingestion script performs the following operations:

1. **Fetches bill metadata** from Congress.gov API
2. **Downloads bill text** in available formats (HTML, XML, TXT)
3. **Extracts bill information:**
   - Title and bill number
   - Sponsors and cosponsors
   - Introduction and action dates
   - Current status
   - Committee assignments
   - Related bills
4. **Stores data** in PostgreSQL tables:
   - `govinfo.packages` - Package metadata
   - `govinfo.bills` - Bill information
   - `govinfo.bill_actions` - Legislative actions
   - `govinfo.bill_summaries` - Bill summaries
   - `govinfo.bill_versions` - Text versions
   - `govinfo.bill_committees` - Committee assignments
   - `govinfo.bill_cosponsors` - Cosponsor information
   - `govinfo.members` - Member information

### 3.5 Programmatic Usage

For more control, use the Python API directly:

```python
from congress_api_ingest import BulkDataIngester

# Initialize the ingester
ingester = BulkDataIngester(
    congress_api_key="your_key_here",
    data_dir="data/congress"
)

# Ingest bills from a specific congress
stats = ingester.ingest_congress_bills(
    congress_number=118,
    bill_type="hr",
    limit=50
)

# Print statistics
ingester.print_statistics()
```

## Step 4: Verification

### 4.1 Check Ingestion Statistics

After ingestion completes, you'll see statistics like:

```
============================================================
Bulk Data Ingestion Statistics
============================================================
Total documents processed: 50
Successful ingestions:     48
Failed ingestions:         1
Skipped documents:         1
Success rate:              96.0%
============================================================
```

### 4.2 Verify Data in Database

Query the database to verify the data was ingested:

```sql
-- Count bills by congress
SELECT congress_number, COUNT(*) as bill_count
FROM govinfo.bills
GROUP BY congress_number
ORDER BY congress_number DESC;

-- View recent bills
SELECT bill_id, bill_type, bill_number, introduced_date, latest_action_date
FROM govinfo.bills
ORDER BY introduced_date DESC
LIMIT 10;

-- Check bill actions
SELECT b.bill_id, ba.action_date, ba.action_text
FROM govinfo.bills b
JOIN govinfo.bill_actions ba ON b.bill_id = ba.bill_id
ORDER BY ba.action_date DESC
LIMIT 10;

-- Count members
SELECT COUNT(DISTINCT member_id) as member_count
FROM govinfo.members;
```

### 4.3 Review Logs

Check the application logs for any errors or warnings:

```bash
# View recent log entries
tail -n 100 data/logs/ingestion.log

# Search for errors
grep ERROR data/logs/ingestion.log
```

## Troubleshooting

### Issue: API Key Not Found

**Error:** `CONGRESS_API_KEY not configured`

**Solution:** Ensure your API key is properly set in the environment or `.env` file:

```bash
echo $CONGRESS_API_KEY  # Should display your key
```

### Issue: Database Connection Failed

**Error:** `Could not connect to database`

**Solution:** 
1. Verify PostgreSQL is running: `pg_isready`
2. Check your database credentials in `.env`
3. Ensure the database exists: `createdb opendiscourse`

### Issue: Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:** 
- The script includes built-in rate limiting (0.5s delay between requests)
- If you still encounter issues, increase the delay in `congress_api_ingest.py`:
  ```python
  RATE_LIMIT_DELAY = 1.0  # Increase from 0.5 to 1.0 seconds
  ```

### Issue: No Text Versions Available

**Warning:** `No text versions for bill`

**Explanation:** Some bills may not have text versions available yet, especially recently introduced bills. The script will skip these and continue.

### Issue: Slow Ingestion

**Problem:** Ingestion is taking too long

**Solutions:**
1. Use the `--limit` parameter to ingest smaller batches
2. Run multiple instances with different bill types in parallel
3. Consider running during off-peak hours for better API performance

## API Reference

### Congress.gov API Endpoints

The script uses the following API endpoints:

- **Bill List:** `https://api.congress.gov/v3/bill/{congress}/{bill_type}`
- **Bill Details:** `https://api.congress.gov/v3/bill/{congress}/{bill_type}/{bill_number}`

### Rate Limits

- Congress.gov API has a rate limit (exact limit not publicly specified)
- The script implements automatic rate limiting with exponential backoff
- Default delay: 0.5 seconds between requests

### Data Freshness

- Congress.gov API data is typically updated daily
- For real-time updates, consider scheduling regular ingestion runs

## Advanced Usage

### Automated Scheduled Ingestion

Set up a cron job for regular updates:

```bash
# Edit crontab
crontab -e

# Add daily ingestion at 2 AM
0 2 * * * cd /path/to/opendiscourse && /path/to/venv/bin/python congress_api_ingest.py --source congress --congress 118 --limit 100 >> /var/log/congress_ingest.log 2>&1
```

### Incremental Updates

For incremental updates, track the last ingestion date and use filters:

```python
from datetime import datetime, timedelta
from congress_api_ingest import BulkDataIngester

# Get bills from the last 7 days
start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

ingester = BulkDataIngester()
stats = ingester.ingest_congress_bills(
    congress_number=118,
    bill_type="hr"
)
```

## Next Steps

After successfully ingesting Congress.gov data:

1. **Ingest GovInfo.gov data** - See [GOVINFO_API_INGESTION.md](GOVINFO_API_INGESTION.md)
2. **Ingest OpenStates data** - See [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)
3. **Set up automated updates** - Configure cron jobs for regular data refresh
4. **Explore the data** - Run analytics queries on your ingested data
5. **Build applications** - Use the data in your own applications

## Support

For issues or questions:
- Check the [main workflow guide](DATA_INGESTION_MASTER.md)
- Review the [BULK_INGESTION_README.md](../../BULK_INGESTION_README.md)
- Check existing test cases in `tests/test_congress_ingestion.py`

## Resources

- Congress.gov API Documentation: https://api.congress.gov/
- Congress.gov API Sign-up: https://api.congress.gov/sign-up/
- GovInfo.gov: https://www.govinfo.gov/
- OpenStates: https://openstates.org/
