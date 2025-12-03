# Bulk Ingestion Quick Start

## Overview
High-performance async bulk ingestion system for OpenStates, Congress.gov, and GovInfo data.

## Features
- ✅ **Async I/O** - Concurrent API requests using `asyncio` + `aiohttp`
- ✅ **Connection Pooling** - `asyncpg` connection pool (5-20 connections)
- ✅ **Rate Limiting** - Token bucket algorithm respects API limits
- ✅ **Parallel Processing** - Process multiple states/congresses simultaneously
- ✅ **Checkpointing** - Resume from failures using `incremental` schema
- ✅ **Progress Tracking** - Real-time updates and job tracking
- ✅ **Error Recovery** - Retry with exponential backoff

## Prerequisites
```bash
# Install dependencies
.venv/bin/pip install asyncpg aiohttp pyyaml tqdm

# Set API keys
export OPENSTATES_API_KEY="your_key_here"
export CONGRESS_API_KEY="your_key_here"
export GOVINFO_API_KEY="your_key_here"
```

## Configuration
Edit [`config/ingestion_config.yaml`](file:///home/cbwinslow/Videos/opendiscourse/config/ingestion_config.yaml):

```yaml
openstates:
  enabled: true
  jurisdictions: [ca, ny, tx, ...]  # All 50 states + territories
  data_types: [jurisdictions, people, bills, ...]
  rate_limit: 100  # requests per minute
  concurrent_requests: 10  # parallel requests

congress:
  enabled: true
  congresses: [113, 114, 115, 116, 117, 118, 119]

performance:
  parallel_jobs: 5  # jurisdictions/congresses processed in parallel
  worker_threads: 4
```

## Running Ingestion

### Test Run (2 states only)
```bash
cd /home/cbwinslow/Videos/opendiscourse
.venv/bin/python scripts/ingestion/test_bulk_ingest.py
```

### Full Production Run
```bash
# All sources
.venv/bin/python scripts/ingestion/bulk_ingest.py

# Specific source
.venv/bin/python scripts/ingestion/bulk_ingest.py --sources openstates
.venv/bin/python scripts/ingestion/bulk_ingest.py --sources congress govinfo
```

## Monitoring Progress

### Real-time Console
The script shows live progress with:
- Current jurisdiction/congress being processed
- Records ingested per data type
- Progress bars (via `tqdm`)
- Errors and warnings

### Database Queries
```sql
-- Check active/recent jobs
SELECT job_name, status, processed_records, started_at, completed_at
FROM ingestion.ingestion_jobs
ORDER BY started_at DESC LIMIT 10;

-- Check checkpoints
SELECT data_source, data_type, category, total_processed, is_completed
FROM incremental.ingestion_checkpoints
ORDER BY last_ingestion_at DESC;

-- Check record counts
SELECT COUNT(*) FROM openstates.people;
SELECT COUNT(*) FROM openstates.bills;
SELECT COUNT(*) FROM congress.members;
```

### Logs
```bash
tail -f logs/bulk_ingestion.log
```

## Performance Tuning

### Increase Parallelism
In `config/ingestion_config.yaml`:
```yaml
performance:
  parallel_jobs: 10  # More states/congresses at once

openstates:
  concurrent_requests: 20  # More concurrent API calls

database:
  max_pool_size: 30  # More DB connections
```

### Memory Optimization
```yaml
database:
  batch_size: 50  # Smaller batches use less memory
```

## Resuming from Failures

The system automatically tracks progress in `incremental.ingestion_checkpoints`. If interrupted:

```bash
#Just re-run - it will automatically resume
.venv/bin/python scripts/ingestion/bulk_ingest.py
```

## Expected Runtime

**With default settings** (5 parallel jobs, 10 concurrent requests):
- **OpenStates** (52 jurisdictions): ~4-6 hours for all data types
- **Congress** (7 congresses): ~2-3 hours for all members, bills, committees
- **GovInfo**: Depends on document count, ~6-8 hours for 10 years

**Total**: ~12-17 hours for complete historical data load

**With increased parallelism** (10 parallel jobs, 20 concurrent): ~6-10 hours total

## Troubleshooting

### Rate Limit Errors (429)
- Decrease `concurrent_requests`
- Increase `rate_limit` wait time

### Database Connection Errors
- Increase `max_pool_size`
- Check PostgreSQL `max_connections` setting

### Memory Issues
- Decrease `batch_size`
- Decrease `parallel_jobs`

### Resume Not Working
```sql
-- Reset specific checkpoint
DELETE FROM incremental.ingestion_checkpoints
WHERE data_source = 'openstates' AND category = 'ca';

-- Reset all checkpoints (start fresh)
TRUNCATE incremental.ingestion_checkpoints;
```
