# GovInfo.gov API Data Ingestion Workflow

This guide provides step-by-step instructions for ingesting data from the GovInfo.gov API (api.govinfo.gov) into your SQL database.

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

1. Visit the GovInfo API page: https://www.govinfo.gov/developers/api
2. Click "Request an API Key"
3. Fill out the registration form with your information
4. You will receive your API key via email (usually within 24 hours)

### 1.2 Configure API Key

Set your API key as an environment variable:

```bash
# Linux/macOS
export GOVINFO_API_KEY="your_api_key_here"

# Windows (Command Prompt)
set GOVINFO_API_KEY=your_api_key_here

# Windows (PowerShell)
$env:GOVINFO_API_KEY="your_api_key_here"
```

Or add it to your `.env` file in the project root:

```bash
echo "GOVINFO_API_KEY=your_api_key_here" >> .env
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
-- govinfo.packages
-- govinfo.bills
-- govinfo.collections
-- govinfo.granules
-- govinfo.bulk_packages
-- etc.
```

## Step 3: Data Ingestion

The repository provides multiple scripts for GovInfo.gov data ingestion. Choose the method that best fits your needs.

### 3.1 Method 1: Using congress_api_ingest.py (Recommended for Bills)

This is the simplest method for ingesting bill documents from GovInfo collections.

#### Example 1: Ingest Recent Bills

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date 2024-01-01 \
  --limit 10
```

**Parameters:**
- `--source govinfo`: Specifies GovInfo API as the data source
- `--collection BILLS`: Collection code (see available collections below)
- `--start-date`: Start date for filtering documents (YYYY-MM-DD format)
- `--limit 10`: Limit to 10 documents (for testing)

#### Example 2: Ingest Congressional Record

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection CREC \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --limit 50
```

#### Example 3: Ingest Federal Register

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection FR \
  --start-date 2024-01-01 \
  --limit 100
```

### 3.2 Method 2: Using scripts/govinfo_ingestor.py (Advanced)

This method provides more advanced features including NLP processing and entity extraction.

```bash
# Navigate to scripts directory
cd scripts

# Run the ingestor
python govinfo_ingestor.py
```

**Configuration:**
Edit the script to customize:
- Collections to ingest
- Date ranges
- Maximum documents per collection
- NLP model settings

**Example configuration in the script:**

```python
# Collections to ingest
collections = [
    'BILLS',      # Congressional Bills
    'CREC',       # Congressional Record
    'FR',         # Federal Register
    'CFR',        # Code of Federal Regulations
    'GOVPUB',     # Government Publications
]

# Run ingestion
async with GovInfoIngestor() as ingestor:
    for collection in collections:
        stats = await ingestor.ingest_collection(
            collection, 
            days_back=7,        # Last week
            max_documents=50    # Limit per collection
        )
```

### 3.3 Method 3: Using govinfo/scripts/ingest_govinfo.py (Most Advanced)

This method provides the most comprehensive ingestion including bulk data downloads and detailed XML parsing.

```bash
cd govinfo/scripts

# Basic API ingestion
python ingest_govinfo.py \
  --api-key $GOVINFO_API_KEY \
  --collections BILLS,BILLSTATUS \
  --max-packages 100 \
  --output-dir govinfo_output

# Include bulk data downloads
python ingest_govinfo.py \
  --api-key $GOVINFO_API_KEY \
  --collections BILLS \
  --bulk-collections BILLSTATUS \
  --max-packages 50 \
  --bulk-sample 10 \
  --pg-dsn "postgresql://postgres:postgres@localhost:5432/opendiscourse"
```

**Parameters:**
- `--api-key`: Your GovInfo API key
- `--collections`: Comma-separated list of collections for API ingestion
- `--bulk-collections`: Comma-separated list for bulk data download
- `--max-packages`: Maximum packages to process from API
- `--bulk-sample`: Maximum files to download from bulk data
- `--pg-dsn`: PostgreSQL connection string
- `--output-dir`: Directory to save output files

### 3.4 Available Collections

Common GovInfo collections:

- `BILLS` - Congressional Bills (text versions)
- `BILLSTATUS` - Congressional Bills (metadata and status)
- `CREC` - Congressional Record
- `FR` - Federal Register
- `CFR` - Code of Federal Regulations
- `PLAW` - Public Laws
- `STATUTE` - United States Statutes at Large
- `USCODE` - United States Code
- `CHRG` - Congressional Hearings
- `GOVPUB` - Government Publications
- `GAOREPORTS` - GAO Reports
- `CRECB` - Congressional Record Bound Edition

### 3.5 Understanding the Ingestion Process

The ingestion scripts perform the following operations:

1. **Fetches collection metadata** from GovInfo API
2. **Downloads document packages** in multiple formats (XML, TXT, HTML, PDF)
3. **Parses XML bill status** files for detailed metadata:
   - Bill actions and timeline
   - Committee assignments
   - Sponsor and cosponsor information
   - Vote records
   - Member information
4. **Extracts entities** (if using govinfo_ingestor.py):
   - Named entities (people, organizations, locations)
   - Generates text embeddings for semantic search
5. **Stores data** in PostgreSQL tables:
   - `govinfo.packages` - Package metadata
   - `govinfo.collections` - Collection information
   - `govinfo.bills` - Bill details
   - `govinfo.bill_actions` - Legislative actions
   - `govinfo.votes` - Vote records
   - `govinfo.members` - Member information
   - And many more related tables

### 3.6 Programmatic Usage

#### Basic Example (congress_api_ingest.py):

```python
from congress_api_ingest import BulkDataIngester

