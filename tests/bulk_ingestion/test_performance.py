"""
Performance and benchmarking tests
"""

import pytest
import time
import psutil
import statistics
from unittest.mock import patch, Mock
from typing import Dict, Any, List
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from rate_limiter import adaptive_limiters
from .conftest import generate_test_bills

class TestDatabasePerformance:
    """Test database performance and optimization"""

    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.integration
    def test_bulk_insertion_performance(self, clean_database, performance_monitor):
        """Test bulk database insertion performance"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        # Generate test data
        test_bills = generate_test_bills(1000)

        # Measure insertion performance
        performance_monitor.start()

        inserted_count = 0
        batch_size = 100

        for i in range(0, len(test_bills), batch_size):
            batch = test_bills[i:i + batch_size]

            for bill_data in batch:
                # Convert to database format
                db_bill = {
                    'bill_id': f'perf-test-{bill_data["billId"]}',
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

        # Calculate performance metrics
        duration = performance_monitor.get_duration()
        memory_delta = performance_monitor.get_memory_delta()
        operations_per_sec = performance_monitor.get_operations_per_second(inserted_count)

        # Performance assertions
        assert inserted_count == 1000, f"Expected 1000 insertions, got {inserted_count}"
        assert duration < 300, f"Insertion took {duration:.2f}s, should be under 300s"
        assert operations_per_sec > 3, f"Rate {operations_per_sec:.2f}/s too slow, should be > 3/s"
        assert memory_delta < 500 * 1024 * 1024, f"Memory usage {memory_delta / 1024 / 1024:.2f}MB too high"

        print(f"📊 Bulk insertion performance:")
        print(f"   Duration: {duration:.2f}s")
        print(f"   Records: {inserted_count}")
        print(f"   Rate: {operations_per_sec:.2f}/s")
        print(f"   Memory: {memory_delta / 1024 / 1024:.2f}MB")

    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.integration
    def test_batch_query_performance(self, clean_database):
        """Test batch query performance"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        # Insert test data
        for i in range(100):
            bill_data = {
                'bill_id': f'query-test-{i}',
                'congress': 118,
                'bill_type': 'HR',
                'bill_number': str(i),
                'title': f'Query Test Bill {i}',
                'sponsor_bioguide_id': 'T0001'
            }
            helper.insert_test_bill(bill_data)

        # Test query performance
        queries = [
            "SELECT * FROM congress.bills WHERE bill_id LIKE 'query-test-%'",
            "SELECT COUNT(*) FROM congress.bills WHERE congress = 118",
            "SELECT bill_id, title FROM congress.bills WHERE bill_type = 'HR' LIMIT 50",
            "SELECT * FROM congress.bills ORDER BY created_at DESC LIMIT 10"
        ]

        query_times = []

        for query in queries:
            start_time = time.time()
            result = helper.execute_query(query)
            end_time = time.time()

            query_time = end_time - start_time
            query_times.append(query_time)

            print(f"Query: {query[:50]}...")
            print(f"Time: {query_time:.3f}s, Rows: {len(result)}")

        # Performance assertions
        avg_query_time = statistics.mean(query_times)
        assert avg_query_time < 1.0, f"Average query time {avg_query_time:.3f}s too slow"

        print(f"📈 Average query time: {avg_query_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.integration
    def test_connection_pool_performance(self, clean_database):
        """Test database connection pool performance"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        # Test multiple concurrent connections
        num_connections = 10
        operations_per_connection = 5

        start_time = time.time()
        connection_times = []

        for conn_id in range(num_connections):
            conn_start = time.time()

            with helper.get_connection() as conn:
                cursor = conn.cursor()

                for op in range(operations_per_connection):
                    cursor.execute("SELECT 1;")
                    cursor.fetchone()

                cursor.close()

            conn_end = time.time()
            connection_times.append(conn_end - conn_start)

        total_time = time.time() - start_time

        # Performance assertions
        avg_connection_time = statistics.mean(connection_times)
        assert avg_connection_time < 0.1, f"Connection time {avg_connection_time:.3f}s too slow"
        assert total_time < 5.0, f"Total time {total_time:.3f}s too slow"

        print(f"🔗 Connection performance:")
        print(f"   Connections: {num_connections}")
        print(f"   Avg connection time: {avg_connection_time:.3f}s")
        print(f"   Total time: {total_time:.3f}s")

class TestAPIPerformance:
    """Test API performance and rate limiting effectiveness"""

    @pytest.mark.performance
    @pytest.mark.network
    @pytest.mark.integration
    def test_api_rate_limiting_effectiveness(self, performance_monitor):
        """Test that rate limiting effectively controls API usage"""
        limiter = adaptive_limiters['congress.gov']

        # Record initial state
        initial_rate = limiter.current_rate

        # Measure rate limiting effectiveness
        performance_monitor.start()

        request_times = []
        successful_requests = 0

        for i in range(20):
            request_start = time.time()

            # Use rate limiter
            limiter.wait_for_token(1)

            # Simulate API request (with mock)
            time.sleep(0.01)  # Simulate network latency

            request_end = time.time()
            request_times.append(request_end - request_start)
            successful_requests += 1

        performance_monitor.end()

        # Calculate metrics
        total_duration = performance_monitor.get_duration()
        average_request_time = statistics.mean(request_times)
        requests_per_second = successful_requests / total_duration

        # Performance assertions
        assert successful_requests == 20, f"Expected 20 requests, got {successful_requests}"
        assert average_request_time > 0.01, "Rate limiting should add some delay"
        assert requests_per_second <= initial_rate * 1.1, f"Rate {requests_per_second:.2f}/s exceeds limit {initial_rate}/s"

        print(f"🌐 API rate limiting performance:")
        print(f"   Rate limit: {initial_rate}/s")
        print(f"   Actual rate: {requests_per_second:.2f}/s")
        print(f"   Avg request time: {average_request_time:.3f}s")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_adaptive_rate_limiter_performance(self):
        """Test adaptive rate limiter performance"""
        limiter = adaptive_limiters['congress.gov']

        # Measure rate limiter operations
        start_time = time.time()

        # Simulate many rate limit operations
        for i in range(1000):
            limiter.consume(1)
            if i % 100 == 0:
                limiter.update_from_response({'X-RateLimit-Remaining': '50'})
                limiter.handle_error(200)

        end_time = time.time()
        duration = end_time - start_time

        # Performance assertion
        assert duration < 0.1, f"Rate limiter too slow: {duration:.3f}s for 1000 operations"

        print(f"⚡ Rate limiter performance: 1000 ops in {duration:.3f}s ({1000/duration:.0f} ops/s)")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_batch_api_calls_performance(self, mock_requests):
        """Test performance of batch API calls"""
        with patch('requests.get') as mock_get:
            # Configure mock response
            mock_response = mock_requests['response']
            mock_response.status_code = 200
            mock_response.json.return_value = {'bills': generate_test_bills(50)}
            mock_get.return_value = mock_response

            # Measure batch performance
            start_time = time.time()
            successful_calls = 0

            for i in range(10):  # 10 batch calls
                response = requests.get(f"https://api.congress.gov/v3/bill?limit=50&offset={i*50}")
                if response.status_code == 200:
                    data = response.json()
                    successful_calls += 1

            end_time = time.time()
            duration = end_time - start_time

            # Performance assertion
            assert successful_calls == 10, f"Expected 10 successful calls, got {successful_calls}"
            assert duration < 1.0, f"Batch calls too slow: {duration:.3f}s"

            print(f"📦 Batch API performance: 10 calls in {duration:.3f}s ({10/duration:.1f} calls/s)")

class TestMemoryPerformance:
    """Test memory usage and optimization"""

    @pytest.mark.performance
    @pytest.mark.unit
    def test_memory_usage_tracking(self):
        """Test memory usage tracking accuracy"""
        process = psutil.Process()

        # Record baseline memory
        baseline_memory = process.memory_info().rss

        # Allocate test data
        test_data = []
        for i in range(1000):
            test_data.append({'id': i, 'data': 'x' * 1000})

        # Check memory increase
        after_allocation = process.memory_info().rss
        memory_increase = after_allocation - baseline_memory

        # Clean up
        test_data.clear()

        final_memory = process.memory_info().rss

        # Assertions
        assert memory_increase > 0, "Memory should increase with data allocation"
        assert final_memory < after_allocation, "Memory should decrease after cleanup"

        print(f"🧠 Memory tracking:")
        print(f"   Baseline: {baseline_memory / 1024 / 1024:.2f}MB")
        print(f"   Peak: {after_allocation / 1024 / 1024:.2f}MB")
        print(f"   Increase: {memory_increase / 1024 / 1024:.2f}MB")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_data_processing_memory_efficiency(self):
        """Test memory efficiency of data processing"""
        def process_data_stream(data_size: int) -> int:
            """Process data stream with minimal memory usage"""
            processed_count = 0

            # Process in chunks
            chunk_size = 100
            for i in range(0, data_size, chunk_size):
                chunk = list(range(i, min(i + chunk_size, data_size)))

                # Process chunk
                processed_chunk = [item * 2 for item in chunk]
                processed_count += len(processed_chunk)

                # Allow garbage collection
                if i % 1000 == 0:
                    import gc
                    gc.collect()

            return processed_count

        process = psutil.Process()
        baseline_memory = process.memory_info().rss

        # Process large dataset
        processed = process_data_stream(10000)

        peak_memory = process.memory_info().rss
        memory_increase = peak_memory - baseline_memory

        # Memory usage assertions
        expected_memory_increase = 10000 * 8 / 1024 / 1024  # Rough estimate in MB
        assert memory_increase < expected_memory_increase * 2, "Memory usage too high"

        print(f"💾 Data processing memory efficiency:")
        print(f"   Processed: {processed} items")
        print(f"   Memory increase: {memory_increase / 1024 / 1024:.2f}MB")

class TestBatchProcessingPerformance:
    """Test batch processing optimization"""

    @pytest.mark.performance
    @pytest.mark.unit
    def test_optimal_batch_size_determination(self):
        """Test determination of optimal batch size"""
        def simulate_batch_processing(data_size: int, batch_sizes: List[int]) -> Dict[int, float]:
            """Simulate batch processing with different batch sizes"""
            results = {}

            for batch_size in batch_sizes:
                start_time = time.time()

                processed = 0
                for i in range(0, data_size, batch_size):
                    batch = list(range(i, min(i + batch_size, data_size)))
                    # Simulate batch processing
                    time.sleep(0.001 * len(batch))  # Simulate processing time
                    processed += len(batch)

                duration = time.time() - start_time
                results[batch_size] = duration

            return results

        data_size = 1000
        batch_sizes = [10, 50, 100, 200, 500]

        results = simulate_batch_processing(data_size, batch_sizes)

        # Find optimal batch size
        optimal_batch_size = min(results.keys(), key=lambda x: results[x])

        print(f"📊 Batch size performance:")
        for batch_size, duration in results.items():
            print(f"   Batch {batch_size}: {duration:.3f}s")
        print(f"   Optimal batch size: {optimal_batch_size}")

        # Assertions
        assert optimal_batch_size in [50, 100, 200], f"Unexpected optimal batch size: {optimal_batch_size}"

    @pytest.mark.performance
    @pytest.mark.unit
    def test_concurrent_processing_performance(self):
        """Test concurrent processing performance"""
        import threading
        from concurrent.futures import ThreadPoolExecutor

        def process_item(item_id: int) -> Dict[str, Any]:
            """Simulate processing an item"""
            # Simulate work
            time.sleep(0.01)

            return {
                'item_id': item_id,
                'processed_at': time.time(),
                'thread_id': threading.current_thread().ident
            }

        items = list(range(100))

        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for item in items:
            result = process_item(item)
            sequential_results.append(result)
        sequential_time = time.time() - start_time

        # Concurrent processing
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=4) as executor:
            concurrent_results = list(executor.map(process_item, items))
        concurrent_time = time.time() - start_time

        # Performance comparison
        speedup = sequential_time / concurrent_time

        print(f"🚀 Concurrent processing performance:")
        print(f"   Sequential: {sequential_time:.3f}s")
        print(f"   Concurrent: {concurrent_time:.3f}s")
        print(f"   Speedup: {speedup:.2f}x")

        # Assertions
        assert len(concurrent_results) == 100
        assert speedup > 1.5, f"Expected speedup > 1.5x, got {speedup:.2f}x"

class TestPerformanceBenchmarks:
    """Test performance against established benchmarks"""

    @pytest.mark.performance
    @pytest.mark.database
    @pytest.mark.integration
    def test_database_insertion_benchmark(self, clean_database):
        """Test database insertion against benchmarks"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        # Benchmark: Database insertion should be > 50 records/second
        test_bills = generate_test_bills(200)

        start_time = time.time()
        inserted_count = 0

        for bill_data in test_bills:
            db_bill = {
                'bill_id': f'bench-{bill_data["billId"]}',
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

        end_time = time.time()
        duration = end_time - start_time
        records_per_second = inserted_count / duration

        # Benchmark assertion
        assert records_per_second >= 50, f"Insertion rate {records_per_second:.1f}/s below benchmark of 50/s"

        print(f"📈 Database insertion benchmark:")
        print(f"   Rate: {records_per_second:.1f} records/s")
        print(f"   Benchmark: 50 records/s")
        print(f"   Status: {'✅ PASS' if records_per_second >= 50 else '❌ FAIL'}")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_api_rate_limiting_benchmark(self):
        """Test API rate limiting against benchmarks"""
        limiter = adaptive_limiters['congress.gov']

        # Benchmark: Congress API should be limited to ~2 requests/second
        target_rate = 2.0

        start_time = time.time()
        requests_made = 0

        # Make requests for 10 seconds
        end_time = start_time + 10

        while time.time() < end_time:
            limiter.wait_for_token(1)
            requests_made += 1

        actual_duration = time.time() - start_time
        actual_rate = requests_made / actual_duration

        # Benchmark assertion
        assert actual_rate <= target_rate * 1.1, f"Rate {actual_rate:.2f}/s exceeds benchmark {target_rate}/s"

        print(f"🌐 API rate limiting benchmark:")
        print(f"   Target rate: {target_rate}/s")
        print(f"   Actual rate: {actual_rate:.2f}/s")
        print(f"   Total requests: {requests_made}")
        print(f"   Status: {'✅ PASS' if actual_rate <= target_rate * 1.1 else '❌ FAIL'}")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_memory_usage_benchmark(self):
        """Test memory usage against benchmarks"""
        import gc

        process = psutil.Process()

        # Force garbage collection
        gc.collect()
        baseline_memory = process.memory_info().rss

        # Simulate processing 10,000 items
        test_data = []
        for i in range(10000):
            item = {
                'id': i,
                'title': f'Item {i}',
                'data': 'x' * 100,  # 100 chars per item
                'metadata': {'processed': False, 'timestamp': time.time()}
            }
            test_data.append(item)

        peak_memory = process.memory_info().rss
        memory_per_item = (peak_memory - baseline_memory) / 10000

        # Benchmark: Memory usage should be reasonable
        max_memory_per_item = 1000  # 1KB per item max
        assert memory_per_item <= max_memory_per_item, f"Memory usage {memory_per_item:.0f}B/item exceeds benchmark"

        # Clean up
        test_data.clear()
        gc.collect()

        final_memory = process.memory_info().rss

        print(f"🧠 Memory usage benchmark:")
        print(f"   Baseline: {baseline_memory / 1024 / 1024:.2f}MB")
        print(f"   Peak: {peak_memory / 1024 / 1024:.2f}MB")
        print(f"   Per item: {memory_per_item:.0f}B")
        print(f"   Benchmark: {max_memory_per_item}B/item")
        print(f"   Status: {'✅ PASS' if memory_per_item <= max_memory_per_item else '❌ FAIL'}")

class TestPerformanceMonitoring:
    """Test performance monitoring and alerting"""

    @pytest.mark.performance
    @pytest.mark.unit
    def test_performance_alert_thresholds(self):
        """Test performance monitoring with alert thresholds"""
        class PerformanceMonitor:
            def __init__(self):
                self.metrics = {}
                self.alerts = []

            def record_metric(self, name: str, value: float, threshold: float = None):
                self.metrics[name] = value

                if threshold and value > threshold:
                    self.alerts.append({
                        'metric': name,
                        'value': value,
                        'threshold': threshold,
                        'timestamp': time.time()
                    })

            def get_alerts(self):
                return self.alerts

        monitor = PerformanceMonitor()

        # Test various metrics with thresholds
        test_cases = [
            ('api_response_time', 0.5, 1.0),  # Should not alert
            ('api_response_time', 2.0, 1.0),  # Should alert
            ('memory_usage', 100, 200),       # Should not alert
            ('memory_usage', 250, 200),       # Should alert
        ]

        for metric, value, threshold in test_cases:
            monitor.record_metric(metric, value, threshold)

        alerts = monitor.get_alerts()

        # Should have 2 alerts
        assert len(alerts) == 2, f"Expected 2 alerts, got {len(alerts)}"

        # Check alert contents
        alert_metrics = [alert['metric'] for alert in alerts]
        assert 'api_response_time' in alert_metrics
        assert 'memory_usage' in alert_metrics

        print(f"🚨 Performance alerts:")
        for alert in alerts:
            print(f"   {alert['metric']}: {alert['value']} > {alert['threshold']}")

    @pytest.mark.performance
    @pytest.mark.unit
    def test_performance_trend_analysis(self):
        """Test performance trend analysis"""
        def analyze_performance_trend(values: List[float]) -> Dict[str, Any]:
            """Analyze performance trend"""
            if len(values) < 2:
                return {'trend': 'insufficient_data'}

            # Calculate trend slope
            n = len(values)
            x_values = list(range(n))
            y_values = values

            # Simple linear trend calculation
            x_mean = sum(x_values) / n
            y_mean = sum(y_values) / n

            numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

            slope = numerator / denominator if denominator != 0 else 0

            # Determine trend
            if slope > 0.1:
                trend = 'degrading'
            elif slope < -0.1:
                trend = 'improving'
            else:
                trend = 'stable'

            return {
                'trend': trend,
                'slope': slope,
                'average': statistics.mean(values),
                'latest': values[-1]
            }

        # Test with degrading performance
        degrading_data = [1.0, 1.1, 1.3, 1.6, 2.0]
        degrading_result = analyze_performance_trend(degrading_data)

        assert degrading_result['trend'] == 'degrading'

        # Test with improving performance
        improving_data = [2.0, 1.8, 1.5, 1.2, 1.0]
        improving_result = analyze_performance_trend(improving_data)

        assert improving_result['trend'] == 'improving'

        # Test with stable performance
        stable_data = [1.0, 1.05, 0.95, 1.02, 0.98]
        stable_result = analyze_performance_trend(stable_data)

        assert stable_result['trend'] == 'stable'

        print(f"📈 Performance trend analysis:")
        print(f"   Degrading: {degrading_result['trend']} (slope: {degrading_result['slope']:.3f})")
        print(f"   Improving: {improving_result['trend']} (slope: {improving_result['slope']:.3f})")
        print(f"   Stable: {stable_result['trend']} (slope: {stable_result['slope']:.3f})")
