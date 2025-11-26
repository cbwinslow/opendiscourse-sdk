-- =============================================
-- Comprehensive Monitoring Dashboard
-- =============================================

-- Create monitoring dashboard schema
CREATE SCHEMA IF NOT EXISTS dashboard;

-- =============================================
-- Dashboard Views
-- =============================================

-- Overall system status
CREATE OR REPLACE VIEW dashboard.system_status AS
SELECT 
    'ingestion_system' as component,
    'healthy' as status,
    CURRENT_TIMESTAMP as last_check,
    json_build_object(
        'total_records', (SELECT COUNT(*) FROM congress.members) + (SELECT COUNT(*) FROM govinfo.members) + (SELECT COUNT(*) FROM openstates.people),
        'congress_records', (SELECT COUNT(*) FROM congress.members),
        'govinfo_records', (SELECT COUNT(*) FROM govinfo.members),
        'openstates_records', (SELECT COUNT(*) FROM openstates.people),
        'active_jobs', (SELECT COUNT(*) FROM ingestion.ingestion_jobs WHERE status = 'running'),
        'recent_errors', (SELECT COUNT(*) FROM ingestion.ingestion_errors WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour')
    ) as metrics;

-- Data source overview
CREATE OR REPLACE VIEW dashboard.data_source_overview AS
SELECT 
    data_source,
    total_records,
    last_ingestion,
    ingestion_status,
    error_count,
    CASE 
        WHEN error_count > 0 THEN 'error'
        WHEN total_records = 0 THEN 'empty'
        WHEN last_ingestion < CURRENT_TIMESTAMP - INTERVAL '7 days' THEN 'stale'
        ELSE 'healthy'
    END as health_status
FROM ingestion.get_ingestion_statistics();

-- Recent ingestion activity
CREATE OR REPLACE VIEW dashboard.recent_ingestion_activity AS
SELECT 
    ij.id,
    ij.job_name,
    ij.data_source,
    ij.table_name,
    ij.status,
    ij.total_estimated,
    ij.processed_records,
    ij.failed_records,
    CASE 
        WHEN ij.total_estimated > 0 
        THEN ROUND(ij.processed_records::NUMERIC / ij.total_estimated * 100, 2)
        ELSE 0
    END as progress_percent,
    ij.throughput_per_minute,
    ij.started_at,
    ij.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(ij.completed_at, CURRENT_TIMESTAMP) - ij.started_at))/60 as duration_minutes
FROM ingestion.ingestion_jobs ij
WHERE ij.started_at > CURRENT_TIMESTAMP - INTERVAL '7 days'
ORDER BY ij.started_at DESC;

-- Query performance summary
CREATE OR REPLACE VIEW dashboard.query_performance_summary AS
SELECT 
    'slow_queries' as metric,
    COUNT(*) as value,
    CASE 
        WHEN COUNT(*) > 10 THEN 'critical'
        WHEN COUNT(*) > 5 THEN 'warning'
        ELSE 'ok'
    END as status
FROM monitoring.slow_query_log
WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours'

UNION ALL

SELECT 
    'avg_query_duration_ms' as metric,
    ROUND(AVG(duration_ms)) as value,
    CASE 
        WHEN AVG(duration_ms) > 5000 THEN 'critical'
        WHEN AVG(duration_ms) > 1000 THEN 'warning'
        ELSE 'ok'
    END as status
FROM monitoring.query_execution_log
WHERE start_time > CURRENT_TIMESTAMP - INTERVAL '24 hours'

UNION ALL

SELECT 
    'total_queries_24h' as metric,
    COUNT(*) as value,
    'ok' as status
FROM monitoring.query_execution_log
WHERE start_time > CURRENT_TIMESTAMP - INTERVAL '24 hours';

-- Data quality metrics
CREATE OR REPLACE VIEW dashboard.data_quality_metrics AS
SELECT 
    schema_name,
    table_name,
    total_records,
    duplicate_count,
    deduplication_status,
    CASE 
        WHEN deduplication_status = 'OK' THEN 'good'
        WHEN duplicate_count > 10 THEN 'poor'
        ELSE 'fair'
    END as quality_score
FROM ingestion.validate_deduplication();

-- =============================================
-- Monitoring Procedures
-- =============================================

