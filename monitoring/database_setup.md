# Database Setup for Progress Monitoring

## Overview

This document describes the database schema and setup procedures for the real-time progress monitoring system.

## Prerequisites

- PostgreSQL 12+
- Database user with CREATE privileges
- OpenDiscourse database already created

## Schema Creation

### Core Tables

```sql
-- =============================================
-- OpenDiscourse Progress Monitoring Schema
-- =============================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================
-- Core Progress Tracking Tables
-- =============================================

-- Main jobs table
CREATE TABLE ingestion_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    data_source VARCHAR(255) NOT NULL, -- congress.gov, govinfo.gov, etc.
    table_name VARCHAR(255) NOT NULL DEFAULT 'documents',
    record_type VARCHAR(100) NOT NULL, -- bill, document, entity, etc.
    status VARCHAR(50) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'paused', 'cancelled')),

    -- Progress tracking
    total_records INTEGER,
    processed_records INTEGER NOT NULL DEFAULT 0,
    failed_records INTEGER NOT NULL DEFAULT 0,
    throughput_per_minute NUMERIC DEFAULT 0,
    eta_timestamp TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Error tracking table
CREATE TABLE ingestion_errors (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    record_id VARCHAR(500), -- ID of the record that failed
    retry_count INTEGER NOT NULL DEFAULT 0,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    error_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Progress log for detailed tracking (optional, for high-frequency updates)
CREATE TABLE ingestion_progress_log (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    processed_records INTEGER NOT NULL,
    failed_records INTEGER NOT NULL,
    throughput_per_minute NUMERIC,
    current_record_id VARCHAR(500),
    log_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Indexes for Performance
-- =============================================

-- Core job indexes
CREATE INDEX idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX idx_ingestion_jobs_data_source ON ingestion_jobs(data_source);
CREATE INDEX idx_ingestion_jobs_started_at ON ingestion_jobs(started_at DESC);
CREATE INDEX idx_ingestion_jobs_table_name ON ingestion_jobs(table_name);
CREATE INDEX idx_ingestion_jobs_record_type ON ingestion_jobs(record_type);

-- Composite indexes for common queries
CREATE INDEX idx_ingestion_jobs_status_started ON ingestion_jobs(status, started_at DESC);
CREATE INDEX idx_ingestion_jobs_data_source_table ON ingestion_jobs(data_source, table_name);
CREATE INDEX idx_ingestion_jobs_active ON ingestion_jobs(status) WHERE status IN ('running', 'paused');

-- Error indexes
CREATE INDEX idx_ingestion_errors_job_id ON ingestion_errors(job_id);
CREATE INDEX idx_ingestion_errors_type ON ingestion_errors(error_type);
CREATE INDEX idx_ingestion_errors_resolved ON ingestion_errors(resolved);
CREATE INDEX idx_ingestion_errors_created_at ON ingestion_errors(created_at DESC);

-- Composite error indexes
CREATE INDEX idx_ingestion_errors_job_type ON ingestion_errors(job_id, error_type);
CREATE INDEX idx_ingestion_errors_unresolved ON ingestion_errors(job_id, resolved) WHERE resolved = FALSE;

-- Progress log indexes (if using detailed logging)
CREATE INDEX idx_progress_log_job_id ON ingestion_progress_log(job_id);
CREATE INDEX idx_progress_log_timestamp ON ingestion_progress_log(log_timestamp DESC);

-- =============================================
-- Views for Reporting
-- =============================================

-- Active jobs view
CREATE VIEW active_ingestion_jobs AS
SELECT
    id,
    job_name,
    data_source,
    table_name,
    record_type,
    processed_records,
    total_records,
    ROUND(processed_records::NUMERIC / GREATEST(total_records, 1) * 100, 2) as progress_percent,
    failed_records,
    throughput_per_minute,
    eta_timestamp,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at))/60 as minutes_running,
    started_at
FROM ingestion_jobs
WHERE status = 'running';

-- Error summary view
CREATE VIEW ingestion_error_summary AS
SELECT
    job_id,
    error_type,
    COUNT(*) as error_count,
    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
    MAX(created_at) as last_error_at
FROM ingestion_errors
GROUP BY job_id, error_type;

-- Job performance view
CREATE VIEW ingestion_job_performance AS
SELECT
    ij.id,
    ij.job_name,
    ij.data_source,
    ij.table_name,
    ij.processed_records,
    ij.failed_records,
    ij.throughput_per_minute,
    ij.started_at,
    ij.completed_at,
    CASE
        WHEN ij.completed_at IS NOT NULL THEN
            EXTRACT(EPOCH FROM (ij.completed_at - ij.started_at))/60
        ELSE
            EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ij.started_at))/60
    END as duration_minutes,
    CASE
        WHEN ij.completed_at IS NOT NULL AND ij.processed_records > 0 THEN
            ij.processed_records / (EXTRACT(EPOCH FROM (ij.completed_at - ij.started_at))/3600)
        WHEN ij.processed_records > 0 THEN
            ij.processed_records / (EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - ij.started_at))/3600)
        ELSE 0
    END as records_per_hour
FROM ingestion_jobs ij;

-- =============================================
-- Functions and Triggers
-- =============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for automatic timestamp updates
CREATE TRIGGER update_ingestion_jobs_updated_at
    BEFORE UPDATE ON ingestion_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ingestion_errors_updated_at
    BEFORE UPDATE ON ingestion_errors
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate ETA
CREATE OR REPLACE FUNCTION calculate_eta(
    processed_records INTEGER,
    total_records INTEGER,
    throughput_per_minute NUMERIC,
    started_at TIMESTAMP
) RETURNS TIMESTAMP AS $$
DECLARE
    remaining_records INTEGER;
    minutes_remaining NUMERIC;
BEGIN
    IF total_records IS NULL OR throughput_per_minute <= 0 THEN
        RETURN NULL;
    END IF;

    remaining_records := total_records - processed_records;
    IF remaining_records <= 0 THEN
        RETURN CURRENT_TIMESTAMP;
    END IF;

    minutes_remaining := remaining_records / throughput_per_minute;
    RETURN started_at + INTERVAL '1 minute' * minutes_remaining;
END;
$$ LANGUAGE plpgsql;

-- Function to update job progress and ETA
CREATE OR REPLACE FUNCTION update_job_progress(
    p_job_id INTEGER,
    p_processed_increment INTEGER DEFAULT 0,
    p_failed_increment INTEGER DEFAULT 0,
    p_current_record_id VARCHAR(500) DEFAULT NULL
) RETURNS VOID AS $$
DECLARE
    job_record RECORD;
    new_processed INTEGER;
    new_failed INTEGER;
    time_elapsed_minutes NUMERIC;
    new_throughput NUMERIC;
BEGIN
    -- Get current job state
    SELECT * INTO job_record FROM ingestion_jobs WHERE id = p_job_id FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Job with ID % not found', p_job_id;
    END IF;

    -- Calculate new counts
    new_processed := job_record.processed_records + p_processed_increment;
    new_failed := job_record.failed_records + p_failed_increment;

    -- Calculate throughput
    time_elapsed_minutes := EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - job_record.started_at)) / 60;
    IF time_elapsed_minutes > 0 THEN
        new_throughput := new_processed / time_elapsed_minutes;
    ELSE
        new_throughput := 0;
    END IF;

    -- Update job record
    UPDATE ingestion_jobs SET
        processed_records = new_processed,
        failed_records = new_failed,
        throughput_per_minute = new_throughput,
        eta_timestamp = calculate_eta(new_processed, total_records, new_throughput, started_at),
        metadata = jsonb_set(metadata, '{current_record_id}', to_jsonb(p_current_record_id)),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_job_id;

END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Sample Data and Testing
-- =============================================

-- Insert sample job for testing
INSERT INTO ingestion_jobs (
    job_name, data_source, table_name, record_type,
    total_records, metadata
) VALUES (
    'Test Congress Bills',
    'congress.gov',
    'documents',
    'bill',
    5000,
    '{"congress": 118, "test": true}'::jsonb
);

-- Insert sample errors
INSERT INTO ingestion_errors (
    job_id, error_type, error_message, record_id, error_metadata
) VALUES (
    1,
    'api_error',
    'Rate limit exceeded',
    '118-hr-1234',
    '{"retry_after": 60, "endpoint": "/bill/118/hr/1234"}'::jsonb
);
```

