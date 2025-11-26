-- =============================================
-- Ingestion Tracking Tables
-- =============================================

-- Create ingestion schema if not exists
CREATE SCHEMA IF NOT EXISTS ingestion;

-- Main ingestion jobs table
CREATE TABLE IF NOT EXISTS ingestion.ingestion_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(255) NOT NULL,
    data_source VARCHAR(100) NOT NULL, -- congress.gov, govinfo.gov, openstates.org
    table_name VARCHAR(100) NOT NULL DEFAULT 'members',
    record_type VARCHAR(100) NOT NULL, -- members, people, etc.
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'paused', 'cancelled')),

    -- Progress tracking
    total_estimated INTEGER,
    processed_records INTEGER NOT NULL DEFAULT 0,
    failed_records INTEGER NOT NULL DEFAULT 0,
    throughput_per_minute NUMERIC DEFAULT 0,
    current_record_id VARCHAR(500),

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Metadata
    metadata JSONB DEFAULT '{}'
);

-- Ingestion errors table
CREATE TABLE IF NOT EXISTS ingestion.ingestion_errors (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES ingestion.ingestion_jobs(id) ON DELETE CASCADE,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    record_id VARCHAR(500),
    resolved BOOLEAN NOT NULL DEFAULT FALSE,
    error_metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================================
-- Indexes for Ingestion Tables
-- =============================================

-- Ingestion jobs indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status ON ingestion.ingestion_jobs(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_data_source ON ingestion.ingestion_jobs(data_source);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_started_at ON ingestion.ingestion_jobs(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_table_name ON ingestion.ingestion_jobs(table_name);

-- Ingestion errors indexes
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_job_id ON ingestion.ingestion_errors(job_id);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_type ON ingestion.ingestion_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_resolved ON ingestion.ingestion_errors(resolved);
CREATE INDEX IF NOT EXISTS idx_ingestion_errors_created_at ON ingestion.ingestion_errors(created_at DESC);

-- =============================================
-- Grant Permissions
-- =============================================

GRANT USAGE ON SCHEMA ingestion TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA ingestion TO PUBLIC;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ingestion TO PUBLIC;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA ingestion TO PUBLIC;

COMMENT ON SCHEMA ingestion IS 'Ingestion job tracking and error logging';