-- Procedure to get comprehensive dashboard data
CREATE OR REPLACE PROCEDURE dashboard.get_dashboard_data(
    OUT system_status JSONB,
    OUT data_sources JSONB,
    OUT recent_activity JSONB,
    OUT query_performance JSONB,
    OUT data_quality JSONB
)
LANGUAGE plpgsql AS $$
BEGIN
    -- System status
    SELECT json_agg(s) INTO system_status
    FROM (
        SELECT * FROM dashboard.system_status
    ) s;
    
    -- Data sources
    SELECT json_agg(ds) INTO data_sources
    FROM (
        SELECT * FROM dashboard.data_source_overview
    ) ds;
    
    -- Recent activity
    SELECT json_agg(ra) INTO recent_activity
    FROM (
        SELECT * FROM dashboard.recent_ingestion_activity LIMIT 10
    ) ra;
    
    -- Query performance
    SELECT json_agg(qp) INTO query_performance
    FROM (
        SELECT * FROM dashboard.query_performance_summary
    ) qp;
    
    -- Data quality
    SELECT json_agg(dq) INTO data_quality
    FROM (
        SELECT * FROM dashboard.data_quality_metrics
    ) dq;
END;
$$;

-- Procedure to generate health report
CREATE OR REPLACE PROCEDURE dashboard.generate_health_report(
    OUT overall_status TEXT,
    OUT issues JSONB,
    OUT recommendations TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    v_issues JSONB := '[]'::JSONB;
    v_recommendations TEXT[] := '{}';
    v_slow_queries INTEGER;
    v_failed_jobs INTEGER;
    v_stale_data INTEGER;
    v_duplicates INTEGER;
BEGIN
    -- Check for slow queries
    SELECT COUNT(*) INTO v_slow_queries
    FROM monitoring.slow_query_log
    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '24 hours';
    
    IF v_slow_queries > 5 THEN
        v_issues := v_issues || json_build_object(
            'type', 'performance',
            'severity', CASE WHEN v_slow_queries > 10 THEN 'high' ELSE 'medium' END,
            'message', format('%s slow queries in last 24 hours', v_slow_queries)
        );
        v_recommendations := array_append(v_recommendations, 'Review and optimize slow queries');
    END IF;
    
    -- Check for failed jobs
    SELECT COUNT(*) INTO v_failed_jobs
    FROM ingestion.ingestion_jobs
    WHERE status = 'failed' AND started_at > CURRENT_TIMESTAMP - INTERVAL '24 hours';
    
    IF v_failed_jobs > 0 THEN
        v_issues := v_issues || json_build_object(
            'type', 'ingestion',
            'severity', 'high',
            'message', format('%s failed ingestion jobs in last 24 hours', v_failed_jobs)
        );
        v_recommendations := array_append(v_recommendations, 'Review failed ingestion jobs and retry');
    END IF;
    
    -- Check for stale data
    SELECT COUNT(*) INTO v_stale_data
    FROM ingestion.get_ingestion_statistics()
    WHERE last_ingestion < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    IF v_stale_data > 0 THEN
        v_issues := v_issues || json_build_object(
            'type', 'freshness',
            'severity', 'medium',
            'message', format('%s data sources have stale data', v_stale_data)
        );
        v_recommendations := array_append(v_recommendations, 'Refresh stale data sources');
    END IF;
    
    -- Check for duplicates
    SELECT SUM(duplicate_count) INTO v_duplicates
    FROM ingestion.validate_deduplication()
    WHERE deduplication_status = 'DUPLICATES_FOUND';
    
    IF v_duplicates > 0 THEN
        v_issues := v_issues || json_build_object(
            'type', 'quality',
            'severity', 'medium',
            'message', format('%s duplicate records found', v_duplicates)
        );
        v_recommendations := array_append(v_recommendations, 'Clean up duplicate records');
    END IF;
    
    -- Determine overall status
    IF (SELECT COUNT(*) FROM jsonb_array_elements(v_issues) WHERE value->>'severity' = 'high') > 0 THEN
        overall_status := 'critical';
    ELSIF (SELECT COUNT(*) FROM jsonb_array_elements(v_issues)) > 0 THEN
        overall_status := 'warning';
    ELSE
        overall_status := 'healthy';
    END IF;
    
    issues := v_issues;
    recommendations := v_recommendations;
END;
$$;

-- Procedure to track query execution automatically
CREATE OR REPLACE PROCEDURE dashboard.track_query_execution(
    p_query_text TEXT,
    p_duration_ms INTEGER DEFAULT NULL,
    p_rows_affected INTEGER DEFAULT 0,
    p_rows_returned INTEGER DEFAULT 0,
    p_status VARCHAR(20) DEFAULT 'completed',
    p_error_message TEXT DEFAULT NULL
)
LANGUAGE plpgsql AS $$
DECLARE
    v_session_id VARCHAR(64);
    v_transaction_id VARCHAR(64);
BEGIN
    -- Get session and transaction identifiers
    v_session_id := COALESCE(current_setting('application_name', true), 'unknown') || '_' || pg_backend_pid();
    v_transaction_id := COALESCE(txid_current()::TEXT, 'unknown');
    
    -- Log the query execution
    CALL monitoring.log_query_execution(
        v_session_id,
        v_transaction_id,
        p_query_text,
        CURRENT_TIMESTAMP - (p_duration_ms || ' milliseconds')::INTERVAL,
        CURRENT_TIMESTAMP,
        p_duration_ms,
        p_rows_affected,
        p_rows_returned,
        p_status,
        p_error_message
    );
END;
$$;

-- =============================================
-- Automated Monitoring Triggers
-- =============================================

-- Function to create monitoring trigger for a table
CREATE OR REPLACE FUNCTION dashboard.create_monitoring_trigger(
    p_table_name TEXT,
    p_schema_name TEXT DEFAULT 'public'
)
RETURNS VOID AS $$
DECLARE
    v_trigger_name TEXT;
    v_trigger_sql TEXT;
BEGIN
    v_trigger_name := 'trg_monitor_' || p_table_name;
    
    -- Create trigger function
    v_trigger_sql := format($$
        CREATE OR REPLACE FUNCTION %s()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Track the DML operation
            PERFORM dashboard.track_query_execution(
                'DML on %I.%I: ' || TG_OP,
                NULL,
                CASE WHEN TG_OP = 'DELETE' THEN 1 ELSE 0 END,
                CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN 1 ELSE 0 END,
                'completed'
            );
            
            RETURN COALESCE(NEW, OLD);
        END;
        $$ LANGUAGE plpgsql;
    $$, v_trigger_name, p_schema_name, p_table_name);
    
    EXECUTE v_trigger_sql;
    
    -- Create trigger
    EXECUTE format($$
        CREATE TRIGGER %s
        AFTER INSERT OR UPDATE OR DELETE ON %I.%I
        FOR EACH ROW EXECUTE FUNCTION %s();
    $$, v_trigger_name, p_schema_name, p_table_name, v_trigger_name);
    
    RAISE NOTICE 'Created monitoring trigger for %.%', p_schema_name, p_table_name;
END;
$$ LANGUAGE plpgsql;

-- Procedure to set up monitoring for all ingestion tables
CREATE OR REPLACE PROCEDURE dashboard.setup_ingestion_monitoring()
LANGUAGE plpgsql AS $$
BEGIN
    -- Congress tables
    PERFORM dashboard.create_monitoring_trigger('members', 'congress');
    PERFORM dashboard.create_monitoring_trigger('member_terms', 'congress');
    
    -- GovInfo tables
    PERFORM dashboard.create_monitoring_trigger('members', 'govinfo');
    
    -- OpenStates tables
    PERFORM dashboard.create_monitoring_trigger('people', 'openstates');
    
    -- Ingestion tracking tables
    PERFORM dashboard.create_monitoring_trigger('ingestion_jobs', 'ingestion');
    PERFORM dashboard.create_monitoring_trigger('ingestion_errors', 'ingestion');
    
    -- Monitoring tables
    PERFORM dashboard.create_monitoring_trigger('query_execution_log', 'monitoring');
    PERFORM dashboard.create_monitoring_trigger('slow_query_log', 'monitoring');
    
    RAISE NOTICE 'Ingestion monitoring setup completed';
END;
$$;

-- =============================================
-- Alert System
-- =============================================

-- Alert types table
CREATE TABLE IF NOT EXISTS dashboard.alert_types (
    id SERIAL PRIMARY KEY,
    alert_code VARCHAR(50) UNIQUE NOT NULL,
    alert_name VARCHAR(100) NOT NULL,
    description TEXT,
    default_severity VARCHAR(20) DEFAULT 'medium',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Active alerts table
CREATE TABLE IF NOT EXISTS dashboard.active_alerts (
    id BIGSERIAL PRIMARY KEY,
    alert_code VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    source_table VARCHAR(100),
    source_record_id VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (alert_code) REFERENCES dashboard.alert_types(alert_code)
);

-- Procedure to create an alert
CREATE OR REPLACE PROCEDURE dashboard.create_alert(
    p_alert_code VARCHAR(50),
    p_severity VARCHAR(20),
    p_title VARCHAR(200),
    p_message TEXT,
    p_source_table VARCHAR(100) DEFAULT NULL,
    p_source_record_id VARCHAR(100) DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}'
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO dashboard.active_alerts (
        alert_code, severity, title, message, source_table, 
        source_record_id, metadata
    ) VALUES (
        p_alert_code, p_severity, p_title, p_message, p_source_table,
        p_source_record_id, p_metadata
    );
END;
$$;

-- Procedure to check for alerts
CREATE OR REPLACE PROCEDURE dashboard.check_for_alerts()
LANGUAGE plpgsql AS $$
DECLARE
    v_slow_query_count INTEGER;
    v_failed_job_count INTEGER;
    v_duplicate_count INTEGER;
BEGIN
    -- Check for slow queries
    SELECT COUNT(*) INTO v_slow_query_count
    FROM monitoring.slow_query_log
    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    IF v_slow_query_count > 5 THEN
        CALL dashboard.create_alert(
            'SLOW_QUERIES',
            CASE WHEN v_slow_query_count > 10 THEN 'high' ELSE 'medium' END,
            'High Number of Slow Queries',
            format('Detected %s slow queries in the last hour', v_slow_query_count),
            'query_execution_log',
            NULL,
            json_build_object('count', v_slow_query_count)
        );
    END IF;
    
    -- Check for failed jobs
    SELECT COUNT(*) INTO v_failed_job_count
    FROM ingestion.ingestion_jobs
    WHERE status = 'failed' AND started_at > CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    IF v_failed_job_count > 0 THEN
        CALL dashboard.create_alert(
            'FAILED_JOBS',
            'high',
            'Failed Ingestion Jobs',
            format('Detected %s failed ingestion jobs in the last hour', v_failed_job_count),
            'ingestion_jobs',
            NULL,
            json_build_object('count', v_failed_job_count)
        );
    END IF;
    
    -- Check for duplicates
    SELECT SUM(duplicate_count) INTO v_duplicate_count
    FROM ingestion.validate_deduplication()
    WHERE deduplication_status = 'DUPLICATES_FOUND';
    
    IF v_duplicate_count > 0 THEN
        CALL dashboard.create_alert(
            'DUPLICATES',
            'medium',
            'Duplicate Records Detected',
            format('Found %s duplicate records across data sources', v_duplicate_count),
            NULL,
            NULL,
            json_build_object('count', v_duplicate_count)
        );
    END IF;
END;
$$;

-- Initialize alert types
INSERT INTO dashboard.alert_types (alert_code, alert_name, description, default_severity) VALUES
('SLOW_QUERIES', 'Slow Queries', 'High number of slow queries detected', 'medium'),
('FAILED_JOBS', 'Failed Jobs', 'Ingestion jobs have failed', 'high'),
('DUPLICATES', 'Duplicate Records', 'Duplicate records found in data sources', 'medium'),
('STALE_DATA', 'Stale Data', 'Data has not been updated recently', 'low'),
('HIGH_ERROR_RATE', 'High Error Rate', 'High error rate in queries or operations', 'high')
ON CONFLICT (alert_code) DO NOTHING;

-- =============================================
-- Grant Permissions
-- =============================================

GRANT USAGE ON SCHEMA dashboard TO PUBLIC;
GRANT SELECT ON ALL TABLES IN SCHEMA dashboard TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dashboard TO PUBLIC;
GRANT EXECUTE ON ALL PROCEDURES IN SCHEMA dashboard TO PUBLIC;

COMMENT ON SCHEMA dashboard IS 'Comprehensive monitoring dashboard with alerts and health checks';