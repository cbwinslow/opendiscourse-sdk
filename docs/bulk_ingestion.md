# Bulk Data Ingestion Guide

This guide explains how to use the bulk data ingestion functionality to import large volumes of congressional and government documents into OpenDiscourse.

## Overview

The bulk data ingestion system (`congress_api_ingest.py`) provides a comprehensive solution for ingesting documents from:

- **GovInfo API**: Access to bills, federal register documents, congressional records, and more
- **Congress.gov API**: Direct access to congressional bills and related metadata

## Features

- **Batch Processing**: Process multiple documents in a single run
- **Rate Limiting**: Automatic rate limiting to respect API guidelines
- **Retry Logic**: Built-in retry mechanism with exponential backoff
- **Error Handling**: Graceful error handling with detailed logging
- **Statistics Tracking**: Comprehensive statistics on ingestion success/failure
- **Flexible Date Ranges**: Filter documents by date range
- **Multiple Formats**: Supports HTML, TXT, XML, and PDF formats

## Prerequisites

### API Keys

Before using the bulk ingestion system, you need to obtain API keys:

1. **GovInfo API Key**:
   - Visit: https://www.govinfo.gov/developers/api
   - Sign up for a free API key
   - Set environment variable: `export GOVINFO_API_KEY=your_key_here`

2. **Congress.gov API Key**:
   - Visit: https://api.congress.gov/sign-up/
   - Request an API key
   - Set environment variable: `export CONGRESS_API_KEY=your_key_here`

### Installation

Ensure you have the required dependencies installed:

```bash
pip install requests beautifulsoup4 psycopg2-binary python-dotenv
```

## Usage

### Basic Command Structure

```bash
python congress_api_ingest.py --source <govinfo|congress> [options]
```

### Example 1: Ingest Bills from GovInfo

Ingest bills from the last 30 days:

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --limit 10
```

Ingest bills with a specific date range:

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection BILLS \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --limit 50
```

### Example 2: Ingest Congressional Records

```bash
python congress_api_ingest.py \
  --source govinfo \
  --collection CREC \
  --start-date 2024-01-01 \
  --limit 20
```

### Example 3: Ingest Bills from Congress.gov

Ingest all House bills from the 118th Congress:

```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type hr \
  --limit 100
```

Ingest Senate bills:

```bash
python congress_api_ingest.py \
  --source congress \
  --congress 118 \
  --bill-type s \
  --limit 50
```

## Command-Line Options

### Required Options

- `--source {govinfo,congress}`: Data source to ingest from

### GovInfo Options

- `--collection COLLECTION`: Collection code (required for govinfo)
  - Examples: BILLS, FR, CREC, STATUTE, PLAW
- `--start-date START_DATE`: Start date in YYYY-MM-DD format (default: 30 days ago)
- `--end-date END_DATE`: End date in YYYY-MM-DD format (default: today)

### Congress.gov Options

- `--congress CONGRESS`: Congress number (required for congress source)
  - Example: 118 for the 118th Congress
- `--bill-type BILL_TYPE`: Bill type filter
  - Options: hr, s, hjres, sjres, hconres, sconres, hres, sres

### Common Options

- `--limit LIMIT`: Maximum number of documents to ingest
- `--data-dir DATA_DIR`: Directory for storing data (default: data/bulk_ingestion)

## GovInfo Collection Codes

Common collection codes you can use with the `--collection` option:

| Code | Description |
|------|-------------|
| BILLS | Congressional Bills |
| BILLSTATUS | Bill Status (XML) |
| PLAW | Public Laws |
| STATUTE | Statutes at Large |
| FR | Federal Register |
| CFR | Code of Federal Regulations |
| CREC | Congressional Record |
| CHRG | Congressional Hearings |
| CPRT | Committee Prints |
| CRPT | Committee Reports |
| HMAN | House Manual |
| SMAN | Senate Manual |

