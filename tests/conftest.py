"""
================================================================================
File: conftest.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Enhanced pytest configuration with comprehensive fixtures for OpenDiscourse
    testing suite. Provides fixtures for database, API mocking, file system,
    performance testing, and more.

================================================================================
"""

import os
import sys
import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import test helpers
from tests.utils.test_helpers import (
    DatabaseTestHelper,
    APITestHelper,
    FileSystemTestHelper,
    PerformanceTestHelper,
    TestConfigHelper,
    generate_test_uuid,
    create_mock_datetime
)

# Import modules to test
try:
    from scripts.core.database_adapter import DatabaseAdapter, DatabaseBackend
    from scripts.ingestion.congress_ingestor import CongressDataIngester
    from scripts.ingestion.openstates_ingestor import OpenStatesIngester
    from scripts.ingestion.govinfo_ingestor import GovInfoIngester
    from scripts.utils.rate_limiter import RateLimiter, AdaptiveRateLimiter
    from scripts.utils.api_client import APIError, RateLimitError
except ImportError as e:
    print(f"Warning: Could not import some modules for testing: {e}")


# ============================================================================
# Global Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "network: marks tests that require network access")
    config.addinivalue_line("markers", "database: marks tests that require database access")
    config.addinivalue_line("markers", "api: marks tests that require API access")
    config.addinivalue_line("markers", "e2e: marks end-to-end tests")
    config.addinivalue_line("markers", "load: marks tests for load testing")


# ============================================================================
# Environment Setup Fixtures
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment for the entire test session."""
    temp_dir = TestConfigHelper.setup_test_environment()
    yield
    TestConfigHelper.cleanup_test_environment(temp_dir)


@pytest.fixture
def mock_env_vars():
    """Provide mocked environment variables for testing."""
    test_env = TestConfigHelper.get_test_env_vars()

    with patch.dict(os.environ, test_env, clear=False):
        yield test_env


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
def temp_sqlite_db():
    """Create temporary SQLite database for testing."""
    temp_file = tempfile.mktemp(suffix='.db')
    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.fixture
def sqlite_adapter(temp_sqlite_db):
    """Create SQLite adapter for testing."""
    try:
        from scripts.core.database_adapter import SQLiteAdapter
        adapter = SQLiteAdapter(database=temp_sqlite_db)
        yield adapter
    except ImportError:
        pytest.skip("Database adapter not available")


@pytest.fixture
def mock_database_connection():
    """Create mock database connection."""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_conn.commit = Mock()
    mock_conn.rollback = Mock()
    mock_conn.close = Mock()

    mock_cursor.fetchone.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.execute.return_value = None

    return mock_conn


@pytest.fixture
def database_stats():
    """Provide database statistics tracking for tests."""
    class DatabaseStats:
        def __init__(self):
            self.before_count = {}
            self.after_count = {}
            self.queries_executed = []
            self.connections_made = 0
            self.transactions_completed = 0

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
            self.connections_made += 1

        def get_stats(self) -> Dict[str, Any]:
            return {
                'queries_executed': len(self.queries_executed),
                'connections_made': self.connections_made,
                'transactions_completed': self.transactions_completed,
                'before_counts': self.before_count,
                'after_counts': self.after_count
            }

    return DatabaseStats()


# ============================================================================
# API Mocking Fixtures
# ============================================================================

@pytest.fixture
def mock_requests_session():
    """Mock requests session with common patterns."""
    mock_session = Mock()

    # Default successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        'X-RateLimit-Remaining': '100',
        'X-RateLimit-Reset': '3600',
        'Content-Type': 'application/json'
    }
    mock_response.json.return_value = {'data': 'test'}
    mock_response.raise_for_status = Mock()

    mock_session.get.return_value = mock_response
    mock_session.post.return_value = mock_response
    mock_session.put.return_value = mock_response
    mock_session.delete.return_value = mock_response

    return mock_session


@pytest.fixture
def mock_congress_api(mock_requests_session):
    """Mock Congress.gov API responses."""
    mock_requests_session.get.return_value = APITestHelper.mock_congress_api_response()
    return mock_requests_session


@pytest.fixture
def mock_openstates_api(mock_requests_session):
    """Mock OpenStates API responses."""
    mock_requests_session.get.return_value = APITestHelper.mock_openstates_api_response()
    return mock_requests_session


@pytest.fixture
def mock_govinfo_api(mock_requests_session):
    """Mock GovInfo API responses."""
    mock_requests_session.get.return_value = APITestHelper.mock_govinfo_api_response()
    return mock_requests_session


@pytest.fixture
def rate_limiter():
    """Provide rate limiter instance for testing."""
    return RateLimiter()


@pytest.fixture
def adaptive_rate_limiter():
    """Provide adaptive rate limiter instance for testing."""
    return AdaptiveRateLimiter('test_api', requests_per_second=1.0, max_burst=5)


@pytest.fixture
def api_client_config():
    """Provide API client configuration for testing."""
    return {
        'congress_api': {
            'base_url': 'https://api.congress.gov/v3',
            'timeout': 30,
            'retry_attempts': 3,
            'rate_limit': 100  # requests per hour
        },
        'openstates_api': {
            'base_url': 'https://api.openstates.org/v3',
            'timeout': 30,
            'retry_attempts': 3,
            'rate_limit': 1000  # requests per day
        },
        'govinfo_api': {
            'base_url': 'https://api.govinfo.gov',
            'timeout': 60,
            'retry_attempts': 3,
            'rate_limit': 500  # requests per day
        }
    }


# ============================================================================
# Data Generation Fixtures
# ============================================================================

@pytest.fixture
def sample_bill_data():
    """Provide sample bill data for testing."""
    return DatabaseTestHelper._generate_bill_data(1)[0]


@pytest.fixture
def sample_member_data():
    """Provide sample member data for testing."""
    return DatabaseTestHelper._generate_member_data(1)[0]


@pytest.fixture
def sample_vote_data():
    """Provide sample vote data for testing."""
    return DatabaseTestHelper._generate_vote_data(1)[0]


@pytest.fixture
def batch_bill_data():
    """Provide batch of bill data for testing."""
    return DatabaseTestHelper._generate_bill_data(10)


@pytest.fixture
def batch_member_data():
    """Provide batch of member data for testing."""
    return DatabaseTestHelper._generate_member_data(20)


@pytest.fixture
def ingestion_session_data():
    """Provide ingestion session data for testing."""
    return DatabaseTestHelper._generate_session_data(1)[0]


@pytest.fixture
def test_data_factory():
    """Provide factory for generating test data."""
    class TestDataFactory:
        @staticmethod
        def create_bill_data(count: int = 1, **overrides) -> Dict[str, Any]:
            data = DatabaseTestHelper._generate_bill_data(count)[0]
            data.update(overrides)
            return data

        @staticmethod
        def create_member_data(count: int = 1, **overrides) -> Dict[str, Any]:
            data = DatabaseTestHelper._generate_member_data(count)[0]
            data.update(overrides)
            return data

        @staticmethod
        def create_vote_data(count: int = 1, **overrides) -> Dict[str, Any]:
            data = DatabaseTestHelper._generate_vote_data(count)[0]
            data.update(overrides)
            return data

        @staticmethod
        def create_session_data(**overrides) -> Dict[str, Any]:
            data = DatabaseTestHelper._generate_session_data(1)[0]
            data.update(overrides)
            return data

    return TestDataFactory()


# ============================================================================
# File System Fixtures
# ============================================================================

@pytest.fixture
def temp_directory():
    """Provide temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix='opendiscourse_test_')
    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_file():
    """Provide temporary file for testing."""
    fd, temp_path = tempfile.mkstemp(prefix='opendiscourse_test_')
    os.close(fd)
    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def test_files(temp_directory):
    """Create test files in temporary directory."""
    created_files = FileSystemTestHelper.create_test_files(temp_directory, count=5)
    yield created_files

    # Cleanup
    for file_path in created_files:
        if os.path.exists(file_path):
            os.unlink(file_path)


