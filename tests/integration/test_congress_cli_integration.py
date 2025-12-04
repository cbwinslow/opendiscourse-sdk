import pytest
from unittest.mock import MagicMock, patch
from scripts.ingestion.congress_cli import CongressCLI

@pytest.fixture
def mock_cli():
    with patch('scripts.ingestion.congress_cli.psycopg2.connect') as mock_connect:
        cli = CongressCLI(api_key="test_key", dry_run=True)
        cli.conn = mock_connect.return_value
        yield cli

def test_worker_pool_initialization(mock_cli):
    assert mock_cli.worker_pool is not None
    assert mock_cli.worker_pool.num_workers == 4

@patch('scripts.ingestion.congress_cli.CongressCLI.get')
def test_ingest_bill_details_parallel(mock_get, mock_cli):
    # Mock DB cursor for fetching bills
    mock_cursor = mock_cli.conn.cursor.return_value
    mock_cursor.fetchall.return_value = [('HR', 1), ('HR', 2), ('S', 1)]

    # Mock API response
    mock_get.return_value = {
        'actions': [
            {'actionDate': '2023-01-01', 'text': 'Introduced', 'type': 'Intro', 'actionCode': '1000'}
        ]
    }

    # Run ingestion
    mock_cli.ingest_bill_details(118, 'actions')

    # Verify get was called (by workers)
    # Since workers run in threads, call count might be tricky if we don't wait,
    # but WorkerPool.run() waits for completion.
    assert mock_get.call_count == 3

    # Verify insert was called (dry run prints, but we can check logic flow)
    # In dry run, we don't execute insert, but we print.
    # To test insert logic, we'd need to mock dry_run=False or check logs.
    # For now, verifying that it ran without error and called get 3 times is good.

def test_deduplication_engine_initialization(mock_cli):
    assert mock_cli.deduplication is not None