### Partitioning (for High Volume)

```sql
-- Partitioning setup for high-volume installations
-- Create partitions by month for better performance

-- Function to create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partitions(
    table_name TEXT,
    start_date DATE DEFAULT CURRENT_DATE,
    months_ahead INTEGER DEFAULT 12
) RETURNS VOID AS $$
DECLARE
    partition_date DATE := start_date;
    partition_name TEXT;
    partition_start DATE;
    partition_end DATE;
BEGIN
    FOR i IN 0..months_ahead-1 LOOP
        partition_start := partition_date;
        partition_end := partition_start + INTERVAL '1 month';

        partition_name := table_name || '_y' || EXTRACT(YEAR FROM partition_start) ||
                         '_m' || LPAD(EXTRACT(MONTH FROM partition_start)::TEXT, 2, '0');

        EXECUTE format('
            CREATE TABLE IF NOT EXISTS %I PARTITION OF %I
            FOR VALUES FROM (%L) TO (%L)',
            partition_name, table_name, partition_start, partition_end);

        partition_date := partition_end;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Create partitions for ingestion_errors (partitioned by created_at)
ALTER TABLE ingestion_errors DROP CONSTRAINT IF EXISTS ingestion_errors_pkey;
ALTER TABLE ingestion_errors ADD PRIMARY KEY (id, created_at);

-- Convert to partitioned table
CREATE TABLE ingestion_errors_temp (LIKE ingestion_errors);
ALTER TABLE ingestion_errors RENAME TO ingestion_errors_old;
ALTER TABLE ingestion_errors_temp RENAME TO ingestion_errors;

-- Create partitions
SELECT create_monthly_partitions('ingestion_errors', '2024-01-01', 24);

-- Migrate data (if any exists)
INSERT INTO ingestion_errors SELECT * FROM ingestion_errors_old;
DROP TABLE ingestion_errors_old;
```

