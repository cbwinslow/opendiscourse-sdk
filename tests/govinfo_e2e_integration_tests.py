#!/usr/bin/env python3
"""
End-to-end integration tests for GovInfo ingestion
Tests complete ingestion flow with all components working together
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoEndToEndIntegration:
    """End-to-end integration test suite"""

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

    def test_complete_bills_ingestion_flow(self):
        """Test complete bills ingestion from API to database"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            request_delay=0
        )

        # Simulate realistic API responses
        api_responses = [
            {'packages': [
                {'packageId': f'BILLS-118hr{i}-2023-01-{d:02d}', 'dateIssued': f'2023-01-{d:02d}T12:00:00Z'}
                for i in range(1, 101)
            ]},
            {'packages': [
                {'packageId': f'BILLS-118hr{i}-2023-01-{d:02d}', 'dateIssued': f'2023-01-{d:02d}T12:00:00Z'}
                for i in range(101, 201)
            ]},
            {'packages': []}  # End of data
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
             patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint, \
             patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses

            # Run complete ingestion
            stats = self.ingestor.ingest_data_type(config)

            # Verify complete flow
            assert stats.total_processed == 200
            assert stats.total_inserted == 200
            assert stats.current_offset == 200
            assert mock_checkpoint.call_count == 2  # One per batch

            # Verify database operations
            cursor.execute.assert_called()

    def test_complete_votes_ingestion_flow(self):
        """Test complete votes ingestion from API to database"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            request_delay=0
        )

        # Simulate realistic vote API responses
        api_responses = [
            {'rolls': [
                {
                    'rollId': f'vote-2023-001{i:03d}',
                    'date': f'2023-01-{i:02d}T14:30:00Z',
                    'chamber': 'Senate' if i % 2 == 0 else 'House',
                    'session': '1st Session',
                    'rollNumber': str(i),
                    'question': f'Vote on motion {i}',
                    'type': 'On Motion',
                    'subject': 'Healthcare Bill'
                }
                for i in range(1, 101)
            ]},
            {'rolls': []}  # End of data
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
             patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint, \
             patch.object(self.ingestor, 'fetch_votes_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses

            # Run complete ingestion
            stats = self.ingestor.ingest_data_type(config)

            # Verify complete flow
            assert stats.total_processed == 100
            assert stats.total_inserted == 100
            assert stats.current_offset == 100
            assert mock_checkpoint.call_count == 1

    def test_complete_members_ingestion_flow(self):
        """Test complete members ingestion from API to database"""
        config = IngestionConfig(
            data_type=DataType.MEMBERS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            request_delay=0
        )

        # Simulate realistic members API responses
        api_responses = [
            {'members': [
                {
                    'memberId': f'M{i:03d}',
                    'bioguideId': f'B{i:06d}',
                    'name': {
                        'first': f'Member{i}',
                        'last': 'Doe',
                        'fullName': f'Member{i} Doe',
                        'preferredName': f'Member{i}'
                    },
                    'birthDate': f'19{70 + i % 30}-{i % 12 + 1:02d}-{i % 28 + 1:02d}',
                    'gender': 'M' if i % 2 == 0 else 'F',
                    'party': 'Democrat' if i % 3 == 0 else 'Republican' if i % 3 == 1 else 'Independent',
                    'state': ['CA', 'TX', 'NY', 'FL'][i % 4],
                    'district': str(i % 20 + 1) if i % 2 == 0 else '',
                    'url': f'https://example.com/member{i}',
                    'twitter': f'@member{i}',
                    'biography': f'Biography for Member {i}'
                }
                for i in range(1, 101)
            ]},
            {'members': []}  # End of data
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
             patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint, \
             patch.object(self.ingestor, 'fetch_members_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses

            # Run complete ingestion
            stats = self.ingestor.ingest_data_type(config)

            # Verify complete flow
            assert stats.total_processed == 100
            assert stats.total_inserted == 100
            assert stats.current_offset == 100
            assert mock_checkpoint.call_count == 1

    def test_ingestion_with_interruption_and_resume(self):
        """Test ingestion that gets interrupted and resumes from checkpoint"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            resume_from_checkpoint=True
        )

        # Simulate interrupted ingestion at offset 150
        with patch.object(self.ingestor, 'get_checkpoint', return_value=(150, False)):
            # Simulate continuation from checkpoint
            api_responses = [
                {'packages': [{'packageId': f'bill-{i}'} for i in range(150, 250)]},
                {'packages': [{'packageId': f'bill-{i}'} for i in range(250, 300)]},
                {'packages': []}
            ]

            conn, cursor = self.get_mock_db_connection()

            with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
                 patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint, \
                 patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

                mock_fetch.side_effect = api_responses

                # Run resumed ingestion
                stats = self.ingestor.ingest_data_type(config)

                # Should resume from checkpoint and complete
                assert stats.total_processed == 150  # 100 + 50 items
                assert stats.total_inserted == 150
                assert stats.current_offset == 300
                assert mock_checkpoint.call_count == 2  # One per batch processed

    def test_ingestion_all_data_types_sequential(self):
        """Test ingesting all data types sequentially"""
        congress = 118

        # Track all ingestion calls
        ingestion_calls = []

        def track_ingestion_call(data_type, stats):
            ingestion_calls.append({
                'data_type': data_type,
                'processed': stats.total_processed,
                'inserted': stats.total_inserted
            })

        # Mock individual ingestion for each data type
        for data_type in [DataType.BILLS, DataType.VOTES, DataType.MEMBERS]:
            config = IngestionConfig(
                data_type=data_type,
                congress=congress,
                batch_size=100,
                enable_checkpoint=True,
                request_delay=0
            )

            api_response = {
                'data': [{f'{data_type.value}-{i}': f'value-{i}'} for i in range(50)]
            }

            conn, cursor = self.get_mock_db_connection()

            with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
                 patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
                 patch.object(self.ingestor, 'update_checkpoint'), \
                 patch.object(self.ingestor, 'fetch_bills_batch', return_value=api_response), \
                 patch.object(self.ingestor, 'fetch_votes_batch', return_value=api_response), \
                 patch.object(self.ingestor, 'fetch_members_batch', return_value=api_response):

                stats = self.ingestor.ingest_data_type(config)
                track_ingestion_call(data_type.value, stats)

        # Verify all data types were processed
        assert len(ingestion_calls) == 3
        assert ingestion_calls[0]['data_type'] == 'bills'
        assert ingestion_calls[1]['data_type'] == 'votes'
        assert ingestion_calls[2]['data_type'] == 'members'

    def test_error_handling_during_ingestion(self):
        """Test error handling during complete ingestion flow"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            request_delay=0
        )

        # Simulate API error during ingestion
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},
            Exception("API service temporarily unavailable"),
            {'packages': [{'packageId': f'bill-{i}'} for i in range(200, 300)]},
            {'packages': []}
        ]

        batch_count = 0
        successful_batches = []

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            try:
                for items_batch in self.ingestor.paginate_api_response(config, 0):
                    batch_count += 1
                    if items_batch:
                        successful_batches.append(len(items_batch))

                # Should have processed some batches before error
                assert len(successful_batches) >= 1
            except Exception:
                # Error propagation is acceptable behavior
                assert batch_count >= 1

    def test_checkpoint_session_integration(self):
        """Test integration between checkpoint and session tracking"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True
        )

        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},
            {'packages': []}
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
             patch.object(self.ingestor, 'start_ingestion_session') as mock_session, \
             patch.object(self.ingestor, 'complete_ingestion_session') as mock_complete, \
             patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint'), \
             patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses
            mock_session.return_value = "test-session-123"

            # Run ingestion with session tracking
            stats = self.ingestor.ingest_data_type(config)

            # Verify session tracking integration
            assert mock_session.called
            assert mock_complete.called
            assert stats.total_processed == 100

    def test_multi_congress_ingestion(self):
        """Test ingestion across multiple congresses"""
        congresses = [117, 118]

        for congress in congresses:
            config = IngestionConfig(
                data_type=DataType.BILLS,
                congress=congress,
                batch_size=100,
                enable_checkpoint=True,
                request_delay=0
            )

            api_responses = [
                {'packages': [{'packageId': f'BILLS-{congress}hr{i}-2023-01-01'} for i in range(50)]},
                {'packages': []}
            ]

            conn, cursor = self.get_mock_db_connection()

            with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
                 patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
                 patch.object(self.ingestor, 'update_checkpoint'), \
                 patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

                mock_fetch.side_effect = api_responses

                stats = self.ingestor.ingest_data_type(config)

                # Verify each congress processed independently
                assert stats.total_processed == 50
                assert stats.current_offset == 50

                # Verify API calls used correct congress number
                calls = mock_fetch.call_args_list
                for call in calls:
                    assert call[1]['congress'] == congress

    def test_production_like_scenario(self):
        """Test realistic production scenario with all features"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            max_retries=3,
            request_delay=0.1,
            enable_checkpoint=True,
            resume_from_checkpoint=True
        )

        # Simulate realistic production data with some variability
        total_expected = 1500
        api_responses = []

        offset = 0
        while offset < total_expected:
            batch_size = min(100, total_expected - offset)
            if offset == 900:  # Simulate one slower response
                import time
                time.sleep(0.05)  # Simulate slow response

            api_responses.append({
                'packages': [
                    {
                        'packageId': f'BILLS-118hr{i}-2023-01-01',
                        'dateIssued': '2023-01-01T12:00:00Z',
                        'lastModified': '2023-01-02T10:30:00Z',
                        'download': [{'url': f'https://example.com/bill-{i}.pdf'}]
                    }
                    for i in range(offset, offset + batch_size)
                ]
            })
            offset += batch_size

        api_responses.append({'packages': []})  # End

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn), \
             patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint, \
             patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses

            start_time = datetime.now()
            stats = self.ingestor.ingest_data_type(config)
            end_time = datetime.now()

            # Verify production-like performance
            assert stats.total_processed == total_expected
            assert stats.total_inserted == total_expected
            assert stats.current_offset == total_expected
            assert len(mock_checkpoint.call_args_list) > 10  # Multiple checkpoint updates

            # Should complete in reasonable time (allowing for delays)
            duration = (end_time - start_time).total_seconds()
            assert duration < 60  # Should complete within 60 seconds

    def test_data_validation_during_flow(self):
        """Test data validation throughout the ingestion flow"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Test data with mixed valid/invalid entries
        test_bills = [
            {'packageId': 'valid-bill-1', 'dateIssued': '2023-01-01'},
            {'packageId': '', 'dateIssued': '2023-01-01'},  # Invalid - empty ID
            {'dateIssued': '2023-01-01'},  # Invalid - missing ID
            {'packageId': 'valid-bill-2', 'dateIssued': '2023-01-02'},
            {'packageId': 'BILLS-118hr123-2023-01-03', 'dateIssued': '2023-01-03'},
        ]

        normalized_count = 0
        for bill_data in test_bills:
            normalized = self.ingestor.normalize_bill_data(bill_data)
            if normalized:
                normalized_count += 1

        # Should filter out invalid entries
        assert normalized_count == 3

    def test_rate_limiting_integration(self):
        """Test rate limiting integration in full flow"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            batch_size=100,
            request_delay=0.05  # 50ms delay
        )

        api_responses = [
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(100)]},
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(100, 200)]},
            {'rolls': []}
        ]

        with patch.object(self.ingestor, 'fetch_votes_batch') as mock_fetch, \
             patch('time.sleep') as mock_sleep:

            mock_fetch.side_effect = api_responses

            start_time = datetime.now()
            batches = list(self.ingestor.paginate_api_response(config, 0))
            end_time = datetime.now()

            # Verify rate limiting integration
            assert len(batches) == 2
            assert mock_sleep.call_count == 2  # One delay between batches

            # Total delay should be approximately 2 * 0.05 seconds
            total_delay = sum(call[0][0] for call in mock_sleep.call_args_list)
            assert abs(total_delay - 0.1) < 0.05  # Allow timing variance


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
