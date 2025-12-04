-- Migration 016: Deduplication Tracking Tables
-- Add tables for tracking record fingerprints and preventing duplicates

BEGIN;

-- Create schema for deduplication tracking
CREATE SCHEMA IF NOT EXISTS deduplication;

-- ============================================================================
-- Fingerprint Tracking Table
-- ============================================================================

CREATE TABLE IF NOT EXISTS deduplication.fingerprints (
    id SERIAL PRIMARY KEY,

    -- Record identification
    record_type VARCHAR(50) NOT NULL,
    record_id VARCHAR(255) NOT NULL,

    -- Content fingerprint
    content_hash VARCHAR(64) NOT NULL,  -- SHA256 hash

    -- Database reference
    database_id INTEGER,  -- FK to actual record (nullable for flexibility)
    schema_name VARCHAR(50),  -- Which schema (congress, openstates, govinfo)
    table_name VARCHAR(100),  -- Which table

    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Metadata
    field_count INTEGER,
    has_include_filter BOOLEAN DEFAULT FALSE,
    has_exclude_filter BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',

    -- Constraints
    UNIQUE(record_type, record_id),
    UNIQUE(content_hash, record_type)
);

-- Indexes for performance
CREATE INDEX idx_fingerprints_type_id ON deduplication.fingerprints(record_type, record_id);
CREATE INDEX idx_fingerprints_hash ON deduplication.fingerprints(content_hash);
CREATE INDEX idx_fingerprints_updated ON deduplication.fingerprints(updated_at);
CREATE INDEX idx_fingerprints_schema_table ON deduplication.fingerprints(schema_name, table_name);

-- ============================================================================
-- Duplicate Detection Log
-- ============================================================================

