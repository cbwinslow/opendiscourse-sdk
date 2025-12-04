#!/usr/bin/env python3
"""
Tests for GovInfo checkpoint system
Validates resume functionality and data integrity during checkpoint operations
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoCheckpointSystem:
    """Test suite for checkpoint system validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ingestor = FixedGovInfoIngestor()
        self.ingestor.logger = mock.MagicMock()

    def get_mock_db_connection(self):
        """Create mock database connection"""
        conn = mock.MagicMock()
        cursor = mock.MagicMock()
        conn.cursor.return_value = cursor
        cursor.fetchone.return_value = None
        return conn, cursor

    def test_get_checkpoint_new_ingestion(self):
        """Test getting checkpoint for new ingestion (no existing checkpoint)"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            enable_checkpoint=True
        )

        conn, cursor = self.get_mock_db_connection()
        cursor.fetchone.return_value = None

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            offset, is_completed = self.ingestor.get_checkpoint(config)

            assert offset == 0
            assert is_completed == False
            cursor.execute.assert_called_once()

    def test_get_checkpoint_existing_offset(self):
        """Test getting checkpoint with existing offset"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            enable_checkpoint=True
        )

        conn, cursor = self.get_mock_db_connection()
        cursor.fetchone.return_value = (250, False)

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            offset, is_completed = self.ingestor.get_checkpoint(config)

            assert offset == 250
            assert is_completed == False

    def test_get_checkpoint_completed_ingestion(self):
        """Test getting checkpoint for completed ingestion"""
        config = IngestionConfig(
            data_type=DataType.MEMBERS,
            congress=118,
            enable_checkpoint=True
        )

        conn, cursor = self.get_mock_db_connection()
        cursor.fetchone.return_value = (500, True)

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            offset, is_completed = self.ingestor.get_checkpoint(config)

            assert offset == 500
            assert is_completed == True

    def test_get_checkpoint_disabled(self):
        """Test checkpoint when checkpointing is disabled"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            enable_checkpoint=False
        )

        offset, is_completed = self.ingestor.get_checkpoint(config)

        assert offset == 0
        assert is_completed == False

    def test_ingestion_resume_from_checkpoint(self):
        """Test ingestion resumes correctly from checkpoint"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            enable_checkpoint=True,
            resume_from_checkpoint=True
        )

        with patch.object(self.ingestor, 'get_checkpoint', return_value=(150, False)):
            api_responses = [
                {'packages': [{'packageId': f'bill-{i}'} for i in range(150, 250)]},
                {'packages': []}
            ]

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
                 patch.object(self.ingestor, 'insert_batch') as mock_insert:

                mock_fetch.side_effect = api_responses
                mock_insert.return_value = 100

                stats = IngestionStats()
                stats.start_time = datetime.now()

                batch_count = 0
                for items_batch in self.ingestor.paginate_api_response(config, start_offset=150):
                    batch_count += 1
                    stats.total_processed += len(items_batch)
                    stats.current_offset += len(items_batch)

                assert batch_count == 1
                assert stats.total_processed == 100
                assert stats.current_offset == 250

    def test_ingestion_skips_completed_data(self):
        """Test ingestion skips already completed data"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            enable_checkpoint=True,
            resume_from_checkpoint=True
        )

        with patch.object(self.ingestor, 'get_checkpoint', return_value=(1000, True)):
            stats = self.ingestor.ingest_data_type(config)

            assert stats.total_processed == 0
            assert stats.total_inserted == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