## Output and Statistics

After ingestion completes, you'll see a summary like:

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

## Programmatic Usage

You can also use the `BulkDataIngester` class directly in your Python code:

```python
from congress_api_ingest import BulkDataIngester

# Initialize ingester
ingester = BulkDataIngester(
    govinfo_api_key="your_govinfo_key",
    congress_api_key="your_congress_key",
    data_dir="data/custom_location"
)

# Ingest GovInfo collection
stats = ingester.ingest_govinfo_collection(
    collection_code="BILLS",
    start_date="2024-01-01",
    end_date="2024-01-31",
    limit=50
)

# Ingest Congress bills
stats = ingester.ingest_congress_bills(
    congress_number=118,
    bill_type="hr",
    limit=100
)

# Print statistics
ingester.print_statistics()
```

## Rate Limiting and Best Practices

The bulk ingestion system implements automatic rate limiting to be respectful of API resources:

- **Default delay**: 0.5 seconds between requests
- **Retry strategy**: 3 retries with exponential backoff
- **Timeout**: 30 seconds per request

### Best Practices

1. **Start small**: Use `--limit` to test with a small number of documents first
2. **Use date ranges**: Narrow down your ingestion with `--start-date` and `--end-date`
3. **Monitor logs**: Watch the console output for errors and warnings
4. **Check statistics**: Review the success rate at the end of each run
5. **Respect API limits**: Don't run multiple ingestion processes simultaneously

## Troubleshooting

### Common Issues

**Issue: "GOVINFO_API_KEY not configured"**
- Solution: Set the `GOVINFO_API_KEY` environment variable

**Issue: "No content available for package"**
- Some documents may not have content in any supported format
- These are automatically skipped and counted in statistics

**Issue: "Failed to fetch collection"**
- Check your internet connection
- Verify your API key is valid
- Check if the collection code is correct

**Issue: "Failed to save to database"**
- Ensure PostgreSQL is running and accessible
- Check database connection settings in `.env` file
- Verify database schema is initialized

## Logging

The ingestion system provides detailed logging at different levels:

- **INFO**: Normal operation progress
- **WARNING**: Skipped documents or minor issues
- **ERROR**: Failed ingestions or API errors

Logs are output to the console in this format:
```
2024-01-15 10:30:45,123 - congress_api_ingest - INFO - Processing package 1/10: BILLS-118hr1
```

## Database Storage

Ingested documents are stored in the `documents` table with the following metadata:

- `title`: Document title
- `content`: Full document text
- `source_url`: Original source URL
- `source_id`: Unique identifier from the source
- `source_type`: Type of source (govinfo_bulk, congress_bill, etc.)
- `source_date`: Publication or introduction date
- `source_collection`: Collection or congress number
- `document_type`: Type of document (bill, law, etc.)
- `created_at`: Timestamp of ingestion

## Advanced Configuration

You can customize the ingestion behavior by modifying `api_config.py`:

```python
BULK_DATA_CONFIG = {
    "rate_limit_delay": 0.5,  # seconds between requests
    "timeout": 30,             # request timeout in seconds
    "retry_attempts": 3,       # number of retry attempts
    "data_dir": "data/bulk_ingestion"  # default data directory
}
```

## Future Enhancements

Planned improvements include:

- Support for additional data sources (state legislatures, etc.)
- Parallel processing for faster ingestion
- Resume capability for interrupted ingestions
- Incremental updates (only fetch new documents)
- Web UI for monitoring ingestion progress
- Scheduled/automated ingestion jobs

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review logs for specific error messages
3. Ensure all prerequisites are met
4. Open an issue on GitHub with detailed information

## See Also

- [GovInfo API Documentation](https://www.govinfo.gov/developers/api)
- [Congress.gov API Documentation](https://api.congress.gov/)
- [OpenDiscourse Ingestion Workflow](../opendiscourse-ingestion-workflow.md)