# ============================================================================
# Performance Testing Fixtures
# ============================================================================

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring utilities."""
    return PerformanceTestHelper


@pytest.fixture
def load_test_data():
    """Provide load test data generators."""
    class LoadTestData:
        @staticmethod
        def generate_small_data() -> bytes:
            return PerformanceTestHelper.generate_load_test_data(size_mb=0.1)

        @staticmethod
        def generate_medium_data() -> bytes:
            return PerformanceTestHelper.generate_load_test_data(size_mb=1.0)

        @staticmethod
        def generate_large_data() -> bytes:
            return PerformanceTestHelper.generate_load_test_data(size_mb=10.0)

    return LoadTestData()


# ============================================================================
# Async Testing Fixtures
# ============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def async_api_client():
    """Provide async API client for testing."""
    class MockAsyncAPIClient:
        def __init__(self):
            self.requests_made = []

        async def get(self, url: str, **kwargs) -> Dict[str, Any]:
            self.requests_made.append(('GET', url, kwargs))
            return {'status': 'success', 'data': 'mocked response'}

        async def post(self, url: str, **kwargs) -> Dict[str, Any]:
            self.requests_made.append(('POST', url, kwargs))
            return {'status': 'success', 'data': 'mocked response'}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    return MockAsyncAPIClient()


# ============================================================================
# Custom Testing Utilities
# ============================================================================

@pytest.fixture
def assert_helpers():
    """Provide custom assertion helpers."""
    class AssertHelpers:
        @staticmethod
        def dict_contains_subset(subset: Dict[str, Any], superset: Dict[str, Any]):
            """Assert that subset dictionary is contained in superset."""
            for key, value in subset.items():
                assert key in superset, f"Key '{key}' not found in superset"
                assert superset[key] == value, f"Value mismatch for key '{key}': expected '{value}', got '{superset[key]}'"

        @staticmethod
        def api_response_valid(response: Dict[str, Any]):
            """Assert API response has required fields."""
            required_fields = ['status', 'data']
            for field in required_fields:
                assert field in response, f"Missing required field: {field}"

        @staticmethod
        def database_row_valid(row: Dict[str, Any], required_fields: list):
            """Assert database row has required fields."""
            for field in required_fields:
                assert field in row, f"Missing required database field: {field}"
                assert row[field] is not None, f"Database field '{field}' cannot be None"

    return AssertHelpers()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """Provide test configuration settings."""
    return {
        'database': {
            'backend': 'sqlite',
            'connection_string': ':memory:',
            'pool_size': 5,
            'timeout': 30
        },
        'api': {
            'timeout': 30,
            'retry_attempts': 3,
            'retry_delay': 1.0,
            'rate_limit_enabled': True
        },
        'logging': {
            'level': 'DEBUG',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
        'cache': {
            'enabled': False,
            'ttl': 300,
            'max_size': 1000
        }
    }


@pytest.fixture
def congress_config():
    """Provide Congress.gov API configuration."""
    return {
        'base_url': 'https://api.congress.gov/v3',
        'version': 'v3',
        'format': 'json',
        'timeout': 30,
        'rate_limit': {
            'requests_per_hour': 100,
            'burst_limit': 10
        }
    }


@pytest.fixture
def openstates_config():
    """Provide OpenStates API configuration."""
    return {
        'base_url': 'https://api.openstates.org/v3',
        'version': 'v3',
        'format': 'json',
        'timeout': 30,
        'rate_limit': {
            'requests_per_day': 1000,
            'burst_limit': 50
        }
    }


# ============================================================================
# Parameterized Test Data
# ============================================================================

@pytest.fixture(params=[
    {'congress': 118, 'bill_type': 'HR', 'status': 'Introduced'},
    {'congress': 117, 'bill_type': 'S', 'status': 'Passed'},
    {'congress': 116, 'bill_type': 'HJ', 'status': 'Failed'},
    {'congress': 115, 'bill_type': 'SJ', 'status': 'Vetoed'},
])
def bill_test_params(request):
    """Provide parameterized bill test data."""
    return request.param


@pytest.fixture(params=[
    {'state': 'CA', 'chamber': 'House', 'party': 'D'},
    {'state': 'TX', 'chamber': 'Senate', 'party': 'R'},
    {'state': 'NY', 'chamber': 'House', 'party': 'I'},
    {'state': 'FL', 'chamber': 'Senate', 'party': 'D'},
])
def member_test_params(request):
    """Provide parameterized member test data."""
    return request.param


@pytest.fixture(params=[
    {'vote_type': 'YEA-NAY', 'congress': 118},
    {'vote_type': 'PRESENT', 'congress': 117},
    {'vote_type': 'VETOED OVERRIDE', 'congress': 116},
])
def vote_test_params(request):
    """Provide parameterized vote test data."""
    return request.param


# ============================================================================
# Clean-up Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Automatically clean up test data after each test."""
    yield

    # Clean up any temporary files
    temp_dir = os.environ.get('TEMP_DIR')
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Clear any mock call history that might interfere with subsequent tests
    import unittest.mock
    for mock in unittest.mock._all_mocks():
        if hasattr(mock, 'reset_mock'):
            mock.reset_mock()


