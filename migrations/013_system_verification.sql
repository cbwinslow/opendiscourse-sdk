-- =============================================
-- Final System Verification and Testing
-- =============================================

-- Test the monitoring system with proper data types
CALL dashboard.track_query_execution(
    'SELECT COUNT(*) FROM congress.members',
    50,
    0,
    1,
    'completed'
);

-- Test ingestion job tracking
SELECT ingestion.start_ingestion_job(
    'Test Congress Members Ingestion',
    'congress.gov',
    'members',
    'members',
    1901,
    '{"test": true}'
) as test_job_id;

-- Update test job progress (using SELECT instead of CALL for functions)
SELECT ingestion.update_ingestion_progress(
    1, -- job_id
    100,
    0,
    'test_record_001'
);

-- Complete test job
SELECT ingestion.complete_ingestion_job(
    1,
    'completed',
    '{"test_completed": true}'
);

-- Add test alert type first
INSERT INTO dashboard.alert_types (alert_code, alert_name, description, default_severity) VALUES
('TEST_ALERT', 'Test Alert', 'Test alert for system verification', 'low')
ON CONFLICT (alert_code) DO NOTHING;

-- Test alert creation
CALL dashboard.create_alert(
    'TEST_ALERT',
    'low',
    'Test Alert',
    'This is a test alert to verify the system is working',
    'test_table',
    'test_record',
    '{"test": true}'
);

-- =============================================
-- Display System Status
-- =============================================

\echo '=== SYSTEM STATUS ==='
SELECT * FROM dashboard.system_status;

\echo '=== DATA SOURCE OVERVIEW ==='
SELECT * FROM dashboard.data_source_overview;

\echo '=== RECENT INGESTION ACTIVITY ==='
SELECT 
    job_name, data_source, status, processed_records, failed_records,
    progress_percent, started_at
FROM dashboard.recent_ingestion_activity 
LIMIT 5;

\echo '=== QUERY PERFORMANCE SUMMARY ==='
SELECT * FROM dashboard.query_performance_summary;

\echo '=== DATA QUALITY METRICS ==='
SELECT * FROM dashboard.data_quality_metrics;

\echo '=== ACTIVE ALERTS ==='
SELECT alert_code, severity, title, created_at 
FROM dashboard.active_alerts 
WHERE resolved = FALSE;

\echo '=== INGESTION STATISTICS ==='
SELECT * FROM ingestion.get_ingestion_statistics();

\echo '=== DEDUPLICATION VALIDATION ==='
SELECT * FROM ingestion.validate_deduplication();

\echo '=== MONITORING QUERY EXECUTION LOG ==='
SELECT 
    query_hash, query_type, duration_ms, status, start_time
FROM monitoring.query_execution_log 
ORDER BY start_time DESC 
LIMIT 5;

\echo '=== SLOW QUERIES ==='
SELECT 
    query_hash, duration_ms, created_at
FROM monitoring.slow_query_log 
ORDER BY duration_ms DESC 
LIMIT 5;

\echo '=== ACTIVE INGESTION JOBS ==='
SELECT 
    id, job_name, data_source, status, processed_records,
    throughput_per_minute, started_at
FROM ingestion.get_active_jobs();

\echo '=== INGESTION ERRORS ==='
SELECT 
    job_id, error_type, error_message, created_at
FROM ingestion.ingestion_errors 
ORDER BY created_at DESC 
LIMIT 5;

-- =============================================
-- Test Monitoring Setup
-- =============================================

\echo '=== SETTING UP MONITORING TRIGGERS ==='
CALL dashboard.setup_ingestion_monitoring();

-- =============================================
-- Performance Tests
-- =============================================

\echo '=== RUNNING PERFORMANCE TESTS ==='

-- Test some queries to populate monitoring data
EXPLAIN ANALYZE SELECT COUNT(*) FROM congress.members;

EXPLAIN ANALYZE SELECT * FROM congress.members LIMIT 10;

EXPLAIN ANALYZE SELECT bioguide_id, first_name, last_name FROM congress.members WHERE gender = 'F';

EXPLAIN ANALYZE SELECT state, COUNT(*) FROM congress.members GROUP BY state;

-- Test ingestion functions with sample data
\echo '=== TESTING INGESTION FUNCTIONS ==='

-- Test Congress member normalization
SELECT ingestion.normalize_congress_member(
    json_build_object(
        'bioguideId', 'T000474',
        'name', 'Tammy Baldwin',
        'firstName', 'Tammy',
        'lastName', 'Baldwin',
        'gender', 'F',
        'birthDate', '1962-02-26'
    )
);

-- Test GovInfo member normalization
SELECT ingestion.normalize_govinfo_member(
    json_build_object(
        'memberId', 'sen_wi_tammy_baldwin',
        'bioguideId', 'B001230',
        'party', 'D',
        'state', 'WI',
        json_build_object(
            'first', 'Tammy',
            'last', 'Baldwin'
        )
    )
);

-- Test OpenStates person normalization
SELECT ingestion.normalize_openstates_person(
    json_build_object(
        'id', 'ocd-person/12345',
        'name', 'John Doe',
        'familyName', 'Doe',
        'givenName', 'John',
        'gender', 'M',
        json_build_object(
            'id', 'ocd-jurisdiction/country:us/state:ca/government'
        )
    )
);

-- =============================================
-- Final System Health Check
-- =============================================

\echo '=== FINAL SYSTEM HEALTH CHECK ==='

-- Check all schemas and tables
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema IN ('congress', 'govinfo', 'openstates', 'ingestion', 'monitoring', 'dashboard')
ORDER BY table_schema, table_name;

-- Check record counts
\echo '=== RECORD COUNTS BY SCHEMA ==='
SELECT 
    schemata.schema_name,
    COALESCE(record_counts.record_count, 0) as record_count
FROM (
    SELECT 'congress' as schema_name UNION
    SELECT 'govinfo' UNION
    SELECT 'openstates' UNION
    SELECT 'ingestion' UNION
    SELECT 'monitoring' UNION
    SELECT 'dashboard'
) schemata
LEFT JOIN (
    SELECT 
        table_schema as schema_name,
        COUNT(*) as record_count
    FROM information_schema.tables
    JOIN (
        SELECT table_schema, table_name, COUNT(*) as cnt
        FROM (
            SELECT 'congress' as table_schema, 'members' as table_name, COUNT(*) as cnt FROM congress.members UNION ALL
            SELECT 'govinfo', 'members', COUNT(*) FROM govinfo.members UNION ALL
            SELECT 'openstates', 'people', COUNT(*) FROM openstates.people UNION ALL
            SELECT 'ingestion', 'ingestion_jobs', COUNT(*) FROM ingestion.ingestion_jobs UNION ALL
            SELECT 'ingestion', 'ingestion_errors', COUNT(*) FROM ingestion.ingestion_errors UNION ALL
            SELECT 'monitoring', 'query_execution_log', COUNT(*) FROM monitoring.query_execution_log UNION ALL
            SELECT 'monitoring', 'slow_query_log', COUNT(*) FROM monitoring.slow_query_log UNION ALL
            SELECT 'dashboard', 'active_alerts', COUNT(*) FROM dashboard.active_alerts
        ) combined
        GROUP BY table_schema, table_name
    ) record_counts ON schemata.schema_name = record_counts.table_schema
) ON schemata.schema_name = record_counts.schema_name
ORDER BY schemata.schema_name;

\echo '=== SYSTEM VERIFICATION COMPLETE ==='
\echo 'All monitoring, ingestion, and tracking systems are operational!'