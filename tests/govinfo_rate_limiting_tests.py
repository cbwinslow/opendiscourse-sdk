#!/usr/bin/env python3
"""
Tests for GovInfo rate limiting and error handling
Validates API call management and error recovery scenarios
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
import time
import requests
from requests.exceptions import HTTPError, ConnectionError, Timeout
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoRateLimiting:
    """Test suite for rate limiting validation"""

    def setup_method(self):
        """Setup test fixtures"""
        self.ingestor = FixedGovInfoIngestor()
        self.ingestor.logger = mock.MagicMock()

    def test_api_request_rate_limiting_handling(self):
        """Test API request handles rate limiting (429 responses)"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=3
        )

        # Mock rate limited response followed by success
        rate_limited_response = mock.MagicMock()
        rate_limited_response.status_code = 429
        rate_limited_response.headers = {'X-RateLimit-Remaining': '0'}
        rate_limited_response.json.side_effect = HTTPError("Rate limited")

        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.headers = {'X-RateLimit-Remaining': '100'}
        success_response.json.return_value = {
            'packages': [{'packageId': 'test-bill-1'}]
        }
        success_response.elapsed.total_seconds.return_value = 1.5

        with patch('requests.get') as mock_get, \
             patch.object(self.ingestor, 'logger') as mock_logger:

            # First call fails with 429, second succeeds
            mock_get.side_effect = [
                requests.exceptions.HTTPError("429 Rate Limited", response=rate_limited_response),
                success_response
            ]

            # Mock adaptive rate limiter
            with patch('scripts.fixed_govinfo_ingestor.adaptive_limiters', {'govinfo.gov': mock.MagicMock()}):
                result = self.ingestor.make_api_request('/test', {})

                # Should have made 2 API calls
                assert mock_get.call_count == 2

                # Verify the successful result
                assert 'packages' in result
                assert len(result['packages']) == 1

    def test_api_request_retries_on_failure(self):
        """Test API request retries on temporary failures"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=3
        )

        # Mock connection error then success
        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {'packages': []}

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                ConnectionError("Connection failed"),
                requests.exceptions.Timeout("Request timeout"),
                success_response
            ]

            result = self.ingestor.make_api_request('/test', {})

            # Should have tried 3 times
            assert mock_get.call_count == 3

    def test_api_request_max_retries_exhausted(self):
        """Test API request fails after max retries exhausted"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=3
        )

        with patch('requests.get') as mock_get:
            mock_get.side_effect = ConnectionError("Persistent connection failure")

            with pytest.raises(Exception, match="All retry attempts failed"):
                self.ingestor.make_api_request('/test', {})

            # Should have tried max_retries + 1 times (including final failure)
            assert mock_get.call_count == 3

    def test_api_request_timeout_handling(self):
        """Test API request handles timeout gracefully"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=2
        )

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Timeout("Request timeout")

            with pytest.raises(Exception, match="All retry attempts failed"):
                self.ingestor.make_api_request('/test', {})

            # Should have retried according to max_retries
            assert mock_get.call_count == 2

    def test_api_request_server_error_handling(self):
        """Test API request handles server errors (5xx responses)"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=3
        )

        server_error_response = mock.MagicMock()
        server_error_response.status_code = 503
        server_error_response.raise_for_status.side_effect = HTTPError("503 Service Unavailable")

        success_response = mock.MagicMock()
        success_response.status_code = 200
        success_response.json.return_value = {'packages': []}

        with patch('requests.get') as mock_get:
            mock_get.side_effect = [
                HTTPError("503 Server Error", response=server_error_response),
                success_response
            ]

            result = self.ingestor.make_api_request('/test', {})

            # Should have retried after server error
            assert mock_get.call_count == 2

    def test_pagination_with_rate_limiting_delays(self):
        """Test pagination respects rate limiting delays"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            request_delay=0.1  # 100ms delay
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': 'bill-1'}]},
            {'packages': [{'packageId': 'bill-2'}]},
            {'packages': []}
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
             patch('time.sleep') as mock_sleep:

            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should have made 3 API calls
            assert mock_fetch.call_count == 3

            # Should have called sleep for rate limiting
            assert mock_sleep.call_count == 2  # Between each batch

            # Verify sleep was called with correct delay
            mock_sleep.assert_called_with(0.1)

    def test_pagination_no_delay_when_disabled(self):
        """Test pagination doesn't delay when rate limiting is disabled"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            request_delay=0  # No delay
        )

        # Mock API responses
        api_responses = [
            {'packages': [{'packageId': 'bill-1'}]},
            {'packages': [{'packageId': 'bill-2'}]},
            {'packages': []}
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
             patch('time.sleep') as mock_sleep:

            mock_fetch.side_effect = api_responses

            batches = list(self.ingestor.paginate_api_response(config, 0))

            # Should have made 3 API calls
            assert mock_fetch.call_count == 3

            # Should not have called sleep
            mock_sleep.assert_not_called()

    def test_api_request_with_api_key(self):
        """Test API request includes API key when available"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        self.ingestor.api_key = "test-api-key-123"

        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {'packages': []}
        response.elapsed.total_seconds.return_value = 1.0

        with patch('requests.get') as mock_get:
            mock_get.return_value = response

            self.ingestor.make_api_request('/test', {'param': 'value'})

            # Verify API key was included in request
            call_kwargs = mock_get.call_args[1]
            assert 'params' in call_kwargs
            assert 'api_key' in call_kwargs['params']
            assert call_kwargs['params']['api_key'] == 'test-api-key-123'

    def test_api_request_metadata_tracking(self):
        """Test API request tracks response metadata"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        response = mock.MagicMock()
        response.status_code = 200
        response.json.return_value = {'packages': []}
        response.url = 'https://api.govinfo.gov/test'
        response.headers = {'Content-Type': 'application/json'}
        response.elapsed.total_seconds.return_value = 2.5

        with patch('requests.get') as mock_get:
            mock_get.return_value = response

            result = self.ingestor.make_api_request('/test', {})

            # Verify metadata was added
            assert '_api_metadata' in result
            metadata = result['_api_metadata']
            assert metadata['url'] == 'https://api.govinfo.gov/test'
            assert metadata['status_code'] == 200
            assert metadata['response_time'] == 2.5
            assert 'Content-Type' in metadata['headers']

    def test_batch_insertion_with_connection_errors(self):
        """Test batch insertion handles database connection errors"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        test_items = [
            {'packageId': 'bill-1', 'dateIssued': '2023-01-01'},
            {'packageId': 'bill-2', 'dateIssued': '2023-01-02'}
        ]

        with patch.object(self.ingestor, 'get_db_connection') as mock_get_conn:
            mock_conn = mock.MagicMock()
            mock_cursor = mock.MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor
            mock_cursor.execute.side_effect = Exception("Database connection lost")

            # Should handle error gracefully
            result = self.ingestor.insert_batch(config, test_items)

            # Should return 0 on error
            assert result == 0

            # Should rollback transaction
            mock_conn.rollback.assert_called_once()

    def test_batch_insertion_rollback_on_error(self):
        """Test batch insertion rolls back on normalization errors"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118
        )

        # Test items that will cause normalization issues
        test_items = [
            {'invalid_data': 'missing_package_id'},  # Missing required field
            {'packageId': '', 'dateIssued': '2023-01-01'},  # Empty package ID
        ]

        with patch.object(self.ingestor, 'get_db_connection') as mock_get_conn:
            mock_conn = mock.MagicMock()
            mock_cursor = mock.MagicMock()
            mock_get_conn.return_value = mock_conn
            mock_conn.cursor.return_value = mock_cursor

            # Should handle error gracefully
            result = self.ingestor.insert_batch(config, test_items)

            # Should return 0 when no valid items
            assert result == 0

    def test_error_recovery_and_continuation(self):
        """Test ingestion continues after recoverable errors"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            max_retries=2,
            request_delay=0
        )

        # Mock API responses with some failures
        api_responses = [
            {'packages': [{'packageId': 'bill-1'}]},  # Success
            Exception("Temporary failure"),            # Error
            {'packages': [{'packageId': 'bill-2'}]},  # Success
            {'packages': []},                          # Empty (end)
        ]

        batch_count = 0
        successful_batches = []

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            try:
                for items_batch in self.ingestor.paginate_api_response(config, 0):
                    batch_count += 1
                    if items_batch:  # Only process non-empty batches
                        successful_batches.append(len(items_batch))
            except Exception:
                # Errors during pagination should be caught by the generator
                pass

            # Should have processed successful batches
            assert len(successful_batches) >= 1

    def test_ingestion_session_error_tracking(self):
        """Test ingestion session tracks errors properly"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            enable_checkpoint=True
        )

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            stats = IngestionStats()
            stats.start_time = datetime.now()
            stats.end_time = datetime.now()
            stats.total_processed = 100
            stats.total_failed = 10

            # Complete session with error
            error_message = "Connection timeout during batch processing"
            self.ingestor.complete_ingestion_session("test-session", "failed", stats, error_message)

            # Verify error was recorded
            cursor.execute.assert_called_once()
            update_call = cursor.execute.call_args[0]
            assert 'UPDATE' in update_call[0]
            assert error_message in str(update_call[1:])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
