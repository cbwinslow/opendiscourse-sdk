-- OpenDiscourse Progress Monitoring Database Setup
-- Run this to create monitoring tables in cbwinslow schema

-- Main jobs table
CREATE TABLE IF NOT EXISTS ingestion_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    data_source VARCHAR(255) NOT NULL,
    table_name VARCHAR(255) NOT NULL DEFAULT 'documents',
    record_type VARCHAR(100) NOT NULL,
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
CREATE TABLE IF NOT EXISTS ingestion_errors (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    record_id VARCHAR(500),
    retry_count INTEGER NOT NULL DEFAULT 0,
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    error_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Progress log for detailed tracking
CREATE TABLE IF NOT EXISTS ingestion_progress_log (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
    processed_records INTEGER NOT NULL,
    failed_records INTEGER NOT NULL,
    throughput_per_minute NUMERIC,
    current_record_id VARCHAR(500),
    log_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_data_source ON ingestion_jobs(data_source);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_started_at ON ingestion_jobs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_table_name ON ingestion_jobs(table_name);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_record_type ON ingestion_jobs(record_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_started ON ingestion_jobs(status, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_data_source_table ON ingestion_jobs(data_source, table_name);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_active ON ingestion_jobs(status) WHERE status IN ('running', 'paused');

-- Error indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_job_id ON ingestion_errors(job_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_type ON ingestion_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_resolved ON ingestion_errors(resolved);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_created_at ON ingestion_errors(created_at DESC);

-- Progress log indexes
CREATE INDEX IF NOT EXISTS idx_progress_log_job_id ON ingestion_progress_log(job_id);
CREATE INDEX IF NOT EXISTS idx_progress_log_timestamp ON ingestion_progress_log(log_timestamp DESC);

-- Views for Reporting
CREATE OR REPLACE VIEW active_ingestion_jobs AS
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
CREATE OR REPLACE VIEW ingestion_error_summary AS
SELECT
    job_id,
    error_type,
    COUNT(*) as error_count,
    COUNT(*) FILTER (WHERE resolved = FALSE) as unresolved_count,
    MAX(created_at) as last_error_at
FROM ingestion_errors
GROUP BY job_id, error_type;

-- Job performance view
CREATE OR REPLACE VIEW ingestion_job_performance AS
SELECT
    ij.id,
    ij.job_name,
    ij.data_source,
    ij.table_name,
    ij.record_type,
    ij.total_records,
    ij.processed_records,
    ij.failed_records,
    ROUND(ij.processed_records::NUMERIC / GREATEST(ij.total_records, 1) * 100, 2) as progress_percent,
    ij.throughput_per_minute,
    ij.eta_timestamp,
    ij.started_at,
    ij.completed_at,
    EXTRACT(EPOCH FROM (ij.completed_at - ij.started_at))/60 as duration_minutes,
    CASE 
        WHEN ij.status = 'completed' AND ij.processed_records > 0 
        THEN ij.processed_records / GREATEST(EXTRACT(EPOCH FROM (ij.completed_at - ij.started_at))/60, 0.01)
        ELSE NULL
    END as actual_throughput_per_minute
FROM ingestion_jobs ij
WHERE ij.status IN ('completed', 'failed')
ORDER BY ij.started_at DESC;