# Initialize the ingester
ingester = BulkDataIngester(
    govinfo_api_key="your_key_here",
    data_dir="data/govinfo"
)

# Ingest from a collection
stats = ingester.ingest_govinfo_collection(
    collection_code="BILLS",
    start_date="2024-01-01",
    end_date="2024-01-31",
    limit=50
)

# Print statistics
ingester.print_statistics()
```

#### Advanced Example (govinfo_ingestor.py):

```python
import asyncio
from scripts.govinfo_ingestor import GovInfoIngestor

async def main():
    async with GovInfoIngestor(api_key="your_key") as ingestor:
        # Ingest a specific collection
        stats = await ingestor.ingest_collection(
            collection='BILLS',
            days_back=30,
            max_documents=100
        )
        print(f"Ingestion stats: {stats}")

asyncio.run(main())
```

## Step 4: Verification

### 4.1 Check Ingestion Statistics

After ingestion completes, you'll see statistics like:

```
============================================================
Bulk Data Ingestion Statistics
============================================================
Total documents processed: 100
Successful ingestions:     95
Failed ingestions:         3
Skipped documents:         2
Success rate:              95.0%
============================================================
```

Or for the advanced ingestor:

```
==================================================
INGESTION SUMMARY
==================================================
BILLS: {'fetched': 100, 'processed': 98, 'stored': 95, 'errors': 3}
CREC: {'fetched': 50, 'processed': 48, 'stored': 47, 'errors': 1}
==================================================
```

### 4.2 Verify Data in Database

Query the database to verify the data was ingested:

```sql
-- Count packages by collection
SELECT collection_code, COUNT(*) as package_count
FROM govinfo.packages
GROUP BY collection_code
ORDER BY package_count DESC;

-- View recent packages
SELECT package_id, title, date_issued, last_modified
FROM govinfo.packages
ORDER BY last_modified DESC
LIMIT 10;

-- Check bills with actions
SELECT b.bill_id, b.bill_number, COUNT(ba.bill_action_id) as action_count
FROM govinfo.bills b
LEFT JOIN govinfo.bill_actions ba ON b.bill_id = ba.bill_id
GROUP BY b.bill_id, b.bill_number
ORDER BY action_count DESC
LIMIT 10;

-- View granule details (for multi-part documents)
SELECT g.package_id, COUNT(*) as granule_count
FROM govinfo.granules g
GROUP BY g.package_id
ORDER BY granule_count DESC
LIMIT 10;

-- Check vote records
SELECT v.vote_id, v.vote_question, v.vote_result, vt.total_yes, vt.total_no
FROM govinfo.votes v
LEFT JOIN govinfo.vote_totals vt ON v.vote_id = vt.vote_id
ORDER BY v.vote_date DESC
LIMIT 10;
```

### 4.3 Verify Embeddings (if using govinfo_ingestor.py)

Check if document embeddings were generated:

```sql
-- Check for documents with embeddings
SELECT COUNT(*) as docs_with_embeddings
FROM govinfo.packages
WHERE metadata->>'embedding' IS NOT NULL;

-- View entity extractions
SELECT document_id, entity_type, COUNT(*) as entity_count
FROM govinfo.entities
GROUP BY document_id, entity_type
ORDER BY entity_count DESC
LIMIT 10;
```

### 4.4 Review Logs

Check the application logs for any errors or warnings:

```bash
# View recent log entries
tail -n 100 data/logs/ingestion.log

# Search for specific errors
grep "ERROR" data/logs/ingestion.log

