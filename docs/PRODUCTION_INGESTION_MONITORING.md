# Production Ingestion Monitoring Guide

## 🚀 Current Run Status

**Started**: $(date)
**Configuration**: 52 jurisdictions, 8 data types each
**Parallelism**: 10 states at once, 15 concurrent API requests
**Expected Runtime**: 6-10 hours

---

## 📊 Monitoring Commands

### Watch Logs Live
```bash
tail -f /home/cbwinslow/Videos/opendiscourse/logs/full_production_ingestion.log
```

### Check Process Status
```bash
ps aux | grep bulk_ingest.py
```

### Overall Progress
```sql
-- In psql
\c opendiscourse

-- Jobs summary
SELECT
    data_source,
    COUNT(*) as total_jobs,
    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
    SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    SUM(processed_records) as total_records
FROM ingestion.ingestion_jobs
WHERE started_at > NOW() - INTERVAL '12 hours'
GROUP BY data_source;
```

### Currently Running Jobs
```sql
SELECT
    job_name,
    processed_records,
    started_at,
    NOW() - started_at as running_for
FROM ingestion.ingestion_jobs
WHERE status = 'running'
ORDER BY started_at;
```

### Recent Completions
```sql
SELECT
    job_name,
    status,
    processed_records,
    EXTRACT(EPOCH FROM (completed_at - started_at))/60 as duration_minutes
FROM ingestion.ingestion_jobs
WHERE completed_at > NOW() - INTERVAL '30 minutes'
ORDER BY completed_at DESC
LIMIT 10;
```

### Record Counts by Table
```sql
SELECT
    'people' as table_name, COUNT(*) as records FROM openstates.people
UNION ALL
SELECT 'bills', COUNT(*) FROM openstates.bills
UNION ALL
SELECT 'vote_events', COUNT(*) FROM openstates.vote_events
UNION ALL
SELECT 'committees', COUNT(*) FROM openstates.organizations
UNION ALL
SELECT 'sessions', COUNT(*) FROM openstates.sessions
UNION ALL
SELECT 'jurisdictions', COUNT(*) FROM openstates.jurisdictions;
```

### Checkpoint Status
```sql
SELECT
    data_source,
    data_type,
    category,
    total_processed,
    is_completed,
    last_ingestion_at
FROM incremental.ingestion_checkpoints
WHERE last_ingestion_at > NOW() - INTERVAL '1 hour'
ORDER BY last_ingestion_at DESC
LIMIT 20;
```

### Error Log
```sql
SELECT
    created_at,
    job_id,
    error_type,
    error_message
FROM ingestion.ingestion_errors
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

---

## 🔧 Management Commands

### Stop Ingestion
```bash
pkill -f bulk_ingest.py
```

### Resume (if stopped)
```bash
cd /home/cbwinslow/Videos/opendiscourse
nohup .venv/bin/python scripts/ingestion/bulk_ingest.py > logs/full_production_ingestion_resumed.log 2>&1 &
```

### Check Disk Space
```bash
df -h /var/lib/postgresql
du -sh /var/lib/postgresql/*/opendiscourse
```

### Check Database Connections
```sql
SELECT count(*) as active_connections
FROM pg_stat_activity
WHERE datname = 'opendiscourse';
```

---

## 📈 Expected Milestones

Based on test run performance:

- **1 hour**: ~5-8 states completed (~40-60 jobs)
- **3 hours**: ~15-20 states completed
- **6 hours**: ~30-40 states completed
- **8-10 hours**: All 52 states completed

**Final Expected Data**:
- ~5-6 million records across all tables
- ~100-150 GB disk space

---

## ⚠️ Troubleshooting

### If Process Dies
Check logs:
```bash
tail -100 logs/full_production_ingestion.log
```

Check for errors in DB:
```sql
SELECT * FROM ingestion.ingestion_errors
ORDER BY created_at DESC LIMIT 10;
```

Resume from checkpoint:
```bash
# Will automatically resume from last checkpoint
.venv/bin/python scripts/ingestion/bulk_ingest.py
```

### If Rate Limited (429 errors)
Slow down in `config/ingestion_config.yaml`:
```yaml
openstates:
  concurrent_requests: 10  # Reduce from 15
```

Then restart.

### Out of Memory
Reduce parallelism:
```yaml
performance:
  parallel_jobs: 5  # Reduce from 10
```
