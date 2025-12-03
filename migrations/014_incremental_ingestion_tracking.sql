-- =============================================
-- Incremental Ingestion Tracking System
-- =============================================

-- Create incremental tracking schema
CREATE SCHEMA IF NOT EXISTS incremental;

-- =============================================
-- Ingestion Progress Tracking Tables
-- =============================================

-- Data source checkpoint table
CREATE TABLE IF NOT EXISTS incremental.ingestion_checkpoints (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(100) NOT NULL, -- congress.gov, govinfo.gov, openstates.org
    data_type VARCHAR(100) NOT NULL, -- members, bills, votes, etc.
    category VARCHAR(100) NOT NULL, -- congress number, state, jurisdiction, etc.

    -- Progress tracking
    last_offset INTEGER NOT NULL DEFAULT 0,
    last_page INTEGER NOT NULL DEFAULT 1,
    last_id VARCHAR(500), -- Last processed record ID
    last_timestamp TIMESTAMP WITH TIME ZONE, -- Last processed timestamp

    -- Completion status
    is_completed BOOLEAN NOT NULL DEFAULT FALSE,
    total_processed INTEGER NOT NULL DEFAULT 0,
    total_estimated INTEGER,
    completion_percentage NUMERIC(5,2) DEFAULT 0,

    -- Metadata
    last_ingestion_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    checkpoint_metadata JSONB DEFAULT '{}',

    -- Constraints
    UNIQUE(data_source, data_type, category),
    CHECK (last_offset >= 0),
    CHECK (last_page >= 1),
    CHECK (completion_percentage BETWEEN 0 AND 100)
);

-- Record fingerprint table to avoid duplicates
CREATE TABLE IF NOT EXISTS incremental.record_fingerprints (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL,
    record_id VARCHAR(500) NOT NULL,
    record_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of record content
    record_timestamp TIMESTAMP WITH TIME ZONE,

    -- Metadata
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fingerprint_metadata JSONB DEFAULT '{}',

    -- Constraints
    UNIQUE(data_source, data_type, record_id)
);

-- Ingestion session tracking
CREATE TABLE IF NOT EXISTS incremental.ingestion_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    data_type VARCHAR(100) NOT NULL,

    -- Session metadata
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'paused')),

    -- Progress
    checkpoints_processed INTEGER NOT NULL DEFAULT 0,
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_skipped INTEGER NOT NULL DEFAULT 0,
    records_failed INTEGER NOT NULL DEFAULT 0,

    -- Session details
    session_metadata JSONB DEFAULT '{}',
    error_summary TEXT
);

-- =============================================
-- Indexes for Performance
-- =============================================