CREATE TABLE IF NOT EXISTS deduplication.duplicate_log (
    id SERIAL PRIMARY KEY,

    -- Record information
    record_type VARCHAR(50) NOT NULL,
    record_id VARCHAR(255) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,

    -- Detection details
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    strategy VARCHAR(20) NOT NULL,  -- skip, update, error, version
    action_taken VARCHAR(50) NOT NULL,  -- skipped, updated, error_raised, versioned

    -- Original vs new
    original_fingerprint_id INTEGER REFERENCES deduplication.fingerprints(id),
    changes_detected JSONB,  -- What changed between versions

    -- Context
    source VARCHAR(50),  -- Which CLI tool detected it
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX idx_duplicate_log_detected ON deduplication.duplicate_log(detected_at);
CREATE INDEX idx_duplicate_log_type ON deduplication.duplicate_log(record_type);
CREATE INDEX idx_duplicate_log_strategy ON deduplication.duplicate_log(strategy);

-- ============================================================================
-- Ingestion Session Tracking
-- ============================================================================

CREATE TABLE IF NOT EXISTS deduplication.ingestion_sessions (
    id SERIAL PRIMARY KEY,

    -- Session identification
    session_id UUID NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    source VARCHAR(50) NOT NULL,  -- congress, openstates, govinfo
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Configuration
    strategy VARCHAR(20) NOT NULL,
    dry_run BOOLEAN DEFAULT FALSE,

    -- Statistics
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    duplicates_detected INTEGER DEFAULT 0,
    errors_encountered INTEGER DEFAULT 0,

    -- Metadata
    config JSONB DEFAULT '{}',
    summary JSONB DEFAULT '{}'
);

-- Index
CREATE INDEX idx_ingestion_sessions_started ON deduplication.ingestion_sessions(started_at);
CREATE INDEX idx_ingestion_sessions_source ON deduplication.ingestion_sessions(source);

-- ============================================================================
-- Functions
-- ============================================================================

-- Function to update fingerprint timestamp on duplicate detection
CREATE OR REPLACE FUNCTION deduplication.update_fingerprint_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE deduplication.fingerprints
    SET last_seen_at = NOW()
    WHERE record_type = NEW.record_type
      AND record_id = NEW.record_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update last_seen when duplicate logged
CREATE TRIGGER trigger_update_last_seen
AFTER INSERT ON deduplication.duplicate_log
FOR EACH ROW
EXECUTE FUNCTION deduplication.update_fingerprint_last_seen();

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION deduplication.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for fingerprints table
CREATE TRIGGER trigger_fingerprints_updated_at
BEFORE UPDATE ON deduplication.fingerprints
FOR EACH ROW
EXECUTE FUNCTION deduplication.update_updated_at();

-- ============================================================================
-- Views for Monitoring
-- ============================================================================

-- View: Recent duplicates detected
CREATE OR REPLACE VIEW deduplication.v_recent_duplicates AS
SELECT
    record_type,
    record_id,
    strategy,
    action_taken,
    detected_at,
    changes_detected
FROM deduplication.duplicate_log
WHERE detected_at > NOW() - INTERVAL '7 days'
ORDER BY detected_at DESC
LIMIT 1000;

-- View: Deduplication statistics by type
CREATE OR REPLACE VIEW deduplication.v_stats_by_type AS
SELECT
    record_type,
    COUNT(*) as total_fingerprints,
    COUNT(DISTINCT content_hash) as unique_hashes,
    MAX(updated_at) as most_recent_update,
    AVG(field_count) as avg_field_count
FROM deduplication.fingerprints
GROUP BY record_type;

-- View: Session summary
CREATE OR REPLACE VIEW deduplication.v_session_summary AS
SELECT
    session_id,
    source,
    started_at,
    completed_at,
    EXTRACT(EPOCH FROM (COALESCE(completed_at, NOW()) - started_at)) as duration_seconds,
    records_processed,
    records_inserted,
    records_updated,
    records_skipped,
    duplicates_detected,
    CASE
        WHEN records_processed > 0 THEN
            ROUND((duplicates_detected::NUMERIC / records_processed * 100), 2)
        ELSE 0
    END as duplicate_rate_pct
FROM deduplication.ingestion_sessions
ORDER BY started_at DESC;

-- ============================================================================
-- Maintenance Functions
-- ============================================================================

-- Function to clean up old fingerprints (older than N days)
CREATE OR REPLACE FUNCTION deduplication.cleanup_old_fingerprints(days_to_keep INTEGER DEFAULT 365)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM deduplication.fingerprints
    WHERE last_seen_at < NOW() - (days_to_keep || ' days')::INTERVAL;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get duplicate statistics
CREATE OR REPLACE FUNCTION deduplication.get_duplicate_stats()
RETURNS TABLE (
    record_type VARCHAR(50),
    total_records BIGINT,
    duplicate_count BIGINT,
    duplicate_rate_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        dl.record_type,
        COUNT(DISTINCT dl.record_id) as total_records,
        COUNT(*) as duplicate_count,
        ROUND((COUNT(*)::NUMERIC / COUNT(DISTINCT dl.record_id) * 100), 2) as duplicate_rate_pct
    FROM deduplication.duplicate_log dl
    GROUP BY dl.record_type
    ORDER BY duplicate_count DESC;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Usage Examples:
--
-- Check for duplicates before insert:
-- SELECT EXISTS(
--     SELECT 1 FROM deduplication.fingerprints
--     WHERE record_type = 'bill' AND record_id = 'BILLS-118hr1'
-- );
--
-- Insert fingerprint:
-- INSERT INTO deduplication.fingerprints (record_type, record_id, content_hash, database_id, schema_name, table_name)
-- VALUES ('bill', 'BILLS-118hr1', 'abc123...', 12345, 'congress', 'bills')
-- ON CONFLICT (record_type, record_id) DO UPDATE
-- SET content_hash = EXCLUDED.content_hash,
--     updated_at = NOW(),
--     last_seen_at = NOW();
--
-- Log duplicate detection:
-- INSERT INTO deduplication.duplicate_log (record_type, record_id, content_hash, strategy, action_taken)
-- VALUES ('bill', 'BILLS-118hr1', 'abc123...', 'update', 'updated');
--
-- Get stats:
-- SELECT * FROM deduplication.v_stats_by_type;
--
-- Cleanup old records:
-- SELECT deduplication.cleanup_old_fingerprints(180);  -- Keep last 6 months
