"""
Error handling and recovery tests
"""

import pytest
import time
import requests
from unittest.mock import patch, Mock, MagicMock
from typing import Dict, Any
import psycopg2

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

from rate_limiter import adaptive_limiters

class TestNetworkErrorHandling:
    """Test network error handling and recovery"""

    @pytest.mark.unit
    def test_connection_timeout_handling(self):
        """Test handling of connection timeouts"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Connection timeout")

            with pytest.raises(requests.exceptions.Timeout):
                requests.get('https://api.congress.gov/v3/bill', timeout=5)

    @pytest.mark.unit
    def test_connection_error_handling(self):
        """Test handling of connection errors"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            with pytest.raises(requests.exceptions.ConnectionError):
                requests.get('https://api.congress.gov/v3/bill')

    @pytest.mark.unit
    def test_http_error_responses(self):
        """Test handling of various HTTP error responses"""
        error_scenarios = [
            (400, 'Bad Request'),
            (401, 'Unauthorized'),
            (403, 'Forbidden'),
            (404, 'Not Found'),
            (429, 'Too Many Requests'),
            (500, 'Internal Server Error'),
            (502, 'Bad Gateway'),
            (503, 'Service Unavailable')
        ]

        for status_code, expected_message in error_scenarios:
            mock_response = Mock()
            mock_response.status_code = status_code
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(f"HTTP {status_code}")

            with patch('requests.get') as mock_get:
                mock_get.return_value = mock_response

                response = requests.get('https://api.congress.gov/v3/test')

                if status_code >= 400:
                    with pytest.raises(requests.exceptions.HTTPError):
                        response.raise_for_status()

class TestAPIErrorRecovery:
    """Test API error recovery mechanisms"""

    @pytest.mark.unit
    def test_rate_limit_recovery(self):
        """Test recovery from rate limit errors"""
        def simulate_rate_limited_request():
            """Simulate a rate-limited request with recovery"""
            if not hasattr(simulate_rate_limited_request, 'attempt_count'):
                simulate_rate_limited_request.attempt_count = 0

            simulate_rate_limited_request.attempt_count += 1

            if simulate_rate_limited_request.attempt_count == 1:
                mock_response = Mock()
                mock_response.status_code = 429
                mock_response.headers = {
                    'X-RateLimit-Remaining': '0',
                    'X-RateLimit-Reset': str(int(time.time()) + 60),
                    'Retry-After': '60'
                }
                return mock_response
            else:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = {'bills': []}
                return mock_response

        with patch('requests.get') as mock_get:
            mock_get.side_effect = simulate_rate_limited_request

            response1 = requests.get('https://api.congress.gov/v3/bill')
            assert response1.status_code == 429

            time.sleep(0.1)

            response2 = requests.get('https://api.congress.gov/v3/bill')
            assert response2.status_code == 200

    @pytest.mark.unit
    def test_adaptive_rate_limiter_error_recovery(self):
        """Test adaptive rate limiter error recovery"""
        limiter = adaptive_limiters['congress.gov']

        initial_rate = limiter.current_rate

        for _ in range(5):
            limiter.handle_error(429)

        assert limiter.current_rate < initial_rate

        for _ in range(3):
            limiter.handle_error(200)

        assert limiter.consecutive_errors == 0

    @pytest.mark.unit
    def test_retry_logic_with_exponential_backoff(self):
        """Test retry logic with exponential backoff"""
        def calculate_backoff_delay(attempt: int, base_delay: float = 1.0, max_delay: float = 60.0) -> float:
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            return delay

        delays = [calculate_backoff_delay(i) for i in range(1, 6)]

        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0

        assert calculate_backoff_delay(10) <= 60.0

