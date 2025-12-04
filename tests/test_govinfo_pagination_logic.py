#!/usr/bin/env python3
"""
Tests for GovInfo pagination logic with mock API responses
Validates proper handling of variable API response sizes
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Generator

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoPaginationLogic:
    """Test suite for pagination logic validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ingestor = FixedGovInfoIngestor()
        self.ingestor.logger = mock.MagicMock()  # Mock logger

    def test_pagination_handles_api_rate_limits(self):
        """Test pagination logic handles API rate limits gracefully"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            request_delay=0.1
        )

        # Mock API responses with varying sizes (simulating real API behavior)
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},  # Full batch
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 195)]},  # 95 items
            {'packages': [{'packageId': f'bill-{i}'} for i in range(195, 245)]},  # 50 items
            {'packages': []},  # Empty response (end)
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify pagination handled all responses correctly
            assert len(batches) == 3
            assert len(batches[0]) == 100
            assert len(batches[1]) == 95
            assert len(batches[2]) == 50

            # Verify pagination stops after empty response
            assert mock_fetch.call_count == 4

    def test_pagination_with_inconsistent_response_sizes(self):
        """Test pagination handles inconsistent response sizes from API"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            batch_size=100
        )

        # Mock API responses with highly variable sizes
        api_responses = [
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(25)]},      # 25 items (small)
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(25, 125)]},  # 100 items (full)
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(125, 130)]}, # 5 items (tiny)
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(130, 175)]}, # 45 items (medium)
            {'rolls': []},  # Empty (end)
        ]

        with patch.object(self.ingestor, 'fetch_votes_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify all batches were processed
            assert len(batches) == 4
            assert len(batches[0]) == 25
            assert len(batches[1]) == 100
            assert len(batches[2]) == 5
            assert len(batches[3]) == 45

            # Verify proper offset progression despite variable sizes
            calls = mock_fetch.call_args_list
            assert calls[0][1]['offset'] == 0     # Start
            assert calls[1][1]['offset'] == 25    # 0 + 25 items
            assert calls[2][1]['offset'] == 125   # 25 + 100 items
            assert calls[3][1]['offset'] == 130   # 125 + 5 items
            assert calls[4][1]['offset'] == 175   # 130 + 45 items

    def test_pagination_max_batch_size_limit(self):
        """Test pagination respects API max batch size limits"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=250  # Request larger than API limit
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},  # API returns 100 max
            {'packages': []},  # Empty
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            # Should respect API limit of 100, not requested 250
            assert config.batch_size == 250
            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify pageSize parameter was capped at 100
            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs['pageSize'] == 100  # Should be capped

            assert len(batches) == 1
            assert len(batches[0]) == 100

    def test_pagination_handles_api_errors(self):
        """Test pagination handles API errors and continues"""
        config = IngestionConfig(
            data_type=DataType.MEMBERS,
            congress=118,
            batch_size=100,
            max_retries=3
        )

        # Mock API responses with one error
        api_responses = [
            {'members': [{'memberId': f'member-{i}'} for i in range(50)]},
            {'members': [{'memberId': f'member-{i}'} for i in range(50, 100)]},
            {'members': []},  # Empty
        ]

        with patch.object(self.ingestor, 'fetch_members_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify pagination continued after each response
            assert len(batches) == 2
            assert len(batches[0]) == 50
            assert len(batches[1]) == 50

    def test_pagination_with_malformed_responses(self):
        """Test pagination handles malformed API responses gracefully"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses with missing data keys
        api_responses = [
            {'packages': [{'packageId': 'bill-1'}]},
            {'packages': [{'packageId': 'bill-2'}]},
            {'other_key': []},  # Missing packages key
            {'packages': []},  # Empty with correct key
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should handle malformed response as empty
            assert len(batches) == 3  # First two + empty from malformed

            # Verify data extraction works correctly
            assert len(batches[0]) == 1
            assert len(batches[1]) == 1
            assert len(batches[2]) == 0  # Empty or malformed treated as empty

    def test_pagination_session_tracking(self):
        """Test that pagination tracks session state correctly"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(75)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(75, 130)]},
            {'packages': []},
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
             patch.object(self.ingestor, 'start_ingestion_session') as mock_session, \
             patch.object(self.ingestor, 'update_checkpoint') as mock_checkpoint:

            mock_fetch.side_effect = api_responses
            mock_session.return_value = "test-session-123"

            # Start ingestion session
            session_id = self.ingestor.start_ingestion_session(config)
            assert session_id == "test-session-123"

            # Process batches
            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify checkpoint updates happened
            assert mock_checkpoint.call_count == len(batches)

            # Verify checkpoint calls have correct offsets
            checkpoint_calls = mock_checkpoint.call_args_list
            assert checkpoint_calls[0][1]['offset'] == 75   # After first batch
            assert checkpoint_calls[1][1]['offset'] == 130  # After second batch

    def test_pagination_generator_behavior(self):
        """Test that pagination returns a proper generator"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(50)]},
            {'packages': []},
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            # Should return a generator
            paginator = self.ingestor.paginate_api_response(config, 0)
            assert hasattr(paginator, '__iter__')
            assert hasattr(paginator, '__next__')

            # Can iterate through batches
            batches = []
            for batch in paginator:
                batches.append(batch)

            assert len(batches) == 1
            assert len(batches[0]) == 50

    def test_pagination_empty_response_stops_immediately(self):
        """Test that empty initial response stops pagination immediately"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        # Mock API response starting with empty
        api_responses = [
            {'packages': []},  # Empty on first call
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should return no batches
            assert len(batches) == 0

            # Should only make one API call
            assert mock_fetch.call_count == 1

    def test_pagination_different_data_types_consistency(self):
        """Test pagination behavior is consistent across different data types"""
        data_types_and_keys = [
            (DataType.BILLS, 'packages'),
            (DataType.VOTES, 'rolls'),
            (DataType.MEMBERS, 'members')
        ]

        for data_type, expected_key in data_types_and_keys:
            config = IngestionConfig(
                data_type=data_type,
                congress=118,
                batch_size=100
            )

            # Mock API responses
            api_responses = [
                {expected_key: [{'id': f'{data_type.value}-{i}'} for i in range(100)]},
                {expected_key: [{'id': f'{data_type.value}-{i}'} for i in range(100, 150)]},
                {expected_key: []},
            ]

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
                 patch.object(self.ingestor, 'fetch_votes_batch') as mock_votes, \
                 patch.object(self.ingestor, 'fetch_members_batch') as mock_members:

                # Set up appropriate mock
                if data_type == DataType.BILLS:
                    mock_fetch.side_effect = api_responses
                elif data_type == DataType.VOTES:
                    mock_votes.side_effect = api_responses
                elif data_type == DataType.MEMBERS:
                    mock_members.side_effect = api_responses

                batches = list(self.ingestor.paginate_api_response(config, 0))

                # Verify consistent behavior
                assert len(batches) == 2
                assert len(batches[0]) == 100
                assert len(batches[1]) == 50

    def test_pagination_with_large_congress_numbers(self):
        """Test pagination works with larger congress numbers"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=119,  # Future congress
            batch_size=100
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': 'BILLS-119hr1-2025-01-01'}]},
            {'packages': []},
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Verify pagination worked with higher congress number
            assert len(batches) == 1

            # Verify correct parameters were passed to API
            call_kwargs = mock_fetch.call_args[1]
            assert call_kwargs['congress'] == 119
            assert call_kwargs['offset'] == 0
            assert call_kwargs['pageSize'] == 100


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