# ============================================================================
# Test Skipping Conditions
# ============================================================================

def pytest_runtest_setup(item):
    """Setup logic before each test."""
    # Skip tests based on markers and environment
    if "slow" in item.keywords and os.getenv('SKIP_SLOW_TESTS', 'false').lower() == 'true':
        pytest.skip("Slow tests skipped via environment variable")

    if "network" in item.keywords and os.getenv('SKIP_NETWORK_TESTS', 'false').lower() == 'true':
        pytest.skip("Network tests skipped via environment variable")

    if "integration" in item.keywords and os.getenv('SKIP_INTEGRATION_TESTS', 'false').lower() == 'true':
        pytest.skip("Integration tests skipped via environment variable")

    if "database" in item.keywords and not os.getenv('TEST_DATABASE_AVAILABLE', 'false').lower() == 'true':
        pytest.skip("Database tests skipped - test database not available")


# Export commonly used fixtures
__all__ = [
    'setup_test_environment',
    'mock_env_vars',
    'temp_sqlite_db',
    'sqlite_adapter',
    'mock_database_connection',
    'mock_congress_api',
    'mock_openstates_api',
    'mock_govinfo_api',
    'rate_limiter',
    'adaptive_rate_limiter',
    'sample_bill_data',
    'sample_member_data',
    'batch_bill_data',
    'temp_directory',
    'test_files',
    'performance_monitor',
    'async_api_client',
    'test_config',
    'bill_test_params',
    'member_test_params',
    'vote_test_params'
]