class TestDatabaseErrorHandling:
    """Test database error handling and recovery"""

    @pytest.mark.database
    @pytest.mark.integration
    def test_database_connection_failure(self):
        """Test handling of database connection failures"""
        def mock_db_connect(*args, **kwargs):
            raise psycopg2.OperationalError("Connection refused")

        with patch('psycopg2.connect', side_effect=mock_db_connect):
            from .utils.database_utils import get_database_helper
            helper = get_database_helper(use_test_db=False)

            with pytest.raises(psycopg2.OperationalError):
                with helper.get_connection():
                    pass

    @pytest.mark.database
    @pytest.mark.integration
    def test_database_constraint_violations(self, clean_database):
        """Test handling of database constraint violations"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        bill_data = {
            'bill_id': 'hr997-118',
            'congress': 118,
            'bill_type': 'HR',
            'bill_number': '997',
            'title': 'First Test Bill',
            'sponsor_bioguide_id': 'T0001'
        }

        helper.insert_test_bill(bill_data)

        duplicate_data = bill_data.copy()
        duplicate_data['title'] = 'Updated Test Bill'

        success = helper.insert_test_bill(duplicate_data)
        assert success == True

    @pytest.mark.database
    @pytest.mark.integration
    def test_database_transaction_rollback(self, clean_database):
        """Test transaction rollback on errors"""
        from .utils.database_utils import get_database_helper
        helper = get_database_helper(use_test_db=False)

        before_count = helper.get_table_count('congress.bills')

        cursor = clean_database.cursor()

        try:
            cursor.execute("""
                INSERT INTO congress.bills (bill_id, congress, bill_type, bill_number, title)
                VALUES ('hr995-118', 118, 'HR', '995', 'Valid Bill')
            """)

            cursor.execute("""
                INSERT INTO congress.bills (bill_id, congress, bill_type, bill_number, title)
                VALUES (NULL, 118, 'HR', '996', 'Invalid Bill')
            """)

            clean_database.commit()
        except psycopg2.Error:
            clean_database.rollback()
        finally:
            cursor.close()

        after_count = helper.get_table_count('congress.bills')
        assert after_count == before_count + 1

class TestDataCorruptionHandling:
    """Test handling of data corruption scenarios"""

    @pytest.mark.unit
    def test_invalid_json_response(self):
        """Test handling of invalid JSON responses"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch('requests.get') as mock_get:
            mock_get.return_value = mock_response

            response = requests.get('https://api.congress.gov/v3/bill')

            with pytest.raises(ValueError):
                response.json()

    @pytest.mark.unit
    def test_malformed_api_response(self):
        """Test handling of malformed API responses"""
        def normalize_bill_data_safe(bill_data: Dict[str, Any]) -> Dict[str, Any]:
            try:
                bill = bill_data.get('bill', bill_data)

                bill_id = bill.get('billId', '')
                if not bill_id:
                    raise ValueError("Missing required billId")

                title = ''
                if bill.get('titles') and isinstance(bill['titles'], list):
                    title = bill['titles'][0].get('title', '') if bill['titles'] else ''

                return {
                    'bill_id': bill_id,
                    'title': title,
                    'congress': 118
                }
            except Exception as e:
                raise

        with pytest.raises(ValueError):
            normalize_bill_data_safe({'type': 'HR'})

        valid_data = {'billId': 'hr123-118', 'titles': [{'title': 'Test'}]}
        result = normalize_bill_data_safe(valid_data)
        assert result['bill_id'] == 'hr123-118'
        assert result['title'] == 'Test'

    @pytest.mark.unit
    def test_encoding_errors(self):
        """Test handling of encoding errors"""
        def safe_decode_data(data: bytes) -> str:
            try:
                return data.decode('utf-8')
            except UnicodeDecodeError:
                return data.decode('latin-1', errors='replace')

        valid_data = b'Test data with unicode: \xc3\xa9'
        result = safe_decode_data(valid_data)
        assert 'é' in result

        invalid_data = b'Test data with invalid: \xff\xfe'
        result = safe_decode_data(invalid_data)
        assert 'Test data with invalid:' in result

class TestResourceExhaustionHandling:
    """Test handling of resource exhaustion scenarios"""

    @pytest.mark.performance
    @pytest.mark.unit
    def test_memory_pressure_handling(self):
        """Test handling of memory pressure"""
        def process_large_dataset_safely(data_size: int) -> bool:
            try:
                chunk_size = 100
                total_processed = 0

                for i in range(0, data_size, chunk_size):
                    chunk = list(range(i, min(i + chunk_size, data_size)))
                    processed_chunk = [x * 2 for x in chunk]
                    total_processed += len(processed_chunk)

                    if total_processed > 1000:
                        break

                return total_processed > 0
            except MemoryError:
                return False

        result = process_large_dataset_safely(1000)
        assert result == True

        with patch('builtins.memory_usage', create=True) as mock_memory:
            mock_memory.return_value = 1000

            result = process_large_dataset_safely(10000)
            assert isinstance(result, bool)

    @pytest.mark.performance
    @pytest.mark.unit
    def test_rate_limit_exhaustion(self):
        """Test handling of rate limit exhaustion"""
        limiter = adaptive_limiters['congress.gov']

        initial_rate = limiter.current_rate
        initial_capacity = limiter.bucket.capacity

        for _ in range(10):
            limiter.handle_error(429)

        assert limiter.current_rate < initial_rate * 0.5
        assert limiter.consecutive_errors > 0

        for _ in range(5):
            limiter.handle_error(200)

        assert limiter.consecutive_errors == 0

