"""
================================================================================
File: test_output_formatters.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Version: 1.0.0

Description:
    Tests for output formatters including JSON, JSONL, CSV, and SQLite.

================================================================================
"""

import pytest
import json
import csv
import sqlite3
import tempfile
from pathlib import Path

from scripts.core.output_formatters import (
    OutputFormat,
    FormatterFactory,
    JSONFormatter,
    JSONLFormatter,
    CSVFormatter,
    SQLiteFormatter
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_data():
    """Sample data for testing."""
    return [
        {"id": 1, "name": "Bill A", "status": "passed"},
        {"id": 2, "name": "Bill B", "status": "pending"},
        {"id": 3, "name": "Bill C", "status": "failed"},
    ]


@pytest.fixture
def temp_file():
    """Create temporary file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as f:
        path = Path(f.name)

    yield path

    # Cleanup
    if path.exists():
        path.unlink()
    # Also clean up compressed version
    if path.with_suffix(path.suffix + '.gz').exists():
        path.with_suffix(path.suffix + '.gz').unlink()


# ============================================================================
# JSON Formatter Tests
# ============================================================================

def test_json_formatter_basic(sample_data, temp_file):
    """Test basic JSON formatting."""
    formatter = JSONFormatter(destination=temp_file)
    formatter.write(sample_data)

    # Read and verify
    with open(temp_file) as f:
        result = json.load(f)

    assert len(result) == 3
    assert result[0]["name"] == "Bill A"


def test_json_formatter_with_indent(sample_data, temp_file):
    """Test JSON with custom indentation."""
    formatter = JSONFormatter(destination=temp_file, indent=4)
    formatter.write(sample_data)

    # Read content
    content = temp_file.read_text()

    # Should have newlines (pretty-printed)
    assert '\n' in content


# ============================================================================
# JSONL Formatter Tests
# ============================================================================

def test_jsonl_formatter_basic(sample_data, temp_file):
    """Test JSONL formatting."""
    formatter = JSONLFormatter(destination=temp_file)
    formatter.write(sample_data)

    # Read and verify (one JSON object per line)
    lines = temp_file.read_text().strip().split('\n')

    assert len(lines) == 3

    # Parse each line
    for i, line in enumerate(lines):
        obj = json.loads(line)
        assert obj["id"] == i + 1


def test_jsonl_formatter_batch(sample_data, temp_file):
    """Test JSONL batch writing (appending)."""
    formatter = JSONLFormatter(destination=temp_file)

    # Write in batches
    formatter.write_batch(sample_data[:2])
    formatter.write_batch(sample_data[2:])

    # Read all lines
    lines = temp_file.read_text().strip().split('\n')

    assert len(lines) == 3


# ============================================================================
# CSV Formatter Tests
# ============================================================================

def test_csv_formatter_basic(sample_data, temp_file):
    """Test CSV formatting."""
    csv_file = temp_file.with_suffix('.csv')
    formatter = CSVFormatter(destination=csv_file)
    formatter.write(sample_data)

    # Read and verify
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3
    assert rows[0]["name"] == "Bill A"

    csv_file.unlink()


def test_csv_formatter_headers(sample_data, temp_file):
    """Test that CSV includes headers."""
    csv_file = temp_file.with_suffix('.csv')
    formatter = CSVFormatter(destination=csv_file)
    formatter.write(sample_data)

    # Read first line
    with open(csv_file) as f:
        first_line = f.readline()

    assert "id" in first_line
    assert "name" in first_line
    assert "status" in first_line

    csv_file.unlink()


def test_csv_formatter_batch(sample_data, temp_file):
    """Test CSV batch writing."""
    csv_file = temp_file.with_suffix('.csv')
    formatter = CSVFormatter(destination=csv_file)

    # Write in batches
    formatter.write_batch(sample_data[:2])
    formatter.write_batch(sample_data[2:])

    # Read all rows
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 3

    csv_file.unlink()


# ============================================================================
# SQLite Formatter Tests
# ============================================================================

def test_sqlite_formatter_basic(sample_data, temp_file):
    """Test SQLite formatting."""
    db_file = temp_file.with_suffix('.db')
    formatter = SQLiteFormatter(destination=db_file, table_name="bills")
    formatter.write(sample_data)

    # Verify data in database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills")
    rows = cursor.fetchall()
    conn.close()

    assert len(rows) == 3

    db_file.unlink()


def test_sqlite_formatter_table_name(sample_data, temp_file):
    """Test custom table name."""
    db_file = temp_file.with_suffix('.db')
    formatter = SQLiteFormatter(destination=db_file, table_name="my_table")
    formatter.write(sample_data)

    # Check table exists
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()

    assert ("my_table",) in tables

    db_file.unlink()


def test_sqlite_formatter_batch(sample_data, temp_file):
    """Test SQLite batch writing (append)."""
    db_file = temp_file.with_suffix('.db')
    formatter = SQLiteFormatter(destination=db_file, table_name="bills")

    # Write in batches
    formatter.write(sample_data[:2])
    formatter.write_batch(sample_data[2:])  # Append

    # Check total count
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM bills")
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 3

    db_file.unlink()


# ============================================================================
# Factory Tests
# ============================================================================

def test_factory_create_json():
    """Test factory creating JSON formatter."""
    formatter = FormatterFactory.create(
        format=OutputFormat.JSON,
        destination="test.json"
    )

    assert isinstance(formatter, JSONFormatter)


def test_factory_create_jsonl():
    """Test factory creating JSONL formatter."""
    formatter = FormatterFactory.create(
        format=OutputFormat.JSONL,
        destination="test.jsonl"
    )

    assert isinstance(formatter, JSONLFormatter)


def test_factory_create_csv():
    """Test factory creating CSV formatter."""
    formatter = FormatterFactory.create(
        format=OutputFormat.CSV,
        destination="test.csv"
    )

    assert isinstance(formatter, CSVFormatter)


def test_factory_create_sqlite():
    """Test factory creating SQLite formatter."""
    formatter = FormatterFactory.create(
        format=OutputFormat.SQLITE,
        destination="test.db",
        table_name="data"
    )

    assert isinstance(formatter, SQLiteFormatter)


def test_factory_unsupported_format():
    """Test error with unsupported format."""
    with pytest.raises(ValueError):
        FormatterFactory.create(
            format="unsupported",
            destination="test.txt"
        )


# ============================================================================
# Edge Cases
# ============================================================================

def test_empty_data_json(temp_file):
    """Test handling empty data with JSON."""
    formatter = JSONFormatter(destination=temp_file)
    formatter.write([])

    # Should create empty array
    with open(temp_file) as f:
        result = json.load(f)

    assert result == []


def test_empty_data_csv(temp_file):
    """Test handling empty data with CSV."""
    csv_file = temp_file.with_suffix('.csv')
    formatter = CSVFormatter(destination=csv_file)
    formatter.write([])

    # Should not crash (warning logged)
    assert True

    if csv_file.exists():
        csv_file.unlink()


def test_nested_data_json(temp_file):
    """Test handling nested data structures."""
    nested_data = [
        {
            "id": 1,
            "details": {
                "sponsor": "John Doe",
                "votes": [10, 20, 30]
            }
        }
    ]

    formatter = JSONFormatter(destination=temp_file)
    formatter.write(nested_data)

    # Read and verify structure preserved
    with open(temp_file) as f:
        result = json.load(f)

    assert result[0]["details"]["sponsor"] == "John Doe"
    assert result[0]["details"]["votes"] == [10, 20, 30]
