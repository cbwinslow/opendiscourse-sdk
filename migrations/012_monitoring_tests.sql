-- =============================================
-- Fixed Monitoring Dashboard Functions
-- =============================================

-- Function to create monitoring trigger for a table (fixed)
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
    v_trigger_sql := format('
        CREATE OR REPLACE FUNCTION %I()
        RETURNS TRIGGER AS $func$
        BEGIN
            -- Track the DML operation
            PERFORM dashboard.track_query_execution(
                ''DML on %I.%I: '' || TG_OP,
                NULL,
                CASE WHEN TG_OP = ''DELETE'' THEN 1 ELSE 0 END,
                CASE WHEN TG_OP IN (''INSERT'', ''UPDATE'') THEN 1 ELSE 0 END,
                ''completed''
            );
            
            RETURN COALESCE(NEW, OLD);
        END;
        $func$ LANGUAGE plpgsql;',
        v_trigger_name, p_schema_name, p_table_name);
    
    EXECUTE v_trigger_sql;
    
    -- Create trigger
    EXECUTE format('
        CREATE TRIGGER %I
        AFTER INSERT OR UPDATE OR DELETE ON %I.%I
        FOR EACH ROW EXECUTE FUNCTION %I();',
        v_trigger_name, p_schema_name, p_table_name, v_trigger_name);
    
    RAISE NOTICE 'Created monitoring trigger for %.%', p_schema_name, p_table_name;
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error creating trigger for %.%: %', p_schema_name, p_table_name, SQLERRM;
END;
$$ LANGUAGE plpgsql;

-- Procedure to set up monitoring for all ingestion tables (fixed)
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
EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Error setting up monitoring: %', SQLERRM;
END;
$$;

-- =============================================
-- Test the monitoring system
-- =============================================

-- Test query tracking
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

-- Update test job progress
CALL ingestion.update_ingestion_progress(
    1, -- Assuming job_id is 1
    100,
    0,
    'test_record_001'
);

-- Complete test job
CALL ingestion.complete_ingestion_job(
    1,
    'completed',
    '{"test_completed": true}'
);

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

-- Check for alerts
CALL dashboard.check_for_alerts();

-- =============================================
-- Test dashboard views
-- =============================================

-- View system status
SELECT * FROM dashboard.system_status;

-- View data source overview
SELECT * FROM dashboard.data_source_overview;

-- View recent activity
SELECT * FROM dashboard.recent_ingestion_activity LIMIT 5;

-- View query performance
SELECT * FROM dashboard.query_performance_summary;

-- View data quality
SELECT * FROM dashboard.data_quality_metrics;

-- View active alerts
SELECT * FROM dashboard.active_alerts WHERE resolved = FALSE;

-- =============================================
-- Generate comprehensive dashboard report
-- =============================================

CALL dashboard.generate_health_report();

-- Get full dashboard data
CALL dashboard.get_dashboard_data(
    NULL, NULL, NULL, NULL, NULL
);