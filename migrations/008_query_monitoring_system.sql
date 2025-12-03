-- =============================================
-- Comprehensive Query Execution Monitoring System
-- =============================================

-- Create monitoring schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS monitoring;

-- =============================================
-- Query Execution Tracking Tables
-- =============================================

-- Main query execution log
CREATE TABLE IF NOT EXISTS monitoring.query_execution_log (
    id BIGSERIAL PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    transaction_id VARCHAR(64) NOT NULL,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL, -- SELECT, INSERT, UPDATE, DELETE, etc.
    table_names TEXT[], -- Array of table names involved
    schema_names TEXT[], -- Array of schema names involved
    
    -- Execution metrics
    start_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    rows_affected INTEGER DEFAULT 0,
    rows_returned INTEGER DEFAULT 0,
    
    -- Performance metrics
    cpu_time_ms INTEGER,
    io_time_ms INTEGER,
    memory_kb INTEGER,
    
    -- Status and errors
    status VARCHAR(20) NOT NULL DEFAULT 'running', -- running, completed, failed, cancelled
    error_message TEXT,
    error_code VARCHAR(10),
    
    -- Context information
    user_name VARCHAR(64) NOT NULL,
    database_name VARCHAR(64) NOT NULL,
    application_name VARCHAR(64),
    client_addr INET,
    
    -- Query classification
    is_dml BOOLEAN DEFAULT FALSE,
    is_ddl BOOLEAN DEFAULT FALSE,
    is_select BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Query performance aggregation table
CREATE TABLE IF NOT EXISTS monitoring.query_performance_stats (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    query_signature TEXT NOT NULL, -- Normalized query template
    
    -- Aggregated metrics
    total_executions BIGINT DEFAULT 0,
    total_duration_ms BIGINT DEFAULT 0,
    avg_duration_ms NUMERIC(10,2) DEFAULT 0,
    min_duration_ms INTEGER,
    max_duration_ms INTEGER,
    p95_duration_ms INTEGER,
    p99_duration_ms INTEGER,
    
    -- Row metrics
    total_rows_affected BIGINT DEFAULT 0,
    avg_rows_affected NUMERIC(10,2) DEFAULT 0,
    total_rows_returned BIGINT DEFAULT 0,
    avg_rows_returned NUMERIC(10,2) DEFAULT 0,
    
    -- Error metrics
    total_errors BIGINT DEFAULT 0,
    error_rate NUMERIC(5,2) DEFAULT 0,
    
    -- Time windows
    first_seen TIMESTAMP WITH TIME ZONE,
    last_seen TIMESTAMP WITH TIME ZONE,
    
    -- Performance classification
    performance_tier VARCHAR(20), -- fast, normal, slow, critical
    needs_optimization BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(query_hash)
);

-- Slow query log (for queries exceeding thresholds)
CREATE TABLE IF NOT EXISTS monitoring.slow_query_log (
    id BIGSERIAL PRIMARY KEY,
    query_execution_id BIGINT REFERENCES monitoring.query_execution_log(id),
    
    -- Slow query details
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    threshold_ms INTEGER NOT NULL,
    
    -- Performance impact
    impact_score NUMERIC(5,2), -- 0-100 based on duration and frequency
    estimated_cost_savings NUMERIC, -- Potential improvement if optimized
    
    -- Analysis
    missing_indexes TEXT[], -- Suggested indexes
    table_scans TEXT[], -- Tables that were scanned
    recommendations TEXT[], -- Optimization recommendations
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Query execution plan cache
CREATE TABLE IF NOT EXISTS monitoring.query_execution_plans (
    id BIGSERIAL PRIMARY KEY,
    query_hash VARCHAR(64) NOT NULL,
    plan_hash VARCHAR(64) NOT NULL,
    
    -- Plan details
    execution_plan JSONB NOT NULL,
    plan_cost NUMERIC,
    plan_rows BIGINT,
    plan_width INTEGER,
    
    -- Plan analysis
    uses_index BOOLEAN DEFAULT FALSE,
    uses_seq_scan BOOLEAN DEFAULT FALSE,
    uses_sort BOOLEAN DEFAULT FALSE,
    uses_hash BOOLEAN DEFAULT FALSE,
    uses_nested_loop BOOLEAN DEFAULT FALSE,
    
    -- Performance
    actual_cost NUMERIC,
    actual_rows BIGINT,
    actual_time_ms INTEGER,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(query_hash, plan_hash)
);

-- =============================================
-- Supporting Indexes
-- =============================================

-- Query execution log indexes
CREATE INDEX IF NOT EXISTS idx_query_execution_log_session_id ON monitoring.query_execution_log(session_id);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_query_hash ON monitoring.query_execution_log(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_start_time ON monitoring.query_execution_log(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_duration_ms ON monitoring.query_execution_log(duration_ms DESC);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_status ON monitoring.query_execution_log(status);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_user_name ON monitoring.query_execution_log(user_name);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_query_type ON monitoring.query_execution_log(query_type);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_table_names ON monitoring.query_execution_log USING GIN(table_names);
CREATE INDEX IF NOT EXISTS idx_query_execution_log_schema_names ON monitoring.query_execution_log USING GIN(schema_names);

-- Performance stats indexes
CREATE INDEX IF NOT EXISTS idx_query_performance_stats_total_executions ON monitoring.query_performance_stats(total_executions DESC);
CREATE INDEX IF NOT EXISTS idx_query_performance_stats_avg_duration_ms ON monitoring.query_performance_stats(avg_duration_ms DESC);
CREATE INDEX IF NOT EXISTS idx_query_performance_stats_performance_tier ON monitoring.query_performance_stats(performance_tier);
CREATE INDEX IF NOT EXISTS idx_query_performance_stats_needs_optimization ON monitoring.query_performance_stats(needs_optimization);

-- Slow query log indexes
CREATE INDEX IF NOT EXISTS idx_slow_query_log_duration_ms ON monitoring.slow_query_log(duration_ms DESC);
CREATE INDEX IF NOT EXISTS idx_slow_query_log_impact_score ON monitoring.slow_query_log(impact_score DESC);
CREATE INDEX IF NOT EXISTS idx_slow_query_log_created_at ON monitoring.slow_query_log(created_at DESC);

-- Execution plan indexes
CREATE INDEX IF NOT EXISTS idx_query_execution_plans_query_hash ON monitoring.query_execution_plans(query_hash);
CREATE INDEX IF NOT EXISTS idx_query_execution_plans_plan_cost ON monitoring.query_execution_plans(plan_cost DESC);

-- =============================================
-- Triggers and Functions for Query Tracking
-- =============================================

-- Function to extract table names from query text
CREATE OR REPLACE FUNCTION monitoring.extract_table_names(query_text TEXT)
RETURNS TEXT[] AS $$
DECLARE
    table_names TEXT[] := '{}';
    match TEXT;
BEGIN
    -- Simple regex to extract table names - can be enhanced
    FOR match IN 
        SELECT regexp_matches[1] 
        FROM regexp_matches(query_text, '(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)?)', 'gi') AS regexp_matches
    LOOP
        table_names := array_append(table_names, match);
    END LOOP;
    
    RETURN array(SELECT DISTINCT unnest(table_names));
END;
$$ LANGUAGE plpgsql;

-- Function to extract schema names from query text
CREATE OR REPLACE FUNCTION monitoring.extract_schema_names(query_text TEXT)
RETURNS TEXT[] AS $$
DECLARE
    schema_names TEXT[] := '{}';
    match TEXT;
    table_name TEXT;
BEGIN
    -- Extract schema.table patterns
    FOR match IN 
        SELECT regexp_matches[1] 
        FROM regexp_matches(query_text, '(?:FROM|JOIN|INTO|UPDATE)\s+([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)', 'gi') AS regexp_matches
    LOOP
        schema_names := array_append(schema_names, match);
    END LOOP;
    
    RETURN array(SELECT DISTINCT unnest(schema_names));
END;
$$ LANGUAGE plpgsql;

-- Function to generate query hash
CREATE OR REPLACE FUNCTION monitoring.generate_query_hash(query_text TEXT)
RETURNS VARCHAR(64) AS $$
BEGIN
    RETURN encode(sha256(convert_to(query_text, 'UTF-8')), 'hex');
END;
$$ LANGUAGE plpgsql;

-- Function to normalize query for signature
CREATE OR REPLACE FUNCTION monitoring.normalize_query(query_text TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Remove literal values and normalize whitespace
    RETURN regexp_replace(
        regexp_replace(
            regexp_replace(query_text, '\b\d+\b', '?', 'g'), -- Replace numbers
            "'[^']*'", '?', 'g' -- Replace string literals
        ),
        '\s+', ' ', 'g' -- Normalize whitespace
    );
END;
$$ LANGUAGE plpgsql;

-- Function to classify query type
CREATE OR REPLACE FUNCTION monitoring.classify_query_type(query_text TEXT)
RETURNS VARCHAR(50) AS $$
BEGIN
    query_text := upper(trim(query_text));
    
    IF strpos(query_text, 'SELECT') = 1 THEN
        RETURN 'SELECT';
    ELSIF strpos(query_text, 'INSERT') = 1 THEN
        RETURN 'INSERT';
    ELSIF strpos(query_text, 'UPDATE') = 1 THEN
        RETURN 'UPDATE';
    ELSIF strpos(query_text, 'DELETE') = 1 THEN
        RETURN 'DELETE';
    ELSIF strpos(query_text, 'CREATE') = 1 OR strpos(query_text, 'ALTER') = 1 OR strpos(query_text, 'DROP') = 1 THEN
        RETURN 'DDL';
    ELSIF strpos(query_text, 'GRANT') = 1 OR strpos(query_text, 'REVOKE') = 1 THEN
        RETURN 'DCL';
    ELSE
        RETURN 'OTHER';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Stored Procedures for Monitoring
-- =============================================

-- Procedure to log query execution
CREATE OR REPLACE PROCEDURE monitoring.log_query_execution(
    p_session_id VARCHAR(64),
    p_transaction_id VARCHAR(64),
    p_query_text TEXT,
    p_start_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    p_end_time TIMESTAMP WITH TIME ZONE DEFAULT NULL,
    p_duration_ms INTEGER DEFAULT NULL,
    p_rows_affected INTEGER DEFAULT 0,
    p_rows_returned INTEGER DEFAULT 0,
    p_status VARCHAR(20) DEFAULT 'completed',
    p_error_message TEXT DEFAULT NULL,
    p_user_name VARCHAR(64) DEFAULT CURRENT_USER,
    p_database_name VARCHAR(64) DEFAULT CURRENT_DATABASE(),
    p_application_name VARCHAR(64) DEFAULT NULL,
    p_client_addr INET DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_query_hash VARCHAR(64);
    v_query_type VARCHAR(50);
    v_table_names TEXT[];
    v_schema_names TEXT[];
    v_execution_id BIGINT;
BEGIN
    -- Generate query hash and extract metadata
    v_query_hash := monitoring.generate_query_hash(p_query_text);
    v_query_type := monitoring.classify_query_type(p_query_text);
    v_table_names := monitoring.extract_table_names(p_query_text);
    v_schema_names := monitoring.extract_schema_names(p_query_text);
    
    -- Insert into execution log
    INSERT INTO monitoring.query_execution_log (
        session_id, transaction_id, query_hash, query_text, query_type,
        table_names, schema_names, start_time, end_time, duration_ms,
        rows_affected, rows_returned, status, error_message,
        user_name, database_name, application_name, client_addr,
        is_dml, is_ddl, is_select, is_admin, metadata
    ) VALUES (
        p_session_id, p_transaction_id, v_query_hash, p_query_text, v_query_type,
        v_table_names, v_schema_names, p_start_time, p_end_time, p_duration_ms,
        p_rows_affected, p_rows_returned, p_status, p_error_message,
        p_user_name, p_database_name, p_application_name, p_client_addr,
        p_query_type IN ('INSERT', 'UPDATE', 'DELETE'),
        p_query_type = 'DDL',
        p_query_type = 'SELECT',
        FALSE, p_metadata
    ) RETURNING id INTO v_execution_id;
    
    -- Update performance statistics
    INSERT INTO monitoring.query_performance_stats (
        query_hash, query_signature, total_executions, avg_duration_ms,
        min_duration_ms, max_duration_ms, total_rows_affected, total_rows_returned,
        first_seen, last_seen, updated_at
    ) VALUES (
        v_query_hash, monitoring.normalize_query(p_query_text), 1, p_duration_ms,
        p_duration_ms, p_duration_ms, p_rows_affected, p_rows_returned,
        p_start_time, COALESCE(p_end_time, CURRENT_TIMESTAMP), CURRENT_TIMESTAMP
    )
    ON CONFLICT (query_hash) DO UPDATE SET
        total_executions = query_performance_stats.total_executions + 1,
        total_duration_ms = query_performance_stats.total_duration_ms + COALESCE(p_duration_ms, 0),
        avg_duration_ms = (query_performance_stats.total_duration_ms + COALESCE(p_duration_ms, 0)) / (query_performance_stats.total_executions + 1),
        min_duration_ms = LEAST(query_performance_stats.min_duration_ms, COALESCE(p_duration_ms, 0)),
        max_duration_ms = GREATEST(query_performance_stats.max_duration_ms, COALESCE(p_duration_ms, 0)),
        total_rows_affected = query_performance_stats.total_rows_affected + p_rows_affected,
        avg_rows_affected = (query_performance_stats.total_rows_affected + p_rows_affected) / (query_performance_stats.total_executions + 1),
        total_rows_returned = query_performance_stats.total_rows_returned + p_rows_returned,
        avg_rows_returned = (query_performance_stats.total_rows_returned + p_rows_returned) / (query_performance_stats.total_executions + 1),
        last_seen = COALESCE(p_end_time, CURRENT_TIMESTAMP),
        updated_at = CURRENT_TIMESTAMP;
    
    -- Check for slow queries
    IF p_duration_ms > 1000 THEN -- 1 second threshold
        INSERT INTO monitoring.slow_query_log (
            query_execution_id, query_hash, query_text, duration_ms, threshold_ms
        ) VALUES (
            v_execution_id, v_query_hash, p_query_text, p_duration_ms, 1000
        );
    END IF;
    
    -- Update performance tier
    UPDATE monitoring.query_performance_stats SET
        performance_tier = CASE
            WHEN avg_duration_ms < 100 THEN 'fast'
            WHEN avg_duration_ms < 1000 THEN 'normal'
            WHEN avg_duration_ms < 5000 THEN 'slow'
            ELSE 'critical'
        END,
        needs_optimization = CASE
            WHEN avg_duration_ms > 1000 OR total_errors > 0 THEN TRUE
            ELSE FALSE
        END
    WHERE query_hash = v_query_hash;
END;
$$;

-- =============================================
-- Views for Monitoring and Analysis
-- =============================================

-- Active queries view
CREATE OR REPLACE VIEW monitoring.active_queries AS
SELECT 
    qel.id,
    qel.session_id,
    qel.query_hash,
    qel.query_text,
    qel.query_type,
    qel.start_time,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - qel.start_time)) as running_seconds,
    qel.user_name,
    qel.application_name,
    qel.table_names,
    qel.schema_names
FROM monitoring.query_execution_log qel
WHERE qel.status = 'running'
ORDER BY qel.start_time;

-- Slow queries summary
CREATE OR REPLACE VIEW monitoring.slow_queries_summary AS
SELECT 
    sql.query_hash,
    sql.query_signature,
    sql.total_executions,
    sql.avg_duration_ms,
    sql.max_duration_ms,
    sql.total_errors,
    sql.error_rate,
    sql.performance_tier,
    sql.needs_optimization
FROM monitoring.query_performance_stats sql
WHERE sql.avg_duration_ms > 1000 OR sql.needs_optimization = TRUE
ORDER BY sql.avg_duration_ms DESC;

-- Query performance by table
CREATE OR REPLACE VIEW monitoring.query_performance_by_table AS
SELECT 
    unnest(qel.table_names) as table_name,
    qel.query_type,
    COUNT(*) as execution_count,
    AVG(qel.duration_ms) as avg_duration_ms,
    SUM(qel.rows_affected) as total_rows_affected,
    SUM(qel.rows_returned) as total_rows_returned,
    MAX(qel.duration_ms) as max_duration_ms
FROM monitoring.query_execution_log qel
WHERE qel.table_names IS NOT NULL
GROUP BY unnest(qel.table_names), qel.query_type
ORDER BY avg_duration_ms DESC;

-- User activity summary
CREATE OR REPLACE VIEW monitoring.user_activity_summary AS
SELECT 
    qel.user_name,
    COUNT(*) as total_queries,
    COUNT(*) FILTER (WHERE qel.query_type = 'SELECT') as select_queries,
    COUNT(*) FILTER (WHERE qel.query_type IN ('INSERT', 'UPDATE', 'DELETE')) as dml_queries,
    COUNT(*) FILTER (WHERE qel.query_type = 'DDL') as ddl_queries,
    AVG(qel.duration_ms) as avg_duration_ms,
    SUM(qel.rows_affected) as total_rows_affected,
    SUM(qel.rows_returned) as total_rows_returned,
    MAX(qel.start_time) as last_activity
FROM monitoring.query_execution_log qel
GROUP BY qel.user_name
ORDER BY total_queries DESC;

-- =============================================
-- Maintenance Procedures
-- =============================================

-- Procedure to clean old execution logs
CREATE OR REPLACE PROCEDURE monitoring.cleanup_old_execution_logs(
    p_days_to_keep INTEGER DEFAULT 30
)
LANGUAGE plpgsql AS $$
BEGIN
    -- Delete old execution logs
    DELETE FROM monitoring.query_execution_log 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    -- Update performance stats for remaining queries
    UPDATE monitoring.query_performance_stats 
    SET first_seen = (
        SELECT MIN(start_time) 
        FROM monitoring.query_execution_log qel 
        WHERE qel.query_hash = query_performance_stats.query_hash
    ),
    last_seen = (
        SELECT MAX(start_time) 
        FROM monitoring.query_execution_log qel 
        WHERE qel.query_hash = query_performance_stats.query_hash
    );
    
    -- Delete orphaned slow query logs
    DELETE FROM monitoring.slow_query_log 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day' * p_days_to_keep;
    
    RAISE NOTICE 'Cleaned up execution logs older than % days', p_days_to_keep;
END;
$$;

-- Procedure to analyze query performance
CREATE OR REPLACE PROCEDURE monitoring.analyze_query_performance()
LANGUAGE plpgsql AS $$
BEGIN
    -- Update performance tiers
    UPDATE monitoring.query_performance_stats SET
        performance_tier = CASE
            WHEN avg_duration_ms < 100 THEN 'fast'
            WHEN avg_duration_ms < 1000 THEN 'normal'
            WHEN avg_duration_ms < 5000 THEN 'slow'
            ELSE 'critical'
        END,
        needs_optimization = CASE
            WHEN avg_duration_ms > 1000 OR total_errors > 0 THEN TRUE
            ELSE FALSE
        END;
    
    -- Calculate percentiles
    UPDATE monitoring.query_performance_stats SET
        p95_duration_ms = (
            SELECT PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms)
            FROM monitoring.query_execution_log qel
            WHERE qel.query_hash = query_performance_stats.query_hash
        ),
        p99_duration_ms = (
            SELECT PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY duration_ms)
            FROM monitoring.query_execution_log qel
            WHERE qel.query_hash = query_performance_stats.query_hash
        );
    
    RAISE NOTICE 'Query performance analysis completed';
END;
$$;

-- =============================================
-- Grant Permissions
-- =============================================

-- Grant necessary permissions (adjust as needed)
GRANT USAGE ON SCHEMA monitoring TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA monitoring TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA monitoring TO PUBLIC;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA monitoring TO PUBLIC;

COMMENT ON SCHEMA monitoring IS 'Comprehensive query execution monitoring system';