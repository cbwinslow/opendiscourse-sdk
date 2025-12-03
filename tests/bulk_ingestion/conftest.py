"""
Pytest configuration and shared fixtures for bulk ingestion tests
"""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Generator
from unittest.mock import Mock, patch

# Add scripts directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))

# Import modules to test
from env_config import load_env_file, get_optional_env_var, get_database_config
from rate_limiter import RateLimiter, TokenBucket, AdaptiveRateLimiter

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment for all tests"""
    # Load environment variables
    load_env_file()

    # Create temporary test database if needed
    setup_test_database()

    yield

    # Cleanup after all tests
    cleanup_test_environment()

def setup_test_database():
    """Setup test database with proper schema"""
    # This would typically run migrations or setup test database
    # For now, we'll just verify basic connectivity
    pass

def cleanup_test_environment():
    """Cleanup after test session"""
    # Remove any temporary files or cleanup resources
    pass

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing"""
    test_env = {
        'CONGRESS_API_KEY': 'test_congress_key_12345',
        'OPENSTATES_API_KEY': 'test_openstates_key_67890',
        'GOVINFO_API_KEY': 'test_govinfo_key_abcdef',
        'DB_NAME': 'opendiscourse_test',
        'DB_USER': 'test_user',
        'DB_PASSWORD': 'test_password',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432'
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env

@pytest.fixture
def clean_database():
    """Provide clean database connection for tests"""
    import psycopg2
    from psycopg2.extras import RealDictCursor

    # Get test database config
    db_config = get_database_config()

    # Override for test
    db_config['database'] = 'opendiscourse_test'

    try:
        conn = psycopg2.connect(**db_config)
        conn.autocommit = False

        # Clean database state
        cursor = conn.cursor()

        # Clear test data from relevant tables
        tables_to_clean = [
            'congress.bills',
            'congress.bill_subjects',
            'congress.members',
            'incremental.ingestion_sessions',
            'incremental.processing_checkpoints'
        ]

        for table in tables_to_clean:
            try:
                cursor.execute(f"DELETE FROM {table};")
            except Exception:
                # Table might not exist, that's ok for tests
                pass

        conn.commit()
        cursor.close()

        yield conn

    finally:
        if 'conn' in locals() and conn:
            conn.close()

@pytest.fixture
def temp_dir():
    """Provide temporary directory for test files"""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def rate_limiter():
    """Provide rate limiter instance for testing"""
    return RateLimiter()

@pytest.fixture
def adaptive_limiter():
    """Provide adaptive rate limiter instance for testing"""
    return AdaptiveRateLimiter('test_api', 1.0, 5)

@pytest.fixture
def mock_requests():
    """Mock requests module for API testing"""
    with patch('requests.get') as mock_get, \
         patch('requests.post') as mock_post:

        # Configure default responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'X-RateLimit-Remaining': '100', 'X-RateLimit-Reset': '3600'}
        mock_response.json.return_value = {
            'bills': [
                {
                    'billId': 'hr123-118',
                    'type': 'HR',
                    'number': '123',
                    'titles': [{'title': 'Test Bill Title'}],
                    'sponsor': {'bioguideId': 'T0001'},
                    'introducedDate': '2024-01-15T00:00:00Z',
                    'url': 'https://api.congress.gov/bill/hr123-118/'
                }
            ]
        }
        mock_get.return_value = mock_response

        yield {
            'get': mock_get,
            'post': mock_post,
            'response': mock_response
        }

@pytest.fixture
def sample_bill_data():
    """Provide sample bill data for testing"""
    return {
        'billId': 'hr123-118',
        'type': 'HR',
        'number': '123',
        'titles': [
            {'title': 'Test Bill Title', 'type': 'short'},
            {'title': 'A Bill to Test Something', 'type': 'official'}
        ],
        'sponsor': {
            'bioguideId': 'T0001',
            'fullName': 'Test Sponsor'
        },
        'introducedDate': '2024-01-15T00:00:00Z',
        'url': 'https://api.congress.gov/bill/hr123-118/',
        'actions': [
            {
                'actionDate': '2024-01-15T00:00:00Z',
                'text': 'Introduced in House'
            }
        ],
        'policyArea': {
            'name': 'Government Operations'
        },
        'subjects': [
            {'name': 'Tax policy'},
            {'name': 'Government spending'}
        ]
    }

@pytest.fixture
def database_stats():
    """Provide database statistics tracking"""
    class DatabaseStats:
        def __init__(self):
            self.before_count = {}
            self.after_count = {}
            self.queries_executed = []

        def record_before(self, table_name: str, count: int):
            self.before_count[table_name] = count

        def record_after(self, table_name: str, count: int):
            self.after_count[table_name] = count

        def get_inserted_count(self, table_name: str) -> int:
            before = self.before_count.get(table_name, 0)
            after = self.after_count.get(table_name, 0)
            return max(0, after - before)

        def add_query(self, query: str):
            self.queries_executed.append(query)

    return DatabaseStats()

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring utilities"""
    import time
    import psutil

    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.start_memory = None
            self.end_time = None
            self.end_memory = None
            self.operations = []

        def start(self):
            self.start_time = time.time()
            self.start_memory = psutil.Process().memory_info().rss

        def end(self):
            self.end_time = time.time()
            self.end_memory = psutil.Process().memory_info().rss

        def record_operation(self, operation: str, start_time: float, end_time: float):
            self.operations.append({
                'operation': operation,
                'duration': end_time - start_time,
                'start_time': start_time,
                'end_time': end_time
            })

        def get_duration(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

        def get_memory_delta(self) -> int:
            if self.start_memory and self.end_memory:
                return self.end_memory - self.start_memory
            return 0

        def get_operations_per_second(self, total_operations: int) -> float:
            duration = self.get_duration()
            if duration > 0:
                return total_operations / duration
            return 0

    return PerformanceMonitor()

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "database: marks tests that require database access")

# Test data generators
def generate_test_bills(count: int = 10) -> list:
    """Generate test bill data"""
    bills = []
    for i in range(count):
        bill = {
            'billId': f'hr{i+100}-{118}',
            'type': 'HR',
            'number': str(i + 100),
            'titles': [{'title': f'Test Bill {i+100}'}],
            'sponsor': {'bioguideId': f'T{str(i+1).zfill(4)}'},
            'introducedDate': f'2024-{(i % 12) + 1:02d}-15T00:00:00Z',
            'url': f'https://api.congress.gov/bill/hr{i+100}-118/',
            'actions': [],
            'policyArea': {'name': f'Test Policy Area {i % 3}'},
            'subjects': [{'name': f'Test Subject {i % 5}'}]
        }
        bills.append(bill)
    return bills

# Utility functions for tests
def assert_database_connected(conn):
    """Assert database is connected and functional"""
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    cursor.close()
    assert result[0] == 1

def assert_api_key_valid(api_key: str):
    """Assert API key is valid format"""
    assert api_key is not None
    assert len(api_key) > 10
    assert not api_key.startswith('DEMO')
    assert not api_key.startswith('TEST')

def assert_rate_limiter_functional(limiter):
    """Assert rate limiter is functional"""
    assert limiter is not None
    assert hasattr(limiter, 'consume')
    assert hasattr(limiter, 'wait_for_token')

    # Test token consumption
    assert limiter.consume(1)  # Should succeed initially
    assert not limiter.consume(999999)  # Should fail for insufficient tokens

# Test skip conditions
def should_skip_network_tests():
    """Check if network tests should be skipped"""
    return os.getenv('SKIP_NETWORK_TESTS', 'false').lower() == 'true'

def should_skip_integration_tests():
    """Check if integration tests should be skipped"""
    return os.getenv('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true'

def pytest_runtest_setup(item):
    """Setup for each test"""
    # Skip network tests if env var is set
    if 'network' in item.keywords and should_skip_network_tests():
        pytest.skip("Network tests skipped via environment variable")

    # Skip integration tests if env var is set
    if 'integration' in item.keywords and should_skip_integration_tests():
        pytest.skip("Integration tests skipped via environment variable")
