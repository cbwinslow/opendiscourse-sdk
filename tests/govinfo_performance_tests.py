#!/usr/bin/env python3
"""
Tests for GovInfo performance and throughput
Validates efficiency and performance characteristics of the ingestion process
"""

import pytest
import unittest.mock as mock
from unittest.mock import MagicMock, patch, call
import sys
import os
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.fixed_govinfo_ingestor import FixedGovInfoIngestor, IngestionConfig, DataType, IngestionStats


class TestGovInfoPerformance:
    """Test suite for performance validation"""

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

    def test_batch_processing_throughput(self):
        """Test batch processing throughput with different batch sizes"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            request_delay=0
        )

        test_items = [{'packageId': f'bill-{i}', 'dateIssued': '2023-01-01'} for i in range(1000)]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            start_time = time.time()

            # Process in batches of 100
            for i in range(0, len(test_items), 100):
                batch = test_items[i:i+100]
                self.ingestor.insert_batch(config, batch)

            end_time = time.time()
            processing_time = end_time - start_time
            throughput = len(test_items) / processing_time

            # Should process efficiently
            assert throughput > 1000  # At least 1000 items/second
            assert processing_time < 5.0  # Should complete within 5 seconds

    def test_pagination_efficiency(self):
        """Test pagination efficiency with large datasets"""
        config = IngestionConfig(
            data_type=DataType.VOTES,
            congress=118,
            batch_size=100,
            request_delay=0
        )

        # Simulate large dataset
        total_items = 5000
        items_per_batch = 100
        expected_batches = total_items // items_per_batch

        # Generate API responses
        api_responses = [
            {'rolls': [{'rollId': f'vote-{i}'} for i in range(i, min(i + items_per_batch, total_items))]}
            for i in range(0, total_items, items_per_batch)
        ]
        api_responses.append({'rolls': []})  # Empty response to end pagination

        with patch.object(self.ingestor, 'fetch_votes_batch') as mock_fetch:
            mock_fetch.side_effect = api_responses

            start_time = time.time()

            total_processed = 0
            for items_batch in self.ingestor.paginate_api_response(config, 0):
                total_processed += len(items_batch)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should process all items efficiently
            assert total_processed == total_items
            assert mock_fetch.call_count == expected_batches + 1  # +1 for empty response
            assert processing_time < 10.0  # Should complete within 10 seconds

    def test_concurrent_processing_performance(self):
        """Test performance with concurrent processing simulation"""
        config = IngestionConfig(
            data_type=DataType.MEMBERS,
            congress=118,
            batch_size=50,
            request_delay=0
        )

        # Simulate processing multiple datasets concurrently
        test_data_sets = [
            [{'memberId': f'M-{dataset}-{i}'} for i in range(200)]
            for dataset in range(3)
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            start_time = time.time()

            results = []
            for data_set in test_data_sets:
                result = self.ingestor.insert_batch(config, data_set)
                results.append(result)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should handle concurrent-like workload efficiently
            assert all(result == 200 for result in results)
            assert processing_time < 3.0  # Should complete within 3 seconds

    def test_memory_efficient_batch_processing(self):
        """Test that batch processing doesn't accumulate memory"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100
        )

        large_dataset = [
            {'packageId': f'bill-{i}', 'dateIssued': '2023-01-01'}
            for i in range(10000)
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            initial_memory = self._get_memory_usage()

            # Process in batches to avoid memory accumulation
            for i in range(0, len(large_dataset), 100):
                batch = large_dataset[i:i+100]
                self.ingestor.insert_batch(config, batch)

                # Force garbage collection
                import gc
                gc.collect()

            final_memory = self._get_memory_usage()
            memory_growth = final_memory - initial_memory

            # Memory growth should be reasonable (less than 50MB)
            assert memory_growth < 50 * 1024 * 1024  # 50MB

    def _get_memory_usage(self):
        """Get current memory usage in bytes"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss

    def test_api_response_time_impact(self):
        """Test impact of API response times on overall performance"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            request_delay=0
        )

        # Simulate different response times
        response_times = [0.1, 0.5, 1.0, 2.0]  # seconds

        for response_time in response_times:
            api_response = {
                'packages': [{'packageId': f'bill-{i}', 'dateIssued': '2023-01-01'} for i in range(100)]
            }

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
                 patch('time.sleep') as mock_sleep:

                mock_fetch.return_value = api_response

                start_time = time.time()
                batches = list(self.ingestor.paginate_api_response(config, 0))
                end_time = time.time()

                total_time = end_time - start_time

                # Should handle slow API responses gracefully
                assert len(batches) == 1
                assert total_time < response_time + 1.0  # Allow some overhead

    def test_large_batch_handling(self):
        """Test handling of large batches efficiently"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=1000  # Large batch
        )

        # Large batch that tests memory and processing limits
        large_batch = [
            {'packageId': f'BILLS-118hr{i}-2023-01-01', 'dateIssued': '2023-01-01'}
            for i in range(1000)
        ]

        conn, cursor = self.get_mock_db_connection()

        with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
            start_time = time.time()

            result = self.ingestor.insert_batch(config, large_batch)

            end_time = time.time()
            processing_time = end_time - start_time

            # Should handle large batches efficiently
            assert result == 1000
            assert processing_time < 5.0  # Should complete within 5 seconds

    def test_checkpoint_performance_impact(self):
        """Test performance impact of checkpoint system"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            enable_checkpoint=True,
            request_delay=0
        )

        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 200)]},
            {'packages': []}
        ]

        with patch.object(self.ingestor, 'get_checkpoint', return_value=(0, False)), \
             patch.object(self.ingestor, 'update_checkpoint') as mock_update, \
             patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:

            mock_fetch.side_effect = api_responses

            start_time = time.time()

            batches = list(self.ingestor.paginate_api_response(config, 0))

            end_time = time.time()
            processing_time = end_time - start_time

            # Checkpoint operations shouldn't significantly impact performance
            assert len(batches) == 2
            assert mock_update.call_count == 2  # One per batch
            assert processing_time < 2.0  # Should complete within 2 seconds

    def test_rate_limiting_performance_trade_off(self):
        """Test performance trade-off with rate limiting"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            request_delay=0.1  # 100ms delay
        )

        api_responses = [
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100)]},
            {'packages': [{'packageId': f'bill-{i}'} for i in range(100, 200)]},
            {'packages': []}
        ]

        with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch, \
             patch('time.sleep') as mock_sleep:

            mock_fetch.side_effect = api_responses

            start_time = time.time()

            batches = list(self.ingestor.paginate_api_response(config, 0))

            end_time = time.time()
            processing_time = end_time - start_time

            # Rate limiting should add predictable delay
            assert len(batches) == 2
            assert mock_sleep.call_count == 2  # One delay per batch transition

            # Total delay should be approximately 2 * 0.1 seconds
            total_delay = sum(call[0][0] for call in mock_sleep.call_args_list)
            assert abs(total_delay - 0.2) < 0.01  # Allow small timing variance

    def test_error_recovery_performance(self):
        """Test performance impact of error recovery"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            max_retries=2,
            request_delay=0
        )

        # Simulate occasional errors during processing
        error_count = 0

        def fetch_with_errors(congress, offset, page_size):
            nonlocal error_count
            error_count += 1

            if error_count % 3 == 0:  # Every 3rd call fails
                raise Exception("Temporary API error")

            return {
                'packages': [{'packageId': f'bill-{offset + i}'} for i in range(page_size)]
            }

        with patch.object(self.ingestor, 'fetch_bills_batch', side_effect=fetch_with_errors):
            start_time = time.time()

            error_recoveries = 0
            try:
                batches_processed = 0
                for items_batch in self.ingestor.paginate_api_response(config, 0):
                    batches_processed += 1
                    if batches_processed > 10:  # Limit for testing
                        break
            except Exception:
                error_recoveries += 1

            end_time = time.time()
            processing_time = end_time - start_time

            # Should recover from errors without significant performance impact
            assert processing_time < 10.0  # Should complete within 10 seconds

    def test_performance_with_realistic_data_sizes(self):
        """Test performance with realistic congress data sizes"""
        # Simulate realistic bill volumes for a congress
        realistic_scenarios = [
            (117, 15000),  # congress, expected bills
            (118, 8000),   # congress, expected bills
            (119, 2000),   # congress, expected bills (partial)
        ]

        for congress, expected_bills in realistic_scenarios:
            config = IngestionConfig(
                data_type=DataType.BILLS,
                congress=congress,
                batch_size=100,
                request_delay=0
            )

            # Simulate processing realistic dataset
            api_responses = [
                {'packages': [{'packageId': f'BILLS-{congress}hr{i}-2023-01-01'} for i in range(100)]}
                for _ in range(expected_bills // 100)
            ]
            api_responses.append({'packages': []})

            with patch.object(self.ingestor, 'fetch_bills_batch') as mock_fetch:
                mock_fetch.side_effect = api_responses

                start_time = time.time()

                total_processed = 0
                for items_batch in self.ingestor.paginate_api_response(config, 0):
                    total_processed += len(items_batch)

                end_time = time.time()
                processing_time = end_time - start_time
                throughput = total_processed / processing_time

                # Should handle realistic volumes efficiently
                assert total_processed >= expected_bills - 100  # Allow for final partial batch
                assert throughput > 500  # At least 500 items/second

    def test_throughput_benchmark(self):
        """Benchmark throughput against performance requirements"""
        config = IngestionConfig(
            data_type=DataType.BILLS,
            congress=118,
            batch_size=100,
            request_delay=0
        )

        benchmark_results = []

        # Run multiple iterations for statistical significance
        for iteration in range(5):
            test_items = [
                {'packageId': f'bench-bill-{iteration}-{i}', 'dateIssued': '2023-01-01'}
                for i in range(1000)
            ]

            conn, cursor = self.get_mock_db_connection()

            with patch.object(self.ingestor, 'get_db_connection', return_value=conn):
                start_time = time.time()

                self.ingestor.insert_batch(config, test_items)

                end_time = time.time()
                throughput = len(test_items) / (end_time - start_time)
                benchmark_results.append(throughput)

        # Calculate performance statistics
        mean_throughput = statistics.mean(benchmark_results)
        min_throughput = min(benchmark_results)
        max_throughput = max(benchmark_results)
        std_dev = statistics.stdev(benchmark_results) if len(benchmark_results) > 1 else 0

        # Performance requirements
        assert mean_throughput > 2000  # Average > 2000 items/second
        assert min_throughput > 1000   # Minimum > 1000 items/second
        assert std_dev < 500          # Low variability

        print(f"Throughput benchmark: {mean_throughput:.1f} ± {std_dev:.1f} items/sec")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
