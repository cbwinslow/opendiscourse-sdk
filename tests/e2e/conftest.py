# tests/e2e/conftest.py

import pytest
import os
import psycopg2
import json
from psycopg2.extras import DictCursor

# --- Database Fixtures ---

@pytest.fixture(scope="session")
def db_connection_params():
    """Provides database connection parameters from environment variables."""
    return {
        'database': os.getenv('DB_NAME_TEST', 'opendiscourse_test'),
        'user': os.getenv('DB_USER_TEST', 'test_user'),
        'password': os.getenv('DB_PASSWORD_TEST', 'test_password'),
        'host': os.getenv('DB_HOST_TEST', 'localhost'),
        'port': os.getenv('DB_PORT_TEST', '5433'),
    }

@pytest.fixture(scope="session")
def setup_test_database(db_connection_params):
    """
    Sets up a test database schema.
    This fixture has session scope, so it runs once per test session.
    """
    conn = psycopg2.connect(**{**db_connection_params, 'database': 'postgres'})
    conn.autocommit = True
    cursor = conn.cursor()
    
    db_name = db_connection_params['database']
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name};")
    cursor.execute(f"CREATE DATABASE {db_name};")
    
    conn.close()

    # Connect to the new database to create schema
    conn = psycopg2.connect(**db_connection_params)
    cursor = conn.cursor()
    
    # Minimal schema required for ingestion script
    cursor.execute("""
        CREATE SCHEMA IF NOT EXISTS congress;

        CREATE TABLE IF NOT EXISTS congress.members (
            bioguide_id VARCHAR(10) PRIMARY KEY,
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            birth_year INT,
            death_year INT
        );

        CREATE TABLE IF NOT EXISTS congress.member_terms (
            id SERIAL PRIMARY KEY,
            bioguide_id VARCHAR(10) REFERENCES congress.members(bioguide_id),
            congress_number INT,
            chamber_code VARCHAR(10),
            start_date DATE,
            end_date DATE,
            state_code VARCHAR(2),
            district VARCHAR(10),
            party_code VARCHAR(5)
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()

    yield # Tests run here

    # Teardown: handled by dropping the database at the start of the next run

@pytest.fixture
def db_cursor(setup_test_database, db_connection_params):
    """
    Provides a transactional database cursor for each test function.
    It cleans up tables before each test to ensure isolation.
    """
    conn = psycopg2.connect(**db_connection_params)
    conn.cursor_factory = DictCursor
    cursor = conn.cursor()

    # Truncate tables for test isolation
    cursor.execute("TRUNCATE TABLE congress.member_terms, congress.members RESTART IDENTITY CASCADE;")
    conn.commit()

    yield cursor

    conn.rollback() # Rollback any changes made during the test
    cursor.close()
    conn.close()


# --- API Mocking Fixtures ---

@pytest.fixture
def mock_api_response():
    """Loads sample API response from a file."""
    path = os.path.join(os.path.dirname(__file__), 'sample_member_api_response.json')
    with open(path, 'r') as f:
        return json.load(f)

@pytest.fixture
def mock_successful_api(mocker, mock_api_response):
    """Mocks requests.get to return a successful response."""
    mock_get = mocker.patch('requests.get')
    
    # Mock the response object
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_api_response
    
    mock_get.return_value = mock_response
    return mock_get

@pytest.fixture
def mock_failed_api(mocker):
    """Mocks requests.get to return a 500 server error."""
    mock_get = mocker.patch('requests.get')

    mock_response = mocker.Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"message": "Internal Server Error"}
    mock_response.raise_for_status.side_effect = psycopg2.HTTPError("500 Server Error")
    
    mock_get.return_value = mock_response
    return mock_get

@pytest.fixture
def mock_rate_limit_api(mocker):
    """Mocks requests.get to return a 429 rate limit error."""
    mock_get = mocker.patch('requests.get')

    mock_response = mocker.Mock()
    mock_response.status_code = 429
    mock_response.json.return_value = {"message": "Rate limit exceeded"}
    mock_response.raise_for_status.side_effect = psycopg2.HTTPError("429 Rate Limit")
    
    mock_get.return_value = mock_response
    return mock_get