## Setup Script

```bash
#!/bin/bash
# setup_monitoring_db.sh

# Database connection parameters
DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
DB_NAME=${DB_NAME:-opendiscourse}
DB_USER=${DB_USER:-postgres}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Setting up monitoring database schema..."

# Check if database exists
if ! psql -h $DB_HOST -p $DB_PORT -U $DB_USER -lqt | cut -d \| -f 1 | grep -qw $DB_NAME; then
    echo -e "${RED}Error: Database '$DB_NAME' does not exist${NC}"
    exit 1
fi

# Run schema creation
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f monitoring/database_schema.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Monitoring database schema created successfully${NC}"

    # Run initial data setup
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        -- Insert initial configuration if needed
        INSERT INTO ingestion_jobs (job_name, data_source, table_name, record_type, status)
        VALUES ('System Setup', 'internal', 'metadata', 'setup', 'completed')
        ON CONFLICT DO NOTHING;
    "

    echo -e "${GREEN}✅ Initial data inserted${NC}"
else
    echo -e "${RED}❌ Failed to create monitoring schema${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Monitoring database setup complete!${NC}"
```

## Migration Scripts

### From Basic to Advanced Monitoring

```sql
-- migration_001_add_advanced_monitoring.sql

-- Add new columns for enhanced monitoring
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS record_type VARCHAR(100);
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS throughput_per_minute NUMERIC DEFAULT 0;
ALTER TABLE ingestion_jobs ADD COLUMN IF NOT EXISTS eta_timestamp TIMESTAMP;

-- Add error metadata
ALTER TABLE ingestion_errors ADD COLUMN IF NOT EXISTS error_metadata JSONB DEFAULT '{}';
ALTER TABLE ingestion_errors ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Update existing records
UPDATE ingestion_jobs SET
    record_type = 'document',
    throughput_per_minute = 0,
    eta_timestamp = NULL
WHERE record_type IS NULL;

UPDATE ingestion_errors SET
    error_metadata = '{}',
    retry_count = 0
WHERE error_metadata IS NULL;

-- Add new indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_record_type ON ingestion_jobs(record_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_metadata ON ingestion_errors USING GIN(error_metadata);
```

## Backup and Recovery

