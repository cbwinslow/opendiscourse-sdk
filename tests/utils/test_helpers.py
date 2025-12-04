"""
================================================================================
File: test_helpers.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Comprehensive test utilities, fixtures, and mock data generators for the
    OpenDiscourse project. Provides reusable test helpers across different
    testing frameworks (unittest, pytest, Jest).

================================================================================
"""

import json
import os
import tempfile
from datetime import datetime, date
from typing import Dict, List, Any, Optional, Union
from unittest.mock import Mock, patch
import uuid
from pathlib import Path


# ============================================================================
# Database Test Helpers
# ============================================================================

class DatabaseTestHelper:
    """Helper class for database testing operations."""

    @staticmethod
    def create_test_connection_string(backend: str = "sqlite", **kwargs) -> str:
        """Create a test database connection string."""
        if backend.lower() == "sqlite":
            temp_db = tempfile.mktemp(suffix='.db')
            return f"sqlite:///{temp_db}"
        elif backend.lower() == "postgresql":
            return f"postgresql://test_user:test_pass@localhost:5432/test_db"
        elif backend.lower() == "mysql":
            return f"mysql://test_user:test_pass@localhost:3306/test_db"
        else:
            raise ValueError(f"Unsupported database backend: {backend}")

    @staticmethod
    def generate_test_data(table_name: str, count: int = 10) -> List[Dict[str, Any]]:
        """Generate realistic test data for various table types."""
        generators = {
            'congress.members': DatabaseTestHelper._generate_member_data,
            'congress.bills': DatabaseTestHelper._generate_bill_data,
            'congress.member_terms': DatabaseTestHelper._generate_member_term_data,
            'congress.votes': DatabaseTestHelper._generate_vote_data,
            'incremental.ingestion_sessions': DatabaseTestHelper._generate_session_data,
            'incremental.processing_checkpoints': DatabaseTestHelper._generate_checkpoint_data,
        }

        generator = generators.get(table_name)
        if generator:
            return generator(count)
        else:
            # Generic generator for unknown tables
            return [
                {
                    'id': i + 1,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'data': f'test_data_{i}'
                }
                for i in range(count)
            ]

    @staticmethod
    def _generate_member_data(count: int) -> List[Dict[str, Any]]:
        """Generate test member data."""
        members = []
        for i in range(count):
            bioguide_id = f'{"A"[i % 26]}{str(i).zfill(5)}'
            members.append({
                'bioguide_id': bioguide_id,
                'first_name': f'Test{i}',
                'last_name': f'Member{i}',
                'middle_name': f'Middle{i}' if i % 3 == 0 else None,
                'suffix': 'Jr' if i % 5 == 0 else None,
                'birth_date': f'19{(80 + i % 20):02d}-{((i % 12) + 1):02d}-{((i % 28) + 1):02d}',
                'death_date': None,
                'gender': 'M' if i % 2 == 0 else 'F',
                'current_party': ['D', 'R', 'I'][i % 3],
                'state_code': ['CA', 'TX', 'FL', 'NY', 'PA'][i % 5],
                'district': (i % 50) + 1 if i % 2 == 0 else None,
                'at_large': i % 2 == 1,
                'chamber': 'House' if i % 2 == 0 else 'Senate',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return members

    @staticmethod
    def _generate_bill_data(count: int) -> List[Dict[str, Any]]:
        """Generate test bill data."""
        bills = []
        bill_types = ['HR', 'S', 'HJ', 'SJ', 'HC', 'SC']
        subjects = ['Agriculture', 'Defense', 'Education', 'Health', 'Taxation', 'Transportation']

        for i in range(count):
            bill_type = bill_types[i % len(bill_types)]
            bill_number = str((i % 1000) + 1)
            congress = 118 - (i % 5)

            bills.append({
                'bill_id': f'{bill_type.lower()}{bill_number}-{congress}',
                'congress': congress,
                'bill_type': bill_type,
                'number': bill_number,
                'title': f'Test Bill {i + 1} for Testing Purposes',
                'short_title': f'Test Bill {i + 1}',
                'policy_area': subjects[i % len(subjects)],
                'sponsor_bioguide_id': f'A{str(i).zfill(5)}',
                'introduced_date': f'2024-{((i % 12) + 1):02d}-{((i % 28) + 1):02d}',
                'latest_action_date': f'2024-{((i % 12) + 1):02d}-{((i % 28) + 1):02d}',
                'latest_action': f'Passed House on {datetime.now().strftime("%Y-%m-%d")}',
                'status': ['Introduced', 'Passed', 'Failed', 'Vetoed'][i % 4],
                'subjects': json.dumps([subjects[i % len(subjects)], subjects[(i + 1) % len(subjects)]]),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return bills

    @staticmethod
    def _generate_member_term_data(count: int) -> List[Dict[str, Any]]:
        """Generate test member term data."""
        terms = []
        for i in range(count):
            bioguide_id = f'{"A"[i % 26]}{str(i).zfill(5)}'
            congress = 118 - (i % 10)
            start_year = 2020 + (i % 5)
            end_year = start_year + 2

            terms.append({
                'bioguide_id': bioguide_id,
                'congress_number': congress,
                'session': '1' if i % 2 == 0 else '2',
                'chamber_code': 'H' if i % 2 == 0 else 'S',
                'state_code': ['CA', 'TX', 'FL', 'NY', 'PA'][i % 5],
                'district': (i % 50) + 1 if i % 2 == 0 else None,
                'at_large': i % 2 == 1,
                'party_code': ['D', 'R', 'I'][i % 3],
                'party_name': ['Democrat', 'Republican', 'Independent'][i % 3],
                'class': chr(65 + (i % 3)) if i % 2 == 1 else None,  # Senate classes
                'term_type': 'Provisional' if i % 7 == 0 else 'Full',
                'start_date': f'{start_year}-01-03',
                'end_date': f'{end_year}-01-03',
                'is_current': i < 3,  # First 3 terms are current
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return terms

    @staticmethod
    def _generate_vote_data(count: int) -> List[Dict[str, Any]]:
        """Generate test vote data."""
        votes = []
        for i in range(count):
            congress = 118 - (i % 5)
            roll_number = i + 1
            vote_date = datetime.now().strftime('%Y-%m-%d')

            votes.append({
                'vote_id': f'congress={congress}&session=1&roll={roll_number}',
                'congress': congress,
                'session': 1,
                'roll_number': roll_number,
                'vote_date': vote_date,
                'vote_type': ['YEA-NAY', 'PRESENT', 'VETOED OVERRIDE'][i % 3],
                'question': f'Test Question {i + 1} on Important Matters',
                'question_text': f'Shall the amendment {i + 1} be agreed to?',
                'subjects': json.dumps([f'Subject {i % 5}', f'Subject {(i + 1) % 5}']),
                'total_yes': 250 + (i % 50),
                'total_no': 180 + (i % 30),
                'total_present': i % 10,
                'total_not_voting': 10 + (i % 5),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return votes

    @staticmethod
    def _generate_session_data(count: int) -> List[Dict[str, Any]]:
        """Generate test ingestion session data."""
        sessions = []
        statuses = ['running', 'completed', 'failed', 'cancelled']

        for i in range(count):
            session_id = str(uuid.uuid4())
            start_time = datetime.now()
            end_time = start_time if i % 4 == 0 else None

            sessions.append({
                'session_id': session_id,
                'session_name': f'Test Ingestion Session {i + 1}',
                'source': ['congress_gov', 'openstates', 'govinfo'][i % 3],
                'status': statuses[i % 4],
                'congress_start': 118 - (i % 10),
                'congress_end': 118 - (i % 10),
                'start_time': start_time,
                'end_time': end_time,
                'records_processed': i * 100,
                'records_succeeded': i * 95,
                'records_failed': i * 5,
                'error_details': json.dumps([f'Error {i}', f'Warning {i}']) if i % 4 == 2 else None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return sessions

    @staticmethod
    def _generate_checkpoint_data(count: int) -> List[Dict[str, Any]]:
        """Generate test processing checkpoint data."""
        checkpoints = []
        for i in range(count):
            checkpoint_id = str(uuid.uuid4())
            session_id = str(uuid.uuid4())

            checkpoints.append({
                'checkpoint_id': checkpoint_id,
                'session_id': session_id,
                'checkpoint_name': f'Checkpoint {i + 1}',
                'checkpoint_type': ['api_call', 'data_processing', 'database_insert'][i % 3],
                'status': ['completed', 'running', 'failed'][i % 3],
                'start_time': datetime.now(),
                'end_time': datetime.now() if i % 3 != 1 else None,
                'records_processed': i * 50,
                'success_rate': 0.95 + (i * 0.01),
                'error_count': i % 5,
                'metadata': json.dumps({'step': i, 'phase': 'ingestion'}),
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
        return checkpoints


# ============================================================================
# API Test Helpers
# ============================================================================

class APITestHelper:
    """Helper class for API testing operations."""

    @staticmethod
    def mock_congress_api_response(success: bool = True, count: int = 10) -> Mock:
        """Create a mock Congress.gov API response."""
        mock_response = Mock()
        mock_response.status_code = 200 if success else 500
        mock_response.headers = {
            'X-RateLimit-Remaining': '100',
            'X-RateLimit-Reset': '3600',
            'Content-Type': 'application/json'
        }

        if success:
            mock_response.json.return_value = {
                'bills': DatabaseTestHelper._generate_bill_data(count),
                'pagination': {
                    'count': count,
                    'countIncludingDeletedRecords': count + 2,
                    'next': None if count < 100 else 'https://api.congress.gov/v3/bill/118/house/?offset=100',
                    'offset': 0,
                    'perPage': count,
                    'total': count + 50
                }
            }
        else:
            mock_response.raise_for_status.side_effect = Exception("API Error")

        return mock_response

    @staticmethod
    def mock_openstates_api_response(success: bool = True, count: int = 10) -> Mock:
        """Create a mock OpenStates API response."""
        mock_response = Mock()
        mock_response.status_code = 200 if success else 500
        mock_response.headers = {
            'X-RateLimit-Remaining': '100',
            'X-RateLimit-Reset': '3600',
            'Content-Type': 'application/json'
        }

        if success:
            mock_response.json.return_value = {
                'results': [
                    {
                        'id': f'ocd-bill/{i}',
                        'openstates_id': f'OS{i}',
                        'identifier': f'AB{i}',
                        'title': f'Test Bill {i}',
                        'session': {
                            'name': '2024 Regular Session',
                            'jurisdiction': 'ca'
                        },
                        'subjects': [f'Subject {i % 5}'],
                        'sponsorships': [
                            {
                                'name': f'Sponsor {i}',
                                'entity_type': 'person'
                            }
                        ],
                        'actions': [
                            {
                                'date': '2024-01-15',
                                'description': 'Introduced'
                            }
                        ],
                        'votes': []
                    }
                    for i in range(count)
                ],
                'meta': {
                    'pagination': {
                        'count': count,
                        'page': 1,
                        'per_page': count,
                        'pages': 1
                    }
                }
            }
        else:
            mock_response.raise_for_status.side_effect = Exception("API Error")

        return mock_response

    @staticmethod
    def mock_govinfo_api_response(success: bool = True, count: int = 10) -> Mock:
        """Create a mock GovInfo API response."""
        mock_response = Mock()
        mock_response.status_code = 200 if success else 500
        mock_response.headers = {
            'X-RateLimit-Remaining': '100',
            'X-RateLimit-Reset': '3600',
            'Content-Type': 'application/json'
        }

        if success:
            mock_response.json.return_value = {
                'packages': [
                    {
                        'packageId': f'BILLDETAILS-{i}',
                        'title': f'Test Bill Document {i}',
                        'download': {
                            'txt': f'https://www.govinfo.gov/content/pkg/BILLDETAILS-{i}/txt/BILLDETAILS-{i}.txt',
                            'pdf': f'https://www.govinfo.gov/content/pkg/BILLDETAILS-{i}/pdf/BILLDETAILS-{i}.pdf'
                        },
                        'dateIssued': '2024-01-15',
                        'subType': 'Bill'
                    }
                    for i in range(count)
                ]
            }
        else:
            mock_response.raise_for_status.side_effect = Exception("API Error")

        return mock_response


# ============================================================================
# File System Test Helpers
# ============================================================================

class FileSystemTestHelper:
    """Helper class for file system testing operations."""

    @staticmethod
    def create_test_files(directory: str, count: int = 5) -> List[str]:
        """Create test files in a directory."""
        os.makedirs(directory, exist_ok=True)
        created_files = []

        for i in range(count):
            file_path = os.path.join(directory, f'test_file_{i}.txt')
            with open(file_path, 'w') as f:
                f.write(f'Test content for file {i}\n' * (i + 1))
            created_files.append(file_path)

        return created_files

    @staticmethod
    def create_test_directories(base_path: str, names: List[str]) -> List[str]:
        """Create test directories."""
        created_dirs = []
        for name in names:
            dir_path = os.path.join(base_path, name)
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_path)

        return created_dirs

    @staticmethod
    def cleanup_test_files(paths: List[str]):
        """Clean up test files and directories."""
        for path in paths:
            if os.path.exists(path):
                if os.path.isdir(path):
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)


# ============================================================================
# Performance Test Helpers
# ============================================================================

class PerformanceTestHelper:
    """Helper class for performance testing operations."""

    @staticmethod
    def measure_execution_time(func, *args, **kwargs) -> tuple:
        """Measure execution time of a function."""
        import time

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time
        return result, execution_time

    @staticmethod
    def measure_memory_usage(func, *args, **kwargs) -> tuple:
        """Measure memory usage of a function."""
        import psutil
        import gc

        process = psutil.Process()
        start_memory = process.memory_info().rss

        gc.collect()  # Force garbage collection

        result = func(*args, **kwargs)

        end_memory = process.memory_info().rss
        memory_delta = end_memory - start_memory

        return result, memory_delta

    @staticmethod
    def generate_load_test_data(size_mb: float = 1.0) -> bytes:
        """Generate load test data of specified size."""
        target_size = int(size_mb * 1024 * 1024)  # Convert MB to bytes
        chunk_size = 1024  # 1KB chunks
        chunks_needed = target_size // chunk_size

        data = b''
        for i in range(chunks_needed):
            data += f'Load test chunk {i}\n'.encode() * (chunk_size // 50)

        return data[:target_size]


# ============================================================================
# Test Configuration Helpers
# ============================================================================

class TestConfigHelper:
    """Helper class for test configuration management."""

    @staticmethod
    def get_test_env_vars() -> Dict[str, str]:
        """Get test environment variables."""
        return {
            'CONGRESS_API_KEY': 'test_congress_key_12345',
            'OPENSTATES_API_KEY': 'test_openstates_key_67890',
            'GOVINFO_API_KEY': 'test_govinfo_key_abcdef',
            'DB_NAME': 'opendiscourse_test',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_password',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'TEST_MODE': 'true',
            'LOG_LEVEL': 'DEBUG',
            'CACHE_ENABLED': 'false'
        }

    @staticmethod
    def setup_test_environment(test_env_vars: Dict[str, str] = None):
        """Setup test environment."""
        if test_env_vars is None:
            test_env_vars = TestConfigHelper.get_test_env_vars()

        # Set environment variables
        for key, value in test_env_vars.items():
            os.environ[key] = value

        # Create temporary directories
        temp_dir = tempfile.mkdtemp(prefix='opendiscourse_test_')
        os.environ['TEMP_DIR'] = temp_dir

        return temp_dir

    @staticmethod
    def cleanup_test_environment(temp_dir: str = None):
        """Cleanup test environment."""
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

        # Clear test environment variables
        test_vars = TestConfigHelper.get_test_env_vars()
        for key in test_vars.keys():
            if key in os.environ:
                del os.environ[key]

        if 'TEMP_DIR' in os.environ:
            del os.environ['TEMP_DIR']


# ============================================================================
# Custom Test Markers and Decorators
# ============================================================================

def skip_if_no_database(func):
    """Decorator to skip tests if database is not available."""
    import pytest

    def wrapper(*args, **kwargs):
        if not os.getenv('TEST_DATABASE_AVAILABLE', 'false').lower() == 'true':
            pytest.skip("Test database not available")
        return func(*args, **kwargs)

    return wrapper


def skip_if_no_api_keys(func):
    """Decorator to skip tests if API keys are not available."""
    import pytest

    def wrapper(*args, **kwargs):
        required_keys = ['CONGRESS_API_KEY', 'OPENSTATES_API_KEY', 'GOVINFO_API_KEY']
        missing_keys = [key for key in required_keys if not os.getenv(key)]

        if missing_keys:
            pytest.skip(f"Missing API keys: {', '.join(missing_keys)}")
        return func(*args, **kwargs)

    return wrapper


def measure_performance(threshold_seconds: float = 1.0):
    """Decorator to measure and report test performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result, exec_time = PerformanceTestHelper.measure_execution_time(func, *args, **kwargs)

            if exec_time > threshold_seconds:
                print(f"⚠️  Performance Warning: {func.__name__} took {exec_time:.2f}s (threshold: {threshold_seconds}s)")

            return result
        return wrapper
    return decorator


# ============================================================================
# Utility Functions
# ============================================================================

def assert_dict_contains_subset(subset: Dict[str, Any], superset: Dict[str, Any]):
    """Assert that subset dictionary is contained in superset dictionary."""
    for key, value in subset.items():
        if key not in superset:
            raise AssertionError(f"Key '{key}' not found in superset")
        if superset[key] != value:
            raise AssertionError(f"Value mismatch for key '{key}': expected '{value}', got '{superset[key]}'")


def create_mock_datetime(year: int = 2024, month: int = 1, day: int = 15,
                        hour: int = 12, minute: int = 30, second: int = 0) -> datetime:
    """Create a mock datetime for testing."""
    return datetime(year, month, day, hour, minute, second)


def generate_test_uuid() -> str:
    """Generate a test UUID."""
    return str(uuid.uuid4())


def validate_test_data_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate test data against a schema definition."""
    for field, field_type in schema.items():
        if field not in data:
            return False

        actual_type = type(data[field])
        expected_type = field_type

        if expected_type == 'datetime' and not isinstance(data[field], datetime):
            return False
        elif expected_type == 'uuid' and not isinstance(data[field], str):
            return False
        elif expected_type != 'datetime' and expected_type != 'uuid' and not isinstance(data[field], expected_type):
            return False

    return True


# Export commonly used functions and classes
__all__ = [
    'DatabaseTestHelper',
    'APITestHelper',
    'FileSystemTestHelper',
    'PerformanceTestHelper',
    'TestConfigHelper',
    'assert_dict_contains_subset',
    'create_mock_datetime',
    'generate_test_uuid',
    'validate_test_data_schema'
]
