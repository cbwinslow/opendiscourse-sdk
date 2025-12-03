"""
Database utilities for testing
"""

import psycopg2
import psycopg2.extras
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from datetime import datetime

class DatabaseTestHelper:
    """Helper class for database testing operations"""

    def __init__(self, connection_params: Dict[str, Any]):
        """Initialize with database connection parameters"""
        self.connection_params = connection_params.copy()
        self.connection_params['database'] = connection_params.get('database', 'opendiscourse')

    @contextmanager
    def get_connection(self, autocommit: bool = False):
        """Get database connection with automatic cleanup"""
        conn = None
        try:
            conn = psycopg2.connect(**self.connection_params)
            conn.autocommit = autocommit
            yield conn
        finally:
            if conn:
                conn.close()

    @contextmanager
    def get_cursor(self, autocommit: bool = False):
        """Get database cursor with automatic cleanup"""
        with self.get_connection(autocommit=autocommit) as conn:
            cursor = conn.cursor()
            try:
                yield cursor, conn
            finally:
                cursor.close()

    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries"""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            return []

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute update/insert/delete and return affected row count"""
        with self.get_cursor() as (cursor, conn):
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = %s
            )
        """
        result = self.execute_query(query, (table_name,))
        return result[0]['exists'] if result else False

    def get_table_count(self, table_name: str) -> int:
        """Get count of rows in table"""
        try:
            result = self.execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
            return result[0]['count'] if result else 0
        except Exception:
            return 0

    def get_column_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for table"""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position
        """
        return self.execute_query(query, (table_name,))

    def check_foreign_key_constraints(self, table_name: str) -> List[Dict[str, Any]]:
        """Check foreign key constraints for table"""
        query = """
            SELECT
                tc.constraint_name,
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM
                information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = %s
        """
        return self.execute_query(query, (table_name,))

    def insert_test_bill(self, bill_data: Dict[str, Any]) -> bool:
        """Insert test bill data"""
        query = """
            INSERT INTO congress.bills (
                bill_id, congress, bill_type, bill_number, title,
                sponsor_bioguide_id, introduced_date, latest_action_text,
                latest_action_date, policy_area, subjects, url,
                created_at, updated_at
            ) VALUES (
                %(bill_id)s, %(congress)s, %(bill_type)s, %(bill_number)s, %(title)s,
                %(sponsor_bioguide_id)s, %(introduced_date)s, %(latest_action_text)s,
                %(latest_action_date)s, %(policy_area)s, %(subjects)s, %(url)s,
                %(created_at)s, %(updated_at)s
            )
            ON CONFLICT (bill_id) DO UPDATE SET
                title = EXCLUDED.title,
                sponsor_bioguide_id = EXCLUDED.sponsor_bioguide_id,
                introduced_date = EXCLUDED.introduced_date,
                latest_action_text = EXCLUDED.latest_action_text,
                latest_action_date = EXCLUDED.latest_action_date,
                policy_area = EXCLUDED.policy_area,
                subjects = EXCLUDED.subjects,
                url = EXCLUDED.url,
                updated_at = EXCLUDED.updated_at
        """
        try:
            # Add timestamp fields if not present
            if 'created_at' not in bill_data:
                bill_data['created_at'] = datetime.now()
            if 'updated_at' not in bill_data:
                bill_data['updated_at'] = datetime.now()

            self.execute_update(query, bill_data)
            return True
        except Exception as e:
            print(f"Error inserting test bill: {e}")
            return False

    def create_test_ingestion_session(self, session_id: str, data_source: str = 'congress.gov',
                                    data_type: str = 'bills', status: str = 'running') -> bool:
        """Create test ingestion session"""
        query = """
            INSERT INTO incremental.ingestion_sessions (
                session_id, data_source, data_type, status, started_at
            ) VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (session_id) DO UPDATE SET
                status = EXCLUDED.status,
                started_at = EXCLUDED.started_at
        """
        try:
            self.execute_update(query, (session_id, data_source, data_type, status, datetime.now()))
            return True
        except Exception as e:
            print(f"Error creating test session: {e}")
            return False

    def get_ingestion_sessions(self) -> List[Dict[str, Any]]:
        """Get all ingestion sessions"""
        query = """
            SELECT session_id, data_source, data_type, status, started_at,
                   completed_at, error_summary
            FROM incremental.ingestion_sessions
            ORDER BY started_at DESC
        """
        return self.execute_query(query)

    def cleanup_test_data(self):
        """Clean up test data from database"""
        # Order matters due to foreign key constraints
        tables = [
            'congress.bill_subjects',
            'congress.bills',
            'congress.members',
            'incremental.ingestion_sessions'
        ]

        for table in tables:
            try:
                self.execute_update(f"DELETE FROM {table};")
                print(f"Cleaned table: {table}")
            except Exception as e:
                print(f"Warning: Could not clean {table}: {e}")

    def reset_sequences(self):
        """Reset auto-increment sequences"""
        sequences = ['congress.bills_bill_id_seq', 'congress.members_member_id_seq']
        for seq in sequences:
            try:
                self.execute_update(f"SELECT setval('{seq}', 1, false);")
            except Exception:
                pass  # Sequence might not exist

    def verify_database_schema(self) -> Dict[str, Any]:
        """Verify database schema is correct"""
        schema_status = {
            'congress_tables': [],
            'openstates_tables': [],
            'incremental_tables': [],
            'missing_tables': [],
            'constraint_issues': []
        }

        # Check required tables
        required_tables = [
            'congress.bills',
            'congress.members',
            'congress.bill_subjects',
            'congress.chambers',
            'openstates.people',
            'openstates.jurisdictions',
            'incremental.ingestion_sessions',
            'incremental.processing_checkpoints'
        ]

        for table in required_tables:
            if self.table_exists(table):
                schema_status[f'{table.split(".")[0]}_tables'].append(table)
            else:
                schema_status['missing_tables'].append(table)

        # Check constraints for key tables
        constraint_tables = ['congress.bills', 'congress.members']
        for table in constraint_tables:
            try:
                constraints = self.check_foreign_key_constraints(table)
                if not constraints:
                    schema_status['constraint_issues'].append(f"No foreign keys for {table}")
            except Exception as e:
                schema_status['constraint_issues'].append(f"Error checking {table}: {e}")

        return schema_status

def create_test_database_config() -> Dict[str, Any]:
    """Create test database configuration"""
    return {
        'database': 'opendiscourse_test',
        'user': 'test_user',
        'password': 'test_password',
        'host': 'localhost',
        'port': '5432'
    }

def create_production_database_config() -> Dict[str, Any]:
    """Create production database configuration for testing"""
    return {
        'database': 'opendiscourse',
        'user': 'cbwinslow',
        'password': '',
        'host': '/var/run/postgresql',
        'port': '5432'
    }

def get_database_helper(use_test_db: bool = True) -> DatabaseTestHelper:
    """Get database helper instance"""
    if use_test_db:
        config = create_test_database_config()
    else:
        config = create_production_database_config()

    return DatabaseTestHelper(config)
