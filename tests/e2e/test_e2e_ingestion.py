# tests/e2e/test_e2e_ingestion.py

import subprocess
import os
import pytest

# Path to the ingestion script
# Assumes this test file is in tests/e2e/ and the script is in scripts/
SCRIPT_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'scripts', 'ingest_members_official.py'
)

@pytest.mark.e2e
def test_ingestion_happy_path(db_cursor, mock_successful_api, db_connection_params):
    """
    Tests the complete ingestion process on a "happy path" scenario.
    - Mocks a successful API response.
    - Runs the ingestion script.
    - Verifies that the correct data is inserted into the database.
    """
    # Arrange: Define script arguments
    congress_num = "116"
    args = [
        "python", SCRIPT_PATH,
        "--congress-start", congress_num,
        "--congress-end", congress_num,
        "--batch-size", "10",
        # Point the script to the test database
        "--db-name", db_connection_params['database'],
        "--db-user", db_connection_params['user'],
        "--db-password", db_connection_params['password'],
        "--db-host", db_connection_params['host'],
        "--db-port", str(db_connection_params['port']),
    ]

    # Act: Run the ingestion script
    result = subprocess.run(args, capture_output=True, text=True, check=False)

    # Assert: Script execution
    assert result.returncode == 0, f"Script failed to execute: {result.stderr}"
    assert "Ingestion complete" in result.stdout, "Script should indicate completion."

    # Assert: Database state
    # 1. Check members table
    db_cursor.execute("SELECT * FROM congress.members ORDER BY bioguide_id;")
    members = db_cursor.fetchall()
    assert len(members) == 3
    assert members[0]['bioguide_id'] == 'A000360'
    assert members[1]['bioguide_id'] == 'B001230'
    assert members[2]['bioguide_id'] == 'M001111'
    assert members[0]['first_name'] == 'Lamar'

    # 2. Check member_terms table
    db_cursor.execute("SELECT * FROM congress.member_terms ORDER BY bioguide_id;")
    terms = db_cursor.fetchall()
    assert len(terms) == 3
    assert terms[0]['bioguide_id'] == 'A000360'
    assert terms[0]['congress_number'] == 116
    assert terms[0]['party_code'] == 'R'
    assert terms[1]['state_code'] == 'WI'
    assert terms[2]['chamber_code'] == 'House'
    assert terms[2]['district'] == '2'

@pytest.mark.e2e
def test_ingestion_handles_api_failure(db_cursor, mock_failed_api, db_connection_params):
    """
    Tests that the ingestion script exits gracefully when the API returns an error.
    """
    # Arrange
    args = [
        "python", SCRIPT_PATH,
        "--congress-start", "116", "--congress-end", "116",
        "--db-name", db_connection_params['database'],
        "--db-user", db_connection_params['user'],
        "--db-password", db_connection_params['password'],
        "--db-host", db_connection_params['host'],
        "--db-port", str(db_connection_params['port']),
    ]

    # Act
    result = subprocess.run(args, capture_output=True, text=True, check=False)

    # Assert: Script should fail
    assert result.returncode != 0, "Script should exit with a non-zero code on API failure."
    assert "Failed to fetch data" in result.stderr or "500 Server Error" in result.stderr

    # Assert: No data should be inserted
    db_cursor.execute("SELECT COUNT(*) as count FROM congress.members;")
    count = db_cursor.fetchone()['count']
    assert count == 0, "No data should be ingested on API failure."

@pytest.mark.e2e
def test_ingestion_idempotency(db_cursor, mock_successful_api, db_connection_params):
    """
    Tests that running the ingestion script multiple times does not create duplicate data.
    """
    # Arrange
    args = [
        "python", SCRIPT_PATH,
        "--congress-start", "116", "--congress-end", "116",
        "--db-name", db_connection_params['database'],
        "--db-user", db_connection_params['user'],
        "--db-password", db_connection_params['password'],
        "--db-host", db_connection_params['host'],
        "--db-port", str(db_connection_params['port']),
    ]

    # Act: Run ingestion twice
    first_run = subprocess.run(args, capture_output=True, text=True, check=False)
    assert first_run.returncode == 0, f"First run failed: {first_run.stderr}"
    
    second_run = subprocess.run(args, capture_output=True, text=True, check=False)
    assert second_run.returncode == 0, f"Second run failed: {second_run.stderr}"

    # Assert: Check counts to ensure no duplicates were added
    db_cursor.execute("SELECT COUNT(*) as count FROM congress.members;")
    member_count = db_cursor.fetchone()['count']
    assert member_count == 3

    db_cursor.execute("SELECT COUNT(*) as count FROM congress.member_terms;")
    term_count = db_cursor.fetchone()['count']
    assert term_count == 3