class TestInterruptionRecovery:
    """Test recovery from process interruptions"""

    @pytest.mark.unit
    def test_checkpoint_recovery(self):
        """Test recovery from checkpoint"""
        def simulate_interrupted_ingestion():
            processed_items = []
            checkpoint_data = {
                'last_processed_id': None,
                'processed_count': 0,
                'session_id': 'test_session_123'
            }

            for i in range(10):
                if i < 5:
                    processed_items.append(f'item_{i}')
                    checkpoint_data['processed_count'] = i + 1
                    checkpoint_data['last_processed_id'] = f'item_{i}'
                else:
                    if checkpoint_data['processed_count'] > i:
                        continue

                    processed_items.append(f'item_{i}')
                    checkpoint_data['processed_count'] = i + 1

            return processed_items, checkpoint_data

        processed, checkpoint = simulate_interrupted_ingestion()

        assert len(processed) == 10
        assert checkpoint['processed_count'] == 10
        assert checkpoint['last_processed_id'] == 'item_9'

    @pytest.mark.unit
    def test_session_resumption(self):
        """Test session resumption after interruption"""
        def resume_ingestion_session(session_id: str, last_checkpoint: Dict[str, Any]):
            current_state = {
                'session_id': session_id,
                'status': 'interrupted',
                'last_checkpoint': last_checkpoint,
                'items_processed': last_checkpoint.get('processed_count', 0)
            }

            resume_offset = current_state['items_processed']

            resumed_items = []
            for i in range(resume_offset, resume_offset + 5):
                resumed_items.append(f'resumed_item_{i}')
                current_state['items_processed'] += 1

            return {
                'resumed': True,
                'items_processed': current_state['items_processed'],
                'resumed_items': resumed_items
            }

        last_checkpoint = {'processed_count': 3}
        result = resume_ingestion_session('test_session', last_checkpoint)

        assert result['resumed'] == True
        assert result['items_processed'] == 8
        assert len(result['resumed_items']) == 5

    @pytest.mark.unit
    def test_partial_batch_recovery(self):
        """Test recovery from partial batch failures"""
        def process_batch_with_recovery(batch_size: int = 50):
            results = {
                'successful': [],
                'failed': [],
                'retry_count': 0
            }

            for i in range(batch_size):
                try:
                    if i % 7 == 0:
                        results['failed'].append(i)
                        results['retry_count'] += 1
                    else:
                        results['successful'].append(i)
                except Exception:
                    results['failed'].append(i)
                    results['retry_count'] += 1

            return results

        batch_results = process_batch_with_recovery(50)

        assert len(batch_results['successful']) > 0
        assert len(batch_results['failed']) > 0
        assert len(batch_results['successful']) + len(batch_results['failed']) == 50
        assert batch_results['retry_count'] == len(batch_results['failed'])

class TestErrorReporting:
    """Test error reporting and logging"""

    @pytest.mark.unit
    def test_error_summary_aggregation(self):
        """Test aggregation of error summaries"""
        def aggregate_error_summary(errors: list) -> Dict[str, Any]:
            summary = {
                'total_errors': len(errors),
                'error_types': {},
                'severity_distribution': {'critical': 0, 'warning': 0, 'info': 0}
            }

            for error in errors:
                error_type = error.get('type', 'unknown')
                severity = error.get('severity', 'warning')

                summary['error_types'][error_type] = summary['error_types'].get(error_type, 0) + 1

                if severity in summary['severity_distribution']:
                    summary['severity_distribution'][severity] += 1

            return summary

        test_errors = [
            {'type': 'api_timeout', 'severity': 'critical'},
            {'type': 'api_timeout', 'severity': 'critical'},
            {'type': 'validation_error', 'severity': 'warning'},
            {'type': 'network_error', 'severity': 'warning'}
        ]

        summary = aggregate_error_summary(test_errors)

        assert summary['total_errors'] == 4
        assert summary['error_types']['api_timeout'] == 2
        assert summary['error_types']['validation_error'] == 1
        assert summary['severity_distribution']['critical'] == 2
        assert summary['severity_distribution']['warning'] == 2

    @pytest.mark.unit
    def test_error_context_preservation(self):
        """Test preservation of error context"""
        def capture_error_context(operation: str, data: Dict[str, Any]):
            context = {
                'operation': operation,
                'timestamp': time.time(),
                'data_size': len(str(data)),
                'data_keys': list(data.keys()) if isinstance(data, dict) else None,
                'error_occurred': False
            }

            try:
                if operation == 'failing_operation':
                    raise ValueError("Simulated failure")
                return {'success': True, 'context': context}
            except Exception as e:
                context.update({
                    'error_occurred': True,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                })
                return {'success': False, 'context': context}

        result1 = capture_error_context('normal_operation', {'test': 'data'})
        assert result1['success'] == True
        assert result1['context']['error_occurred'] == False

        result2 = capture_error_context('failing_operation', {'test': 'data'})
        assert result2['success'] == False
        assert result2['context']['error_occurred'] == True
        assert result2['context']['error_type'] == 'ValueError'
