"""
Database bootstrap and migration system for Congress CLI.
"""

import os
import psycopg2
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from ..utils.logger import get_logger
from ..utils.config import get_config


class DatabaseBootstrap:
    """Sophisticated database bootstrap and migration system."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database bootstrap."""
        self.config = get_config()
        self.database_url = database_url or self.config.database.get_connection_string()
        self.logger = get_logger(__name__)

        # Migration files directory
        self.migrations_dir = Path(__file__).parent / "migrations"
        self.migrations_dir.mkdir(exist_ok=True)

        # Create migration files if they don't exist
        self._ensure_migration_files()

    def _ensure_migration_files(self):
        """Ensure migration SQL files exist."""
        migrations = {
            "001_create_schemas.sql": self._get_create_schemas_sql(),
            "002_create_congress_tables.sql": self._get_create_congress_tables_sql(),
            "003_create_incremental_tables.sql": self._get_create_incremental_tables_sql(),
            "004_create_indexes.sql": self._get_create_indexes_sql(),
            "005_create_functions.sql": self._get_create_functions_sql(),
            "006_create_triggers.sql": self._get_create_triggers_sql()
        }

        for filename, sql_content in migrations.items():
            migration_file = self.migrations_dir / filename
            if not migration_file.exists():
                with open(migration_file, 'w') as f:
                    f.write(sql_content)
                self.logger.info(f"Created migration file: {filename}")

    def bootstrap_database(self, drop_existing: bool = False) -> bool:
        """Bootstrap database with all tables and schemas."""
        try:
            conn = psycopg2.connect(self.database_url)
            conn.autocommit = True
            cursor = conn.cursor()

            self.logger.info("Starting database bootstrap...")

            if drop_existing:
                self._drop_all_objects(cursor)
                self.logger.info("Dropped existing database objects")

            # Run migrations in order
            migration_files = sorted(self.migrations_dir.glob("*.sql"))

            for migration_file in migration_files:
                self.logger.info(f"Running migration: {migration_file.name}")
                self._run_migration(cursor, migration_file)

            cursor.close()
            conn.close()

            self.logger.info("✅ Database bootstrap completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"❌ Database bootstrap failed: {e}")
            return False

    def _drop_all_objects(self, cursor):
        """Drop all existing database objects."""
        self.logger.info("Dropping existing database objects...")

        # Drop schemas
        cursor.execute("DROP SCHEMA IF EXISTS congress CASCADE;")
        cursor.execute("DROP SCHEMA IF EXISTS incremental CASCADE;")

        # Drop extensions if they exist
        cursor.execute("DROP EXTENSION IF EXISTS pg_stat_statements CASCADE;")
        cursor.execute("DROP EXTENSION IF EXISTS pg_trgm CASCADE;")

    def _run_migration(self, cursor, migration_file: Path):
        """Run a single migration file."""
        with open(migration_file, 'r') as f:
            migration_sql = f.read()

        # Split by semicolons and execute each statement
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        for statement in statements:
            if statement:
                try:
                    cursor.execute(statement)
                except psycopg2.Error as e:
                    # Ignore errors for CREATE IF NOT EXISTS statements
                    if "already exists" not in str(e):
                        self.logger.warning(f"Migration statement warning: {e}")

    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status."""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()

            # Check if schemas exist
            cursor.execute("""
                SELECT schema_name
                FROM information_schema.schemata
                WHERE schema_name IN ('congress', 'incremental')
            """)
            schemas = [row[0] for row in cursor.fetchall()]

            # Check table counts
            table_counts = {}
            for schema in schemas:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                """)
                table_counts[schema] = cursor.fetchone()[0]

            cursor.close()
            conn.close()

            return {
                'schemas': schemas,
                'table_counts': table_counts,
                'migration_files': len(list(self.migrations_dir.glob("*.sql"))),
                'status': 'complete' if 'congress' in schemas and 'incremental' in schemas else 'incomplete'
            }

        except Exception as e:
            self.logger.error(f"Failed to get migration status: {e}")
            return {'status': 'error', 'error': str(e)}

    def _get_create_schemas_sql(self) -> str:
        """SQL for creating schemas."""
        return """
-- Create schemas
CREATE SCHEMA IF NOT EXISTS congress;
CREATE SCHEMA IF NOT EXISTS incremental;

-- Create extensions for enhanced functionality
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Grant permissions
GRANT USAGE ON SCHEMA congress TO PUBLIC;
GRANT USAGE ON SCHEMA incremental TO PUBLIC;
        """.strip()

    def _get_create_congress_tables_sql(self) -> str:
        """SQL for creating Congress tables."""
        return """
-- Congress members table
CREATE TABLE IF NOT EXISTS congress.members (
    bioguide_id VARCHAR(20) PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    state VARCHAR(2) NOT NULL,
    district VARCHAR(10),
    party VARCHAR(50),
    chamber VARCHAR(20) NOT NULL CHECK (chamber IN ('House', 'Senate')),
    term_start DATE NOT NULL,
    term_end DATE,
    url TEXT,
    depiction JSONB,
    data JSONB,
    fingerprint VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Congress bills table
CREATE TABLE IF NOT EXISTS congress.bills (
    bill_id VARCHAR(50) PRIMARY KEY,
    title TEXT NOT NULL,
    congress INTEGER NOT NULL CHECK (congress BETWEEN 93 AND 120),
    bill_type VARCHAR(20) NOT NULL,
    chamber VARCHAR(20) NOT NULL CHECK (chamber IN ('House', 'Senate')),
    introduced_date DATE NOT NULL,
    sponsor_bioguide_id VARCHAR(20),
    cosponsors JSONB,
    committees JSONB,
    actions JSONB,
    text_versions JSONB,
    latest_action JSONB,
    status VARCHAR(100),
    url TEXT,
    data JSONB,
    fingerprint VARCHAR(64) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (sponsor_bioguide_id) REFERENCES congress.members(bioguide_id)
);

-- Bill cosponsors relationship table
CREATE TABLE IF NOT EXISTS congress.bill_cosponsors (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(50) NOT NULL,
    bioguide_id VARCHAR(20) NOT NULL,
    cosponsor_type VARCHAR(20) DEFAULT 'cosponsor',
    sponsored_at DATE,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bill_id) REFERENCES congress.bills(bill_id) ON DELETE CASCADE,
    FOREIGN KEY (bioguide_id) REFERENCES congress.members(bioguide_id),
    UNIQUE(bill_id, bioguide_id)
);

-- Bill committees relationship table
CREATE TABLE IF NOT EXISTS congress.bill_committees (
    id SERIAL PRIMARY KEY,
    bill_id VARCHAR(50) NOT NULL,
    committee_name VARCHAR(255) NOT NULL,
    committee_code VARCHAR(20),
    activity VARCHAR(50),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bill_id) REFERENCES congress.bills(bill_id) ON DELETE CASCADE
);

-- Member terms table (for historical tracking)
CREATE TABLE IF NOT EXISTS congress.member_terms (
    id SERIAL PRIMARY KEY,
    bioguide_id VARCHAR(20) NOT NULL,
    congress INTEGER NOT NULL,
    chamber VARCHAR(20) NOT NULL,
    state VARCHAR(2) NOT NULL,
    district VARCHAR(10),
    party VARCHAR(50),
    term_start DATE NOT NULL,
    term_end DATE,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (bioguide_id) REFERENCES congress.members(bioguide_id) ON DELETE CASCADE
);
        """.strip()

    def _get_create_incremental_tables_sql(self) -> str:
        """SQL for creating incremental tracking tables."""
        return """
-- Ingestion checkpoints table
CREATE TABLE IF NOT EXISTS incremental.ingestion_checkpoints (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    offset VARCHAR(100) NOT NULL DEFAULT '0',
    total_processed INTEGER NOT NULL DEFAULT 0,
    last_ingestion_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'failed', 'paused')),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(data_source, data_type, category)
);

-- Ingestion logs table
CREATE TABLE IF NOT EXISTS incremental.ingestion_logs (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    log_level VARCHAR(10) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    message TEXT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking table
CREATE TABLE IF NOT EXISTS incremental.api_usage (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    success_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    last_request_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rate_limit_hits INTEGER NOT NULL DEFAULT 0,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(data_source, endpoint)
);

-- Data quality metrics table
CREATE TABLE IF NOT EXISTS incremental.data_quality (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    category VARCHAR(50),
    total_records INTEGER NOT NULL DEFAULT 0,
    valid_records INTEGER NOT NULL DEFAULT 0,
    duplicate_records INTEGER NOT NULL DEFAULT 0,
    invalid_records INTEGER NOT NULL DEFAULT 0,
    quality_score DECIMAL(5,2) DEFAULT 0.0,
    last_checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(data_source, data_type, category)
);

-- Performance metrics table
CREATE TABLE IF NOT EXISTS incremental.performance_metrics (
    id SERIAL PRIMARY KEY,
    data_source VARCHAR(50) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    operation VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    duration_ms INTEGER,
    records_processed INTEGER NOT NULL DEFAULT 0,
    records_per_second DECIMAL(10,2),
    memory_usage_mb DECIMAL(10,2),
    cpu_usage_percent DECIMAL(5,2),
    data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
        """.strip()

    def _get_create_indexes_sql(self) -> str:
        """SQL for creating indexes."""
        return """
-- Congress members indexes
CREATE INDEX IF NOT EXISTS idx_members_state ON congress.members(state);
CREATE INDEX IF NOT EXISTS idx_members_chamber ON congress.members(chamber);
CREATE INDEX IF NOT EXISTS idx_members_party ON congress.members(party);
CREATE INDEX IF NOT EXISTS idx_members_term_start ON congress.members(term_start);
CREATE INDEX IF NOT EXISTS idx_members_fingerprint ON congress.members(fingerprint);
CREATE INDEX IF NOT EXISTS idx_members_data_gin ON congress.members USING GIN(data);

-- Congress bills indexes
CREATE INDEX IF NOT EXISTS idx_bills_congress ON congress.bills(congress);
CREATE INDEX IF NOT EXISTS idx_bills_bill_type ON congress.bills(bill_type);
CREATE INDEX IF NOT EXISTS idx_bills_chamber ON congress.bills(chamber);
CREATE INDEX IF NOT EXISTS idx_bills_introduced_date ON congress.bills(introduced_date);
CREATE INDEX IF NOT EXISTS idx_bills_sponsor ON congress.bills(sponsor_bioguide_id);
CREATE INDEX IF NOT EXISTS idx_bills_fingerprint ON congress.bills(fingerprint);
CREATE INDEX IF NOT EXISTS idx_bills_data_gin ON congress.bills USING GIN(data);
CREATE INDEX IF NOT EXISTS idx_bills_title_gin ON congress.bills USING GIN(to_tsvector('english', title));

-- Relationship table indexes
CREATE INDEX IF NOT EXISTS idx_bill_cosponsors_bill ON congress.bill_cosponsors(bill_id);
CREATE INDEX IF NOT EXISTS idx_bill_cosponsors_member ON congress.bill_cosponsors(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_bill_committees_bill ON congress.bill_committees(bill_id);
CREATE INDEX IF NOT EXISTS idx_member_terms_member ON congress.member_terms(bioguide_id);
CREATE INDEX IF NOT EXISTS idx_member_terms_congress ON congress.member_terms(congress);

-- Incremental tables indexes
CREATE INDEX IF NOT EXISTS idx_checkpoints_source_type ON incremental.ingestion_checkpoints(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_checkpoints_status ON incremental.ingestion_checkpoints(status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_updated ON incremental.ingestion_checkpoints(updated_at);
CREATE INDEX IF NOT EXISTS idx_logs_source_type ON incremental.ingestion_logs(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_logs_level ON incremental.ingestion_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_logs_created ON incremental.ingestion_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_source ON incremental.api_usage(data_source);
CREATE INDEX IF NOT EXISTS idx_api_usage_endpoint ON incremental.api_usage(endpoint);
CREATE INDEX IF NOT EXISTS idx_quality_source_type ON incremental.data_quality(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_performance_source_type ON incremental.performance_metrics(data_source, data_type);
CREATE INDEX IF NOT EXISTS idx_performance_operation ON incremental.performance_metrics(operation);
CREATE INDEX IF NOT EXISTS idx_performance_start_time ON incremental.performance_metrics(start_time);
        """.strip()

    def _get_create_functions_sql(self) -> str:
        """SQL for creating utility functions."""
        return """
-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Function to calculate data quality score
CREATE OR REPLACE FUNCTION calculate_quality_score(
    total_records INTEGER,
    valid_records INTEGER,
    duplicate_records INTEGER,
    invalid_records INTEGER
) RETURNS DECIMAL(5,2) AS $$
BEGIN
    IF total_records = 0 THEN
        RETURN 0.0;
    END IF;

    RETURN ROUND(
        (valid_records::DECIMAL / total_records::DECIMAL) * 100.0, 2
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get ingestion progress
CREATE OR REPLACE FUNCTION get_ingestion_progress(
    p_data_source VARCHAR(50),
    p_data_type VARCHAR(50),
    p_category VARCHAR(50) DEFAULT NULL
) RETURNS JSONB AS $$
DECLARE
    result JSONB;
    checkpoint RECORD;
    total_expected INTEGER := 0;
BEGIN
    -- Get checkpoint
    SELECT * INTO checkpoint
    FROM incremental.ingestion_checkpoints
    WHERE data_source = p_data_source
      AND data_type = p_data_type
      AND (category = p_category OR (category IS NULL AND p_category IS NULL));

    IF NOT FOUND THEN
        result := jsonb_build_object(
            'status', 'not_found',
            'message', 'No checkpoint found for the specified criteria'
        );
        RETURN result;
    END IF;

    -- Calculate progress based on data type
    IF p_data_type = 'members' THEN
        -- Expected members per congress (approximately)
        total_expected := 535; -- House (435) + Senate (100)
    ELSIF p_data_type = 'bills' THEN
        -- Expected bills per congress (approximately)
        total_expected := 10000; -- Rough estimate
    END IF;

    result := jsonb_build_object(
        'data_source', checkpoint.data_source,
        'data_type', checkpoint.data_type,
        'category', checkpoint.category,
        'offset', checkpoint.offset,
        'total_processed', checkpoint.total_processed,
        'total_expected', total_expected,
        'completion_percentage', CASE
            WHEN total_expected > 0 THEN
                ROUND((checkpoint.total_processed::DECIMAL / total_expected::DECIMAL) * 100.0, 2)
            ELSE 0
        END,
        'status', checkpoint.status,
        'last_ingestion_at', checkpoint.last_ingestion_at,
        'updated_at', checkpoint.updated_at
    );

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function to clean old logs
CREATE OR REPLACE FUNCTION cleanup_old_logs(days_to_keep INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM incremental.ingestion_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '%s days' % days_to_keep;

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
        """.strip()

    def _get_create_triggers_sql(self) -> str:
        """SQL for creating triggers."""
        return """
-- Triggers for updated_at columns
CREATE TRIGGER update_members_updated_at
    BEFORE UPDATE ON congress.members
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bills_updated_at
    BEFORE UPDATE ON congress.bills
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_checkpoints_updated_at
    BEFORE UPDATE ON incremental.ingestion_checkpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_api_usage_updated_at
    BEFORE UPDATE ON incremental.api_usage
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_data_quality_updated_at
    BEFORE UPDATE ON incremental.data_quality
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to maintain data quality metrics
CREATE OR REPLACE FUNCTION update_data_quality_trigger()
RETURNS TRIGGER AS $$
BEGIN
    -- Update data quality metrics after data changes
    INSERT INTO incremental.data_quality (
        data_source, data_type, category, total_records,
        valid_records, duplicate_records, invalid_records
    ) VALUES (
        'congress', TG_TABLE_NAME, NULL, 1, 1, 0, 0
    )
    ON CONFLICT (data_source, data_type, category)
    DO UPDATE SET
        total_records = data_quality.total_records + 1,
        valid_records = data_quality.valid_records + 1,
        updated_at = CURRENT_TIMESTAMP;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to main tables
CREATE TRIGGER maintain_members_quality
    AFTER INSERT ON congress.members
    FOR EACH ROW EXECUTE FUNCTION update_data_quality_trigger();

CREATE TRIGGER maintain_bills_quality
    AFTER INSERT ON congress.bills
    FOR EACH ROW EXECUTE FUNCTION update_data_quality_trigger();
        """.strip()


