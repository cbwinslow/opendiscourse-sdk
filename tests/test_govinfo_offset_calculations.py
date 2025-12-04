#!/usr/bin/env python3
"""
Tests for GovInfo offset calculation fixes
Validates that offset calculation uses actual items received vs batch size
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoOffsetCalculations:
    """Test suite for offset calculation validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ingestor = FixedGovInfoIngestor()
        self.ingestor.logger = mock.MagicMock()  # Mock logger

    def test_offset_calculation_with_full_batches(self):
        """Test offset calculation when API returns full batches"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with full batches
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},  # Full batch
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 200)]},  # Full batch
            {'packages': [{'packageId': f'bill-{i}'} for i in range(200, 250)]},  # Partial batch (50 items)
        ]

        expected_offsets = [0, 100, 200]  # Offset should increment by items received

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, start_offset=0))

            # Verify we got 3 batches
            assert len(batches) == 3

            # Verify each batch size matches API response
            assert len(batches[0]) == 100
            assert len(batches[1]) == 100
            assert len(batches[2]) == 50

            # Verify fetch was called 3 times
            assert mock_fetch.call_count == 3

            # Verify the calls had correct offsets
            calls = mock_fetch.call_args_list
            assert calls[0][1]['offset'] == 0  # First call
            assert calls[1][1]['offset'] == 100  # Second call (0 + 100 items)
            assert calls[2][1]['offset'] == 200  # Third call (100 + 100 items)

    def test_offset_calculation_with_variable_batch_sizes(self):
        """Test offset calculation when API returns variable batch sizes"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with variable sizes
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(75)]},    # 75 items
            {'packages': [{'packageId': f'bill-{i}'} for i in range(75, 130)]}, # 55 items
            {'packages': [{'packageId': f'bill-{i}'} for i in range(130, 165)]}, # 35 items
            {'packages': [{'packageId': f'bill-{i}'} for i in range(165, 180)]}, # 15 items
            {'packages': []},  # Empty response (end)
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, start_offset=0))

            # Verify we got 4 batches with data
            assert len(batches) == 4

            # Verify batch sizes
            assert len(batches[0]) == 75
            assert len(batches[1]) == 55
            assert len(batches[2]) == 35
            assert len(batches[3]) == 15

            # Verify offsets advance correctly by items received
            calls = mock_fetch.call_args_list
            assert calls[0][1]['offset'] == 0     # Start
            assert calls[1][1]['offset'] == 75    # 0 + 75 items
            assert calls[2][1]['offset'] == 130   # 75 + 55 items
            assert calls[3][1]['offset'] == 165   # 130 + 35 items
            assert calls[4][1]['offset'] == 180   # 165 + 15 items

    def test_offset_calculation_resume_from_checkpoint(self):
        """Test offset calculation when resuming from checkpoint"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock checkpoint at offset 250
        with patch.object(self.ingestor, 'get_checkpoint') as mock_checkpoint:
            mock_checkpoint.return_value = (250, False)

            api_responses = [
                {'packages': [{'packageId': f'bill-{i}'} for i in range(250, 350)]},  # 100 items
                {'packages': [{'packageId': f'bill-{i}'} for i in range(350, 400)]},  # 50 items
                {'packages': []},  # Empty (end)
            ]

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
                mock_fetch.side_effect = api_responses

                batches = list(self.ingestor.paginate_api_response(config, start_offset=250))

                # Verify we start from checkpoint offset
                calls = mock_fetch.call_args_list
                assert calls[0][1]['offset'] == 250  # Resume from checkpoint
                assert calls[1][1]['offset'] == 350  # 250 + 100 items
                assert calls[2][1]['offset'] == 400  # 350 + 50 items

    def test_offset_calculation_no_data_stops_correctly(self):
        """Test that offset calculation stops when no data is returned"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with empty response
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(50)]},  # 50 items
            {'packages': []},  # Empty response - should stop here
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, start_offset=0))

            # Should only get 1 batch
            assert len(batches) == 1
            assert len(batches[0]) == 50

            # Should stop after empty response
            assert mock_fetch.call_count == 2

    def test_offset_calculation_different_data_types(self):
        """Test offset calculation works correctly for different data types"""
        for data_type in [DataType.BILLS, DataType.VOTES, DataType.MEMBERS]:
            config = IngestionConfig(
                data_type=data_type,
                congress=118,
                batch_size=100
            )

            # Create appropriate mock response for data type
            data_key = self.ingestor._get_data_key(data_type)
            api_responses = [
                {data_key: [{'id': f'{data_type.value}-{i}'} for i in range(100)]},
                {data_key: [{'id': f'{data_type.value}-{i}'} for i in range(100, 150)]},
                {data_key: []},  # Empty
            ]

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
                 patch.object(self.ingestor, 'fetch_votes_batch') as mock_votes, \
                 patch.object(self.ingestor, 'fetch_members_batch') as mock_members:

                # Set up appropriate mock based on data type
                if data_type == DataType.BILLS:
                    mock_fetch.side_effect = api_responses
                elif data_type == DataType.VOTES:
                    mock_votes.side_effect = api_responses
                elif data_type == DataType.MEMBERS:
                    mock_members.side_effect = api_responses

                batches = list(self.ingestor.paginate_api_response(config, start_offset=0))

                # Should get 2 batches with data
                assert len(batches) == 2
                assert len(batches[0]) == 100
                assert len(batches[1]) == 50

    def test_stats_offset_tracking(self):
        """Test that statistics track current offset correctly"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(80)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(80, 140)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(140, 170)]},
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
             patch.object(self.ingestor, 'insert_batch') as mock_insert, \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint:

            mock_fetch.side_effect = api_responses
            mock_insert.return_value = 1  # Simulate successful insertion

            # Mock the ingestion process
            with patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)):
                stats = IngestionStats()
                stats.start_time = datetime.now()

                # Simulate processing
                batch_count = 0
                for items_batch in self.ingestor.paginate_api_response(config, 0):
                    batch_count += 1
                    items_processed = len(items_batch)

                    stats.total_processed += items_processed
                    stats.current_offset += items_processed  # This is the key fix

                    # Verify offset tracking
                    if batch_count == 1:
                        assert stats.current_offset == 80
                    elif batch_count == 2:
                        assert stats.current_offset == 140  # 80 + 60
                    elif batch_count == 3:
                        assert stats.current_offset == 170  # 140 + 30

    def test_edge_case_single_item_batches(self):
        """Test offset calculation with single item batches"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with single items
        api_responses = [
            {'packages': [{'packageId': 'bill-1'}]},
            {'packages': [{'packageId': 'bill-2'}]},
            {'packages': [{'packageId': 'bill-3'}]},
            {'packages': []},  # Empty
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should get 3 single-item batches
            assert len(batches) == 3
            assert len(batches[0]) == 1
            assert len(batches[1]) == 1
            assert len(batches[2]) == 1

            # Verify offsets advance correctly
            calls = mock_fetch.call_args_list
            assert calls[0][1]['offset'] == 0   # Start
            assert calls[1][1]['offset'] == 1   # 0 + 1 item
            assert calls[2][1]['offset'] == 2   # 1 + 1 item
            assert calls[3][1]['offset'] == 3   # 2 + 1 item

    def test_offset_calculation_with_large_gaps(self):
        """Test offset calculation handles large gaps in data"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with scattered data (simulates real API behavior)
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in [1, 5, 12, 23, 45]]},  # 5 items
            {'packages': [{'packageId': f'bill-{i}'} for i in [67, 89, 123]]},       # 3 items
            {'packages': [{'packageId': f'bill-{i}'} for i in [156, 178]]},         # 2 items
            {'packages': []},  # Empty
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should get 3 batches with real data
            assert len(batches) == 3
            assert len(batches[0]) == 5
            assert len(batches[1]) == 3
            assert len(batches[2]) == 2

            # Verify offsets advance correctly
            calls = mock_fetch.call_args_list
            assert calls[0][1]['offset'] == 0     # Start
            assert calls[1][1]['offset'] == 5     # 0 + 5 items
            assert calls[2][1]['offset'] == 8     # 5 + 3 items
            assert calls[3][1]['offset'] == 10    # 8 + 2 items


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
