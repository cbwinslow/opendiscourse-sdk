"""
End-to-end integration tests for complete ingestion workflow
"""

import pytest
import time
import requests
from unittest.mock import patch, Mock
from typing import Dict, Any, List
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from .conftest import generate_test_bills
from .utils.api_utils import get_api_helper, APIResponseBuilder
from .utils.database_utils import get_database_helper

class TestCompleteIngestionWorkflow:
    """Test complete end-to-end ingestion workflow"""

    @pytest.mark.integration
    @pytest.mark.database
    @pytest.mark.unit
    def test_full_congress_bills_ingestion_workflow(self, clean_database, mock_env_vars):
        """Test complete Congress bills ingestion from API to database"""
        from ingest_congress_bills_incremental import IncrementalCongressBillsIngestor

        # Setup test data
        api_helper = get_api_helper()
        test_bills = generate_test_bills(25)

        # Create mock API response
        page_1_bills = test_bills[:20]
        page_1_response = APIResponseBuilder.congress_bills_response(page_1_bills, limit=20, offset=0)

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = page_1_response
            mock_response.headers = {'X-RateLimit-Remaining': '100'}
            mock_get.return_value = mock_response

            # Run ingestion
            ingestor = IncrementalCongressBillsIngestor()
            with patch.object(ingestor, 'db_conn', clean_database):
                result = ingestor.ingest_congress_bills(118)

                assert result['congress'] == 118
                assert 'records_processed' in result
                assert 'records_skipped' in result

    @pytest.mark.integration
    @pytest.mark.database
    def test_ingestion_with_checkpoint_resumption(self, clean_database):
        """Test ingestion workflow with checkpoint resumption"""
        helper = get_database_helper(use_test_db=False)

        session_id = 'test_resume_session'
        helper.create_test_ingestion_session(
            session_id=session_id,
            data_source='congress.gov',
            data_type='bills',
            status='interrupted'
        )

        cursor = clean_database.cursor()
        cursor.execute("""
            INSERT INTO incremental.processing_checkpoints (
                session_id, data_source, data_type, congress, offset, processed_count, timestamp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (session_id, 'congress.gov', 'bills', 118, 50, 1, time.time()))
        clean_database.commit()
        cursor.close()

        checkpoint = helper.execute_query("""
            SELECT * FROM incremental.processing_checkpoints WHERE session_id = %s
        """, (session_id,))

        assert len(checkpoint) == 1
        assert checkpoint[0]['offset'] == 50
        assert checkpoint[0]['processed_count'] == 1

    @pytest.mark.integration
    @pytest.mark.database
    def test_bill_data_integrity_after_ingestion(self, clean_database):
        """Test data integrity after complete bill ingestion"""
        helper = get_database_helper(use_test_db=False)

        test_bills = [
            {
                'bill_id': 'hr001-118',
                'congress': 118,
                'bill_type': 'HR',
                'bill_number': '001',
                'title': 'Test Bill 1',
                'sponsor_bioguide_id': 'T0001',
                'introduced_date': '2024-01-15 00:00:00',
                'policy_area': 'Government Operations',
                'subjects': ['Tax policy'],
                'url': 'https://api.congress.gov/bill/hr001-118/'
            },
            {
                'bill_id': 'hr002-118',
                'congress': 118,
                'bill_type': 'HR',
                'bill_number': '002',
                'title': 'Test Bill 2',
                'sponsor_bioguide_id': 'T0002',
                'introduced_date': '2024-01-16 00:00:00',
                'policy_area': 'Education',
                'subjects': ['Education funding'],
                'url': 'https://api.congress.gov/bill/hr002-118/'
            }
        ]

        for bill_data in test_bills:
            success = helper.insert_test_bill(bill_data)
            assert success == True

        inserted_bills = helper.execute_query("""
            SELECT * FROM congress.bills ORDER BY bill_id
        """)

        assert len(inserted_bills) == 2

        bill1 = inserted_bills[0]
        assert bill1['bill_id'] == 'hr001-118'
        assert bill1['title'] == 'Test Bill 1'
        assert bill1['sponsor_bioguide_id'] == 'T0001'
        assert 'Tax policy' in str(bill1['subjects'])

        bill2 = inserted_bills[1]
        assert bill2['bill_id'] == 'hr002-118'
        assert bill2['title'] == 'Test Bill 2'
        assert bill2['sponsor_bioguide_id'] == 'T0002'

    @pytest.mark.integration
    @pytest.mark.database
    def test_multi_congress_ingestion(self, clean_database):
        """Test ingestion across multiple congresses"""
        helper = get_database_helper(use_test_db=False)

        congress_data = [
            {'congress': 117, 'bill_id': 'hr001-117', 'title': 'Bill 117'},
            {'congress': 118, 'bill_id': 'hr001-118', 'title': 'Bill 118'},
            {'congress': 119, 'bill_id': 'hr001-119', 'title': 'Bill 119'}
        ]

        for data in congress_data:
            bill_data = {
                'bill_id': data['bill_id'],
                'congress': data['congress'],
                'bill_type': 'HR',
                'bill_number': '001',
                'title': data['title'],
                'sponsor_bioguide_id': 'T0001'
            }
            helper.insert_test_bill(bill_data)

        all_bills = helper.execute_query("""
            SELECT congress, COUNT(*) as count
            FROM congress.bills
            GROUP BY congress
            ORDER BY congress
        """)

        assert len(all_bills) == 3
        assert all_bills[0]['congress'] == 117
        assert all_bills[0]['count'] == 1
        assert all_bills[1]['congress'] == 118
        assert all_bills[1]['count'] == 1
        assert all_bills[2]['congress'] == 119
        assert all_bills[2]['count'] == 1

class TestIngestionPerformance:
    """Test end-to-end ingestion performance"""

    @pytest.mark.performance
    @pytest.mark.integration
    @pytest.mark.database
    def test_large_batch_ingestion_performance(self, clean_database, performance_monitor):
        """Test performance with large batches"""
        helper = get_database_helper(use_test_db=False)

        large_bills = generate_test_bills(100)

        performance_monitor.start()

        inserted_count = 0
        for bill_data in large_bills:
            db_bill = {
                'bill_id': f'perf-large-{bill_data["billId"]}',
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

        print(f"📈 Large batch ingestion performance:")
        print(f"   Bills: {inserted_count}")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Rate: {operations_per_sec:.2f}/s")

        assert inserted_count == 100
        assert duration < 60, f"Large batch took {duration:.2f}s, should be under 60s"
        assert operations_per_sec > 1, f"Rate {operations_per_sec:.2f}/s too slow, should be > 1/s"

class TestIngestionErrorScenarios:
    """Test end-to-end error scenarios and recovery"""

    @pytest.mark.integration
    @pytest.mark.database
    def test_database_constraint_violation_handling(self, clean_database):
        """Test handling of database constraint violations"""
        helper = get_database_helper(use_test_db=False)

        bill1 = {
            'bill_id': 'constraint-test-001',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '001',
            'title': 'First Bill',
            'sponsor_bioguide_id': 'T0001'
        }

        success1 = helper.insert_test_bill(bill1)
        assert success1 == True

        bill2 = {
            'bill_id': 'constraint-test-001',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '001',
            'title': 'Updated Bill Title',
            'sponsor_bioguide_id': 'T0002'
        }

        success2 = helper.insert_test_bill(bill2)
        assert success2 == True

        updated_bill = helper.execute_query("""
            SELECT * FROM congress.bills WHERE bill_id = 'constraint-test-001'
        """)

        assert len(updated_bill) == 1
        assert updated_bill[0]['title'] == 'Updated Bill Title'
        assert updated_bill[0]['sponsor_bioguide_id'] == 'T0002'

    @pytest.mark.integration
    @pytest.mark.database
    def test_session_failure_and_recovery(self, clean_database):
        """Test session failure and recovery mechanism"""
        helper = get_database_helper(use_test_db=False)

        failed_session_id = 'test_failed_session'
        helper.create_test_ingestion_session(
            session_id=failed_session_id,
            data_source='congress.gov',
            data_type='bills',
            status='failed'
        )

        cursor = clean_database.cursor()
        cursor.execute("""
            UPDATE incremental.ingestion_sessions
            SET error_summary = 'API timeout during batch processing'
            WHERE session_id = %s
        """, (failed_session_id,))
        clean_database.commit()
        cursor.close()

        failed_session = helper.execute_query("""
            SELECT * FROM incremental.ingestion_sessions WHERE session_id = %s
        """, (failed_session_id,))

        assert len(failed_session) == 1
        assert failed_session[0]['status'] == 'failed'
        assert 'timeout' in failed_session[0]['error_summary']

        recovery_session_id = f'{failed_session_id}_recovery'
        helper.create_test_ingestion_session(
            session_id=recovery_session_id,
            data_source='congress.gov',
            data_type='bills',
            status='running'
        )

        recovery_session = helper.execute_query("""
            SELECT * FROM incremental.ingestion_sessions WHERE session_id = %s
        """, (recovery_session_id,))

        assert len(recovery_session) == 1
        assert recovery_session[0]['status'] == 'running'

class TestIngestionMonitoring:
    """Test ingestion monitoring and reporting"""

    @pytest.mark.integration
    @pytest.mark.database
    def test_session_monitoring(self, clean_database):
        """Test session monitoring and status tracking"""
        helper = get_database_helper(use_test_db=False)

        sessions = [
            ('monitor_session_1', 'completed'),
            ('monitor_session_2', 'running'),
            ('monitor_session_3', 'failed')
        ]

        for session_id, status in sessions:
            helper.create_test_ingestion_session(
                session_id=session_id,
                data_source='congress.gov',
                data_type='bills',
                status=status
            )

        all_sessions = helper.get_ingestion_sessions()

        monitor_sessions = [
            s for s in all_sessions
            if s['session_id'].startswith('monitor_session_')
        ]

        assert len(monitor_sessions) == 3

        status_counts = {}
        for session in monitor_sessions:
            status = session['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        assert status_counts.get('completed', 0) == 1
        assert status_counts.get('running', 0) == 1
        assert status_counts.get('failed', 0) == 1

class TestIngestionQualityAssurance:
    """Test data quality assurance during ingestion"""

    @pytest.mark.integration
    @pytest.mark.database
    def test_duplicate_detection_during_ingestion(self, clean_database):
        """Test duplicate detection during ingestion process"""
        helper = get_database_helper(use_test_db=False)

        bill1 = {
            'bill_id': 'duplicate-test-001',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '001',
            'title': 'Original Bill',
            'sponsor_bioguide_id': 'T0001'
        }

        success1 = helper.insert_test_bill(bill1)
        assert success1 == True

        bill2 = {
            'bill_id': 'duplicate-test-001',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '001',
            'title': 'Updated Title',
            'sponsor_bioguide_id': 'T0002'
        }

        success2 = helper.insert_test_bill(bill2)
        assert success2 == True

        records = helper.execute_query("""
            SELECT * FROM congress.bills WHERE bill_id = 'duplicate-test-001'
        """)

        assert len(records) == 1
        assert records[0]['title'] == 'Updated Title'
        assert records[0]['sponsor_bioguide_id'] == 'T0002'
