"""
Database connectivity and schema validation tests
"""

import pytest
import psycopg2
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# Import test utilities
from .utils.database_utils import get_database_helper, create_test_database_config
from .conftest import generate_test_bills

class TestDatabaseConnectivity:
    """Test database connectivity and basic operations"""

    @pytest.mark.database
    @pytest.mark.integration
    def test_database_connection_basic(self, clean_database):
        """Test basic database connection"""
        cursor = clean_database.cursor()
        cursor.execute("SELECT 1 as test_value;")
        result = cursor.fetchone()
        cursor.close()

        assert result[0] == 1

    @pytest.mark.database
    def test_database_connection_mock(self):
        """Test database connection with mocked connection"""
        with patch('psycopg2.connect') as mock_connect:
            mock_conn = MagicMock()
            mock_connect.return_value = mock_conn

            helper = get_database_helper(use_test_db=False)
            with helper.get_connection() as conn:
                assert conn == mock_conn

    @pytest.mark.database
    @pytest.mark.integration
    def test_cursor_operations(self, clean_database):
        """Test cursor operations"""
        cursor = clean_database.cursor()

        cursor.execute("SELECT 1 as col1, 'test' as col2;")
        assert cursor.description is not None
        assert len(cursor.description) == 2

        result = cursor.fetchone()
        assert result[0] == 1
        assert result[1] == 'test'

        cursor.close()

class TestDatabaseSchema:
    """Test database schema validation"""

    @pytest.mark.database
    @pytest.mark.integration
    def test_required_tables_exist(self, clean_database):
        """Test that all required tables exist"""
        helper = get_database_helper(use_test_db=False)

        required_tables = [
            'congress.bills',
            'congress.members',
            'congress.bill_subjects',
            'congress.chambers',
            'incremental.ingestion_sessions',
            'incremental.processing_checkpoints'
        ]

        for table in required_tables:
            assert helper.table_exists(table), f"Table {table} does not exist"

    @pytest.mark.database
    @pytest.mark.integration
    def test_table_column_structure(self, clean_database):
        """Test table column structure"""
        helper = get_database_helper(use_test_db=False)

        columns = helper.get_column_info('congress.bills')
        column_names = [col['column_name'] for col in columns]

        required_columns = [
            'bill_id', 'congress', 'bill_type', 'bill_number', 'title',
            'sponsor_bioguide_id', 'introduced_date', 'latest_action_text',
            'latest_action_date', 'policy_area', 'subjects', 'url',
            'created_at', 'updated_at'
        ]

        for col in required_columns:
            assert col in column_names, f"Column {col} missing from congress.bills"

class TestDatabaseOperations:
    """Test database CRUD operations"""

    @pytest.mark.database
    @pytest.mark.integration
    def test_bill_insertion(self, clean_database):
        """Test bill data insertion"""
        helper = get_database_helper(use_test_db=False)

        bill_data = {
            'bill_id': 'hr999-118',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '999',
            'title': 'Test Bill for Database Testing',
            'sponsor_bioguide_id': 'T0001',
            'introduced_date': '2024-01-15 00:00:00',
            'latest_action_text': 'Introduced in House',
            'policy_area': 'Government Operations',
            'subjects': ['Tax policy', 'Government spending'],
            'url': 'https://api.congress.gov/bill/hr999-118/'
        }

        success = helper.insert_test_bill(bill_data)
        assert success

        query = "SELECT * FROM congress.bills WHERE bill_id = 'hr999-118';"
        result = helper.execute_query(query)

        assert len(result) == 1
        inserted_bill = result[0]
        assert inserted_bill['title'] == 'Test Bill for Database Testing'
        assert inserted_bill['sponsor_bioguide_id'] == 'T0001'

    @pytest.mark.database
    @pytest.mark.integration
    def test_batch_insertion_performance(self, clean_database, performance_monitor):
        """Test batch insertion performance"""
        helper = get_database_helper(use_test_db=False)

        test_bills = generate_test_bills(100)

        performance_monitor.start()

        inserted_count = 0
        for bill_data in test_bills:
            db_bill = {
                'bill_id': bill_data['billId'],
                'congress': 118,
                'bill_type': bill_data['type'],
                'bill_number': bill_data['number'],
                'title': bill_data['titles'][0]['title'] if bill_data['titles'] else '',
                'sponsor_bioguide_id': bill_data['sponsor']['bioguideId'],
                'introduced_date': bill_data['introducedDate'].replace('Z', ''),
                'policy_area': bill_data['policyArea']['name'] if bill_data.get('policyArea') else '',
                'subjects': [s['name'] for s in bill_data.get('subjects', [])],
                'url': bill_data['url']
            }

            if helper.insert_test_bill(db_bill):
                inserted_count += 1

        performance_monitor.end()

        duration = performance_monitor.get_duration()
        operations_per_sec = performance_monitor.get_operations_per_second(inserted_count)

        assert inserted_count == 100, f"Expected 100 insertions, got {inserted_count}"
        assert duration < 30, f"Batch insertion took {duration:.2f}s, should be under 30s"
        assert operations_per_sec > 3, f"Insertion rate {operations_per_sec:.2f}/s too slow, should be > 3/s"

        print(f"✅ Batch insertion: {inserted_count} bills in {duration:.2f}s ({operations_per_sec:.2f}/s)")

class TestDatabaseErrorHandling:
    """Test database error handling"""

    @pytest.mark.database
    def test_connection_error_handling(self):
        """Test connection error handling"""
        invalid_config = {
            'database': 'nonexistent_db',
            'user': 'invalid_user',
            'password': 'invalid_password',
            'host': 'invalid_host',
            'port': '9999'
        }

        helper = get_database_helper(use_test_db=False)
        helper.connection_params.update(invalid_config)

        with pytest.raises(Exception):
            with helper.get_connection():
                pass