# Check for package-specific issues
grep "Failed to fetch" data/logs/ingestion.log
```

## Troubleshooting

### Issue: API Key Not Found

**Error:** `GOVINFO_API_KEY not configured`

**Solution:** Ensure your API key is properly set:

```bash
echo $GOVINFO_API_KEY  # Should display your key
```

### Issue: Package Not Available

**Warning:** `No content available for package`

**Explanation:** Some packages may not have all content formats available. The script will try multiple formats (XML, TXT, HTML) and skip if none are available.

### Issue: Rate Limiting

**Error:** `429 Too Many Requests`

**Solution:** 
- The scripts include built-in rate limiting
- GovInfo API has generous rate limits (1000 requests/hour for registered keys)
- If issues persist, increase delay between requests

### Issue: Database Connection Timeout

**Error:** `asyncpg.exceptions.ConnectionDoesNotExistError`

**Solution:**
1. Ensure PostgreSQL is running
2. Verify connection string in `--pg-dsn` parameter
3. Check firewall settings if using remote database

### Issue: XML Parsing Error

**Warning:** `XML parsing error`

**Explanation:** Some XML files may be malformed. The script will log the error and continue with the next document.

### Issue: Memory Usage

**Problem:** High memory usage during bulk ingestion

**Solutions:**
1. Reduce `--max-packages` or `--bulk-sample` values
2. Process collections one at a time
3. Increase system memory or use pagination

## API Reference

### GovInfo API Endpoints

The scripts use the following API endpoints:

- **Collections:** `https://api.govinfo.gov/collections/{collection}/{start_date}/{end_date}`
- **Packages:** `https://api.govinfo.gov/packages/{package_id}`
- **Package Summary:** `https://api.govinfo.gov/packages/{package_id}/summary`
- **Package Content:** `https://api.govinfo.gov/packages/{package_id}/{format}`
- **Bulk Data:** `https://www.govinfo.gov/bulkdata/{collection}/`

### Rate Limits

- **Registered API Keys:** 1,000 requests per hour
- **Unregistered:** 100 requests per hour
- The scripts implement automatic rate limiting and retry logic

### Data Formats

GovInfo provides data in multiple formats:
- **XML** - Structured data with detailed metadata
- **TXT** - Plain text content
- **HTML** - Web-formatted content
- **PDF** - Print-ready documents
- **ZIP** - Bulk downloads containing multiple files

## Advanced Usage

### Automated Scheduled Ingestion

Set up a cron job for regular updates:

```bash
# Edit crontab
crontab -e

# Add daily ingestion at 3 AM
0 3 * * * cd /path/to/opendiscourse && /path/to/venv/bin/python congress_api_ingest.py --source govinfo --collection BILLS --start-date $(date -d '1 day ago' +\%Y-\%m-\%d) >> /var/log/govinfo_ingest.log 2>&1
```

### Bulk Data Processing

For large-scale ingestion, use the bulk data feature:

```bash
cd govinfo/scripts

# Download and process bulk data
python ingest_govinfo.py \
  --api-key $GOVINFO_API_KEY \
  --bulk-collections BILLSTATUS,VOTES \
  --disable-api \
  --output-dir /data/govinfo_bulk \
  --pg-dsn $DATABASE_URL
```

### Parallel Processing

Process multiple collections in parallel for faster ingestion:

```bash
# Start multiple processes
python congress_api_ingest.py --source govinfo --collection BILLS --limit 100 &
python congress_api_ingest.py --source govinfo --collection CREC --limit 100 &
python congress_api_ingest.py --source govinfo --collection FR --limit 100 &

# Wait for all to complete
wait
```

### Custom Processing Pipeline

Create your own processing pipeline:

```python
import asyncio
from govinfo.scripts.ingest_govinfo import (
    GovInfoAPIClient,
    PackageTransformer,
    PostgresIngestor,
    IngestionConfig
)

async def custom_pipeline():
    config = IngestionConfig(
        api_key="your_key",
        collections=["BILLS"],
        page_size=100,
        max_packages=1000,
        pg_dsn="postgresql://..."
    )
    
    async with aiohttp.ClientSession() as session:
        client = GovInfoAPIClient(session, config)
        transformer = PackageTransformer()
        pg = await PostgresIngestor.create(config.pg_dsn)
        
        async for package in client.iter_collection_packages("BILLS"):
            summary = await client.fetch_package_summary(package['packageId'])
            normalized = transformer.normalize_package(summary)
            # Custom processing here
            await pg.insert_batch("govinfo.packages", [normalized], "package_id")

asyncio.run(custom_pipeline())
```

## Next Steps

After successfully ingesting GovInfo.gov data:

1. **Ingest Congress.gov data** - See [CONGRESS_GOV_API_INGESTION.md](CONGRESS_GOV_API_INGESTION.md)
2. **Ingest OpenStates data** - See [OPENSTATES_API_INGESTION.md](OPENSTATES_API_INGESTION.md)
3. **Set up automated updates** - Configure cron jobs for regular data refresh
4. **Build semantic search** - Use embeddings for similarity searches
5. **Create analytics dashboards** - Visualize legislative data

## Support

For issues or questions:
- Check the [main workflow guide](DATA_INGESTION_MASTER.md)
- Review the [BULK_INGESTION_README.md](../../BULK_INGESTION_README.md)
- Check the GovInfo API documentation

## Resources

- GovInfo API Documentation: https://www.govinfo.gov/developers/api
- GovInfo API Sign-up: https://www.govinfo.gov/developers/api (click "Request an API Key")
- GovInfo Collections Browser: https://www.govinfo.gov/app/collection/
- GovInfo Bulk Data: https://www.govinfo.gov/bulkdata/
- Congress.gov: https://www.congress.gov/
