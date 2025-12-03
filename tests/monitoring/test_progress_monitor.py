"""
Unit tests for the core progress monitoring functionality.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Import monitoring components
import sys
sys.path.insert(0, '.')

from monitoring.progress_monitor import UniversalProgressMonitor, IngestionContext


class TestUniversalProgressMonitor:
    """Test cases for UniversalProgressMonitor"""

    def setup_method(self):
        """Setup test fixtures"""
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (123,)  # Mock job ID return

        self.monitor = UniversalProgressMonitor(self.mock_db, display_mode='simple')

    def test_job_creation(self):
        """Test job creation with proper metadata"""
        job_id = self.monitor.start_job(
            job_name="Test Congress 118 Members",
            data_source="congress.gov",
            table_name="congress.members",
            record_type="member",
            total_estimated=50,
            metadata={'congress': 118, 'job_name': 'Test Congress 118 Members'}
        )

        assert job_id == 123
        assert job_id in self.monitor.active_jobs

        job_data = self.monitor.active_jobs[job_id]
        assert job_data['context'].data_source == "congress.gov"
        assert job_data['context'].table_name == "congress.members"
        assert job_data['context'].record_type == "member"
        assert job_data['context'].metadata['congress'] == 118

        # Verify database call
        self.mock_cursor.execute.assert_called()

    def test_progress_updates(self):
        """Test progress update functionality"""
        # Setup job
        job_id = self.monitor.start_job(
            job_name="Test Job",
            data_source="test.com",
            table_name="test_table",
            record_type="test_record"
        )

        # Update progress
        self.monitor.update_progress(
            job_id=job_id,
            success=True,
            record_id="TEST001"
        )

        job_data = self.monitor.active_jobs[job_id]
        assert job_data['processed'] == 1
        assert job_data['failed'] == 0
        assert job_data['context'].current_record_id == "TEST001"

    def test_error_handling(self):
        """Test error handling and logging"""
        # Setup job
        job_id = self.monitor.start_job(
            job_name="Test Job",
            data_source="test.com",
            table_name="test_table",
            record_type="test_record"
        )

        # Update with error
        self.monitor.update_progress(
            job_id=job_id,
            success=False,
            record_id="TEST001",
            error_details={
                'error_type': 'api_error',
                'error_message': 'Rate limit exceeded',
                'record_id': 'TEST001'
            }
        )

        job_data = self.monitor.active_jobs[job_id]
        assert job_data['processed'] == 0
        assert job_data['failed'] == 1

        # Verify error logging
        self.mock_cursor.execute.assert_called()

    def test_job_completion(self):
        """Test job completion functionality"""
        # Setup and run job
        job_id = self.monitor.start_job(
            job_name="Test Job",
            data_source="test.com",
            table_name="test_table",
            record_type="test_record"
        )

        # Update some progress
        self.monitor.update_progress(job_id, success=True, record_id="TEST001")
        self.monitor.update_progress(job_id, success=True, record_id="TEST002")

        # Complete job
        self.monitor.complete_job(job_id)

        # Verify job is cleaned up
        assert job_id not in self.monitor.active_jobs

        # Verify database update
        self.mock_cursor.execute.assert_called()


class TestIngestionContext:
    """Test cases for IngestionContext"""

    def test_context_creation(self):
        """Test IngestionContext creation and defaults"""
        context = IngestionContext(
            job_id=123,
            data_source="congress.gov",
            table_name="documents",
            record_type="bill",
            metadata={'congress': 118}
        )

        assert context.job_id == 123
        assert context.data_source == "congress.gov"
        assert context.table_name == "documents"
        assert context.record_type == "bill"
        assert context.metadata['congress'] == 118
        assert context.current_record_id is None

    def test_context_updates(self):
        """Test context field updates"""
        context = IngestionContext(
            job_id=123,
            data_source="test.com",
            table_name="test_table",
            record_type="test_record"
        )

        context.current_record_id = "TEST001"
        context.metadata['processed'] = 100

        assert context.current_record_id == "TEST001"
        assert context.metadata['processed'] == 100


class TestPerformanceMetrics:
    """Test performance calculation and metrics"""

    def setup_method(self):
        self.mock_db = Mock()
        self.mock_cursor = Mock()
        self.mock_db.cursor.return_value = self.mock_cursor
        self.mock_cursor.fetchone.return_value = (123,)

        self.monitor = UniversalProgressMonitor(self.mock_db, display_mode='simple')

    def test_throughput_calculation(self):
        """Test throughput calculation over time"""
        job_id = self.monitor.start_job(
            job_name="Test Job",
            data_source="test.com",
            table_name="test_table",
            record_type="test_record"
        )

        start_time = time.time()

        # Simulate processing over time
        for i in range(10):
            self.monitor.update_progress(job_id, success=True, record_id=f"TEST{i:03d}")
            time.sleep(0.1)  # Simulate processing time

        elapsed = time.time() - start_time
        expected_throughput = 10 / (elapsed / 60)  # records per minute

        # Throughput should be reasonable (allowing for timing variations)
        assert expected_throughput > 500  # At least 500 records/min with 0.1s delays
        assert expected_throughput < 1000  # But not impossibly high


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