CREATE INDEX IF NOT EXISTS idx_ingestion_checkpoints_source_type ON incremental.ingestion_checkpoints(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_ingestion_checkpoints_category ON incremental.ingestion_checkpoints(category);
CREATE INDEX IF NOT EXISTS idx_ingestion_checkpoints_completed ON incremental.ingestion_checkpoints(is_completed);
CREATE INDEX IF NOT EXISTS idx_ingestion_checkpoints_last_ingestion ON incremental.ingestion_checkpoints(last_ingestion_at DESC);

CREATE INDEX IF NOT EXISTS idx_record_fingerprints_source_type ON incremental.record_fingerprints(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_record_fingerprints_record_id ON incremental.record_fingerprints(record_id);
CREATE INDEX IF NOT EXISTS idx_record_fingerprints_hash ON incremental.record_fingerprints(record_hash);
CREATE INDEX IF NOT EXISTS idx_record_fingerprints_last_updated ON incremental.record_fingerprints(last_updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_sessions_status ON incremental.ingestion_sessions(status);
CREATE INDEX IF NOT EXISTS idx_ingestion_sessions_started_at ON incremental.ingestion_sessions(started_at DESC);

-- =============================================
-- Incremental Ingestion Functions
-- =============================================

-- Function to get or create checkpoint
CREATE OR REPLACE FUNCTION incremental.get_or_create_checkpoint(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100),
    p_total_estimated INTEGER DEFAULT NULL
)
RETURNS incremental.ingestion_checkpoints AS $$
DECLARE
    v_checkpoint incremental.ingestion_checkpoints%ROWTYPE;
BEGIN
    -- Try to get existing checkpoint
    SELECT * INTO v_checkpoint
    FROM incremental.ingestion_checkpoints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND category = p_category;

    -- If not found, create new checkpoint
    IF NOT FOUND THEN
        INSERT INTO incremental.ingestion_checkpoints (
            data_source, data_type, category, total_estimated
        ) VALUES (
            p_data_source, p_data_type, p_category, p_total_estimated
        ) RETURNING * INTO v_checkpoint;
    END IF;

    RETURN v_checkpoint;
EXCEPTION WHEN UNIQUE_VIOLATION THEN
    -- Handle race condition - try again
    SELECT * INTO v_checkpoint
    FROM incremental.ingestion_checkpoints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND category = p_category;

    RETURN v_checkpoint;
END;
$$ LANGUAGE plpgsql;

-- Function to update checkpoint progress
CREATE OR REPLACE FUNCTION incremental.update_checkpoint_progress(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100),
    p_last_offset INTEGER DEFAULT NULL,
    p_last_page INTEGER DEFAULT NULL,
    p_last_id VARCHAR(500) DEFAULT NULL,
    p_last_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_records_processed INTEGER DEFAULT 0,
    p_is_completed BOOLEAN DEFAULT FALSE
)
RETURNS VOID AS $$
DECLARE
    v_checkpoint incremental.ingestion_checkpoints%ROWTYPE;
    v_completion_percentage NUMERIC(5,2);
BEGIN
    -- Get current checkpoint
    SELECT * INTO v_checkpoint
    FROM incremental.ingestion_checkpoints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND category = p_category;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Checkpoint not found for %.%.%', p_data_source, p_data_type, p_category;
    END IF;

    -- Calculate completion percentage
    IF v_checkpoint.total_estimated > 0 THEN
        v_completion_percentage := (
            (v_checkpoint.total_processed + p_records_processed)::NUMERIC /
            v_checkpoint.total_estimated * 100
        );
    ELSE
        v_completion_percentage := 0;
    END IF;

    -- Update checkpoint
    UPDATE incremental.ingestion_checkpoints SET
        last_offset = COALESCE(p_last_offset, last_offset),
        last_page = COALESCE(p_last_page, last_page),
        last_id = COALESCE(p_last_id, last_id),
        last_timestamp = COALESCE(p_last_timestamp, last_timestamp),
        is_completed = p_is_completed,
        total_processed = total_processed + p_records_processed,
        completion_percentage = v_completion_percentage,
        last_ingestion_at = CURRENT_TIMESTAMP
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND category = p_category;
END;
$$ LANGUAGE plpgsql;

-- Function to check if record was already processed
CREATE OR REPLACE FUNCTION incremental.is_record_processed(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_record_id VARCHAR(500),
    p_record_content JSONB DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_existing_hash VARCHAR(64);
    v_new_hash VARCHAR(64);
    v_exists BOOLEAN := FALSE;
BEGIN
    -- Check if record exists
    SELECT record_hash INTO v_existing_hash
    FROM incremental.record_fingerprints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND record_id = p_record_id;

    -- If record content provided, check for changes
    IF p_record_content IS NOT NULL THEN
        v_new_hash := encode(sha256(convert_to(p_record_content::TEXT, 'UTF-8')), 'hex');

        IF v_existing_hash IS NOT NULL THEN
            -- Record exists, check if content changed
            IF v_existing_hash = v_new_hash THEN
                v_exists := TRUE; -- Same content, already processed
            ELSE
                -- Content changed, update fingerprint
                UPDATE incremental.record_fingerprints SET
                    record_hash = v_new_hash,
                    last_updated_at = CURRENT_TIMESTAMP
                WHERE data_source = p_data_source
                  AND data_type = p_data_type
                  AND record_id = p_record_id;
            END IF;
        ELSE
            -- New record, add fingerprint
            INSERT INTO incremental.record_fingerprints (
                data_source, data_type, record_id, record_hash, record_timestamp
            ) VALUES (
                p_data_source, p_data_type, p_record_id, v_new_hash,
                (p_record_content->>'updated_at')::TIMESTAMP WITH TIME ZONE
            );
        END IF;
    ELSE
        -- No content provided, just check existence
        v_exists := (v_existing_hash IS NOT NULL);
    END IF;

    RETURN v_exists;
EXCEPTION WHEN OTHERS THEN
    -- If fingerprint check fails, assume not processed to be safe
    RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- Function to start ingestion session
CREATE OR REPLACE FUNCTION incremental.start_ingestion_session(
    p_session_id VARCHAR(100),
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_session_metadata JSONB DEFAULT '{}'
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO incremental.ingestion_sessions (
        session_id, data_source, data_type, session_metadata
    ) VALUES (
        p_session_id, p_data_source, p_data_type, p_session_metadata
    );
END;
$$ LANGUAGE plpgsql;

-- Function to complete ingestion session
CREATE OR REPLACE FUNCTION incremental.complete_ingestion_session(
    p_session_id VARCHAR(100),
    p_status VARCHAR(20) DEFAULT 'completed',
    p_error_summary TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE incremental.ingestion_sessions SET
        status = p_status,
        completed_at = CURRENT_TIMESTAMP,
        error_summary = p_error_summary
    WHERE session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Utility Views and Functions
-- =============================================

-- View for checkpoint status
CREATE OR REPLACE VIEW incremental.checkpoint_status AS
SELECT
    data_source,
    data_type,
    category,
    last_offset,
    last_page,
    last_id,
    is_completed,
    total_processed,
    total_estimated,
    completion_percentage,
    last_ingestion_at,
    error_count,
    CASE
        WHEN is_completed THEN '✅ COMPLETED'
        WHEN completion_percentage > 0 THEN '🔄 IN PROGRESS'
        WHEN error_count > 0 THEN '❌ ERROR'
        ELSE '📋 NOT STARTED'
    END as status
FROM incremental.ingestion_checkpoints
ORDER BY data_source, data_type, category;

-- Function to get next ingestion parameters
CREATE OR REPLACE FUNCTION incremental.get_next_ingestion_params(
    p_data_source VARCHAR(100),
    p_data_type VARCHAR(100),
    p_category VARCHAR(100)
)
RETURNS TABLE(
    next_offset INTEGER,
    next_page INTEGER,
    start_from_id VARCHAR(500),
    start_from_timestamp TIMESTAMP WITH TIME ZONE,
    is_completed BOOLEAN
) AS $$
DECLARE
    v_checkpoint incremental.ingestion_checkpoints%ROWTYPE;
BEGIN
    -- Get checkpoint
    SELECT * INTO v_checkpoint
    FROM incremental.ingestion_checkpoints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND category = p_category;

    IF NOT FOUND THEN
        -- Create new checkpoint
        v_checkpoint := incremental.get_or_create_checkpoint(p_data_source, p_data_type, p_category);
    END IF;

    -- Return next parameters
    RETURN QUERY SELECT
        v_checkpoint.last_offset,
        v_checkpoint.last_page,
        v_checkpoint.last_id,
        v_checkpoint.last_timestamp,
        v_checkpoint.is_completed;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Grant Permissions
-- =============================================

GRANT USAGE ON SCHEMA incremental TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA incremental TO PUBLIC;
GRANT INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA incremental TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA incremental TO PUBLIC;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA incremental TO PUBLIC;

COMMENT ON SCHEMA incremental IS 'Incremental ingestion tracking and checkpoint system';