### Backup Script

```bash
#!/bin/bash
# backup_monitoring_data.sh

BACKUP_DIR="/var/backups/opendiscourse/monitoring"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup monitoring tables
pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --table=ingestion_jobs \
    --table=ingestion_errors \
    --table=ingestion_progress_log \
    --format=custom \
    --compress=9 \
    --file=$BACKUP_DIR/monitoring_backup_$DATE.dump

# Also export as CSV for analysis
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    COPY ingestion_jobs TO '$BACKUP_DIR/jobs_$DATE.csv' WITH CSV HEADER;
    COPY ingestion_errors TO '$BACKUP_DIR/errors_$DATE.csv' WITH CSV HEADER;
"

echo "Backup completed: $BACKUP_DIR/monitoring_backup_$DATE.dump"
```

### Recovery Script

```bash
#!/bin/bash
# restore_monitoring_data.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

echo "Restoring monitoring data from $BACKUP_FILE..."

# Create temporary schema for restore testing
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    CREATE SCHEMA IF NOT EXISTS monitoring_restore;
"

# Restore to temporary schema first
pg_restore -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME \
    --schema=monitoring_restore \
    --create \
    --if-exists \
    --clean \
    $BACKUP_FILE

# Validate data integrity
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
    SELECT
        'Jobs: ' || COUNT(*) as job_count,
        'Errors: ' || COUNT(*) as error_count
    FROM monitoring_restore.ingestion_jobs,
         monitoring_restore.ingestion_errors;
"

read -p "Data looks good? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Move to production schema
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        DROP SCHEMA IF EXISTS monitoring_backup CASCADE;
        ALTER SCHEMA monitoring_restore RENAME TO monitoring_backup;
        -- Add production constraints and indexes
        ALTER TABLE monitoring_backup.ingestion_jobs ADD CONSTRAINT chk_status
            CHECK (status IN ('running', 'completed', 'failed', 'paused', 'cancelled'));
    "
    echo "✅ Restore completed successfully"
else
    # Cleanup
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "
        DROP SCHEMA monitoring_restore CASCADE;
    "
    echo "❌ Restore cancelled"
fi
```

## Monitoring Database Health

### Health Check Queries

```sql
-- Overall system health
SELECT
    'Active Jobs' as metric,
    COUNT(*) as value,
    CASE WHEN COUNT(*) > 10 THEN 'WARNING' ELSE 'OK' END as status
FROM ingestion_jobs
WHERE status = 'running'

UNION ALL

SELECT
    'Failed Jobs (24h)' as metric,
    COUNT(*) as value,
    CASE WHEN COUNT(*) > 5 THEN 'CRITICAL' ELSE 'OK' END as status
FROM ingestion_jobs
WHERE status = 'failed'
  AND started_at > NOW() - INTERVAL '24 hours'

UNION ALL

SELECT
    'Error Rate (1h)' as metric,
    ROUND(COUNT(*)::NUMERIC / GREATEST(COUNT(DISTINCT job_id), 1), 2) as value,
    CASE
        WHEN COUNT(*)::NUMERIC / GREATEST(COUNT(DISTINCT job_id), 1) > 50 THEN 'CRITICAL'
        WHEN COUNT(*)::NUMERIC / GREATEST(COUNT(DISTINCT job_id), 1) > 20 THEN 'WARNING'
        ELSE 'OK'
    END as status
FROM ingestion_errors
WHERE created_at > NOW() - INTERVAL '1 hour';
```

### Performance Monitoring

```sql
-- Slow queries in monitoring tables
SELECT
    query,
    calls,
    total_time / 1000 as total_seconds,
    mean_time / 1000 as mean_seconds,
    rows
FROM pg_stat_statements
WHERE query LIKE '%ingestion_%'
ORDER BY mean_time DESC
LIMIT 10;

-- Table bloat check
SELECT
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup,
    ROUND(n_dead_tup::NUMERIC / GREATEST(n_live_tup, 1) * 100, 2) as bloat_ratio
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'ingestion_%'
ORDER BY bloat_ratio DESC;
```

This comprehensive database setup provides the foundation for robust real-time progress monitoring across all OpenDiscourse ingestion processes.