class DatabaseManager:
    """Database management utilities."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or get_config().database.get_connection_string()
        self.logger = get_logger(__name__)

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()

            self.logger.info(f"Database connection successful: {version[:50]}...")
            return True
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return False

    def get_database_info(self) -> Dict[str, Any]:
        """Get database information."""
        try:
            conn = psycopg2.connect(self.database_url)
            cursor = conn.cursor()

            # Get database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as size
            """)
            size = cursor.fetchone()[0]

            # Get table counts
            cursor.execute("""
                SELECT table_schema, COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema IN ('congress', 'incremental')
                GROUP BY table_schema
            """)
            table_counts = dict(cursor.fetchall())

            # Get record counts
            record_counts = {}
            for schema in ['congress', 'incremental']:
                cursor.execute(f"""
                    SELECT table_name,
                           (SELECT COUNT(*) FROM {schema}.table_name) as count
                    FROM information_schema.tables
                    WHERE table_schema = '{schema}'
                """)
                record_counts[schema] = dict(cursor.fetchall())

            cursor.close()
            conn.close()

            return {
                'size': size,
                'table_counts': table_counts,
                'record_counts': record_counts,
                'status': 'connected'
            }

        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {'status': 'error', 'error': str(e)}

    def backup_database(self, backup_file: str) -> bool:
        """Create database backup."""
        try:
            import subprocess

            # Parse database URL
            import urllib.parse
            parsed = urllib.parse.urlparse(self.database_url.replace('postgresql://', 'postgres://'))

            cmd = [
                'pg_dump',
                '-h', parsed.hostname,
                '-p', str(parsed.port or 5432),
                '-U', parsed.username,
                '-d', parsed.path[1:],  # Remove leading slash
                '-f', backup_file,
                '--verbose',
                '--no-owner',
                '--no-privileges'
            ]

            # Set password in environment
            env = os.environ.copy()
            env['PGPASSWORD'] = parsed.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                self.logger.info(f"Database backup created: {backup_file}")
                return True
            else:
                self.logger.error(f"Backup failed: {result.stderr}")
                return False

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
