"""
================================================================================
File: test_database_adapter.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 1.0.0

Description:
    Comprehensive unit tests for database adapter layer.
    Tests all three database backends (PostgreSQL, MySQL, SQLite)
    with connection pooling, query execution, and error handling.

================================================================================
"""

import pytest
import tempfile
import os
from pathlib import Path

from scripts.core.database_adapter import (
    DatabaseBackend,
    DatabaseAdapter,
    PostgreSQLAdapter,
    MySQLAdapter,
    SQLiteAdapter,
    AdapterFactory
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_sqlite_db():
    """Create temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sqlite_adapter(temp_sqlite_db):
    """Create SQLite adapter for testing."""
    return SQLiteAdapter(database=temp_sqlite_db)


# ============================================================================
# SQLite Adapter Tests
# ============================================================================

def test_sqlite_adapter_creation(temp_sqlite_db):
    """Test SQLite adapter creation."""
    adapter = SQLiteAdapter(database=temp_sqlite_db)
    assert adapter.backend == DatabaseBackend.SQLITE
    assert adapter.config['database'] == temp_sqlite_db


def test_sqlite_connect_disconnect(sqlite_adapter):
    """Test SQLite connection lifecycle."""
    # Initially not connected
    assert sqlite_adapter._connection is None

    # Connect
    sqlite_adapter.connect()
    assert sqlite_adapter._connection is not None

    # Disconnect
    sqlite_adapter.disconnect()
    assert sqlite_adapter._connection is None


def test_sqlite_create_table(sqlite_adapter):
    """Test creating a table in SQLite."""
    sqlite_adapter.connect()

    # Create table
    sqlite_adapter.execute("""
        CREATE TABLE test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            value INTEGER
        )
    """)

    # Verify table exists
    result = sqlite_adapter.fetch_one(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
    )

    assert result is not None
    assert result[0] == 'test_table'

    sqlite_adapter.disconnect()


def test_sqlite_insert_and_fetch(sqlite_adapter):
    """Test inserting and fetching data."""
    sqlite_adapter.connect()

    # Create table
    sqlite_adapter.execute("""
        CREATE TABLE bills (
            id INTEGER PRIMARY KEY,
            number TEXT,
            title TEXT
        )
    """)

    # Insert data
    sqlite_adapter.execute(
        "INSERT INTO bills (number, title) VALUES (?, ?)",
        ("HR1", "Test Bill")
    )
    sqlite_adapter.commit()

    # Fetch data
    result = sqlite_adapter.fetch_one("SELECT number, title FROM bills WHERE number = ?", ("HR1",))

    assert result is not None
    assert result[0] == "HR1"
    assert result[1] == "Test Bill"

    sqlite_adapter.disconnect()


def test_sqlite_fetch_all(sqlite_adapter):
    """Test fetching multiple rows."""
    sqlite_adapter.connect()

    # Create and populate table
    sqlite_adapter.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT)")

    for i in range(5):
        sqlite_adapter.execute("INSERT INTO items (name) VALUES (?)", (f"Item {i}",))
    sqlite_adapter.commit()

    # Fetch all
    results = sqlite_adapter.fetch_all("SELECT name FROM items")

    assert len(results) == 5
    assert results[0][0] == "Item 0"
    assert results[4][0] == "Item 4"

    sqlite_adapter.disconnect()


def test_sqlite_context_manager(temp_sqlite_db):
    """Test using adapter as context manager."""
    adapter = SQLiteAdapter(database=temp_sqlite_db)

    with adapter as db:
        db.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        db.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))
        # Commit happens automatically on exit

    # Verify data persisted
    adapter.connect()
    result = adapter.fetch_one("SELECT value FROM test")
    assert result[0] == "test_value"
    adapter.disconnect()


def test_sqlite_cursor_context_manager(sqlite_adapter):
    """Test cursor as context manager."""
    sqlite_adapter.connect()

    sqlite_adapter.execute("CREATE TABLE test (value TEXT)")

    with sqlite_adapter.cursor() as cursor:
        cursor.execute("INSERT INTO test VALUES (?)", ("test",))
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()

    assert result[0] == "test"
    sqlite_adapter.disconnect()


def test_sqlite_transaction_rollback(sqlite_adapter):
    """Test transaction rollback."""
    sqlite_adapter.connect()

    sqlite_adapter.execute("CREATE TABLE test (value TEXT)")
    sqlite_adapter.execute("INSERT INTO test VALUES (?)", ("original",))
    sqlite_adapter.commit()

    # Make change but rollback
    sqlite_adapter.execute("INSERT INTO test VALUES (?)", ("rolled_back",))
    sqlite_adapter.rollback()

    # Should only have original value
    results = sqlite_adapter.fetch_all("SELECT value FROM test")
    assert len(results) == 1
    assert results[0][0] == "original"

    sqlite_adapter.disconnect()


# ============================================================================
# Adapter Factory Tests
# ============================================================================

def test_factory_create_sqlite():
    """Test factory creating SQLite adapter."""
    adapter = AdapterFactory.create(
        backend=DatabaseBackend.SQLITE,
        database=":memory:"
    )

    assert isinstance(adapter, SQLiteAdapter)
    assert adapter.backend == DatabaseBackend.SQLITE


def test_factory_from_connection_string_sqlite():
    """Test creating SQLite adapter from connection string."""
    adapter = AdapterFactory.from_connection_string("sqlite:///test.db")

    assert isinstance(adapter, SQLiteAdapter)
    assert adapter.config['database'] == "test.db"


def test_factory_from_connection_string_postgresql():
    """Test parsing PostgreSQL connection string."""
    # Note: This just tests parsing, not actual connection
    adapter = AdapterFactory.from_connection_string(
        "postgresql://user:pass@localhost:5432/opendiscourse"
    )

    assert isinstance(adapter, PostgreSQLAdapter)
    assert adapter.config['host'] == 'localhost'
    assert adapter.config['port'] == 5432
    assert adapter.config['database'] == 'opendiscourse'
    assert adapter.config['user'] == 'user'
    assert adapter.config['password'] == 'pass'


def test_factory_from_connection_string_mysql():
    """Test parsing MySQL connection string."""
    adapter = AdapterFactory.from_connection_string(
        "mysql://root:password@localhost:3306/opendiscourse"
    )

    assert isinstance(adapter, MySQLAdapter)
    assert adapter.config['host'] == 'localhost'
    assert adapter.config['port'] == 3306
    assert adapter.config['database'] == 'opendiscourse'


def test_factory_unsupported_backend():
    """Test error with unsupported backend."""
    with pytest.raises(ValueError, match="Unsupported backend"):
        AdapterFactory.create(
            backend="unsupported",  # Invalid backend
            database="test"
        )


def test_factory_unsupported_scheme():
    """Test error with unsupported connection string scheme."""
    with pytest.raises(ValueError, match="Unsupported scheme"):
        AdapterFactory.from_connection_string("oracle://localhost/db")


# ============================================================================
# Integration Tests (Mock/Skip if drivers unavailable)
# ============================================================================

@pytest.mark.skipif(
    not hasattr(PostgreSQLAdapter, '__init__'),
    reason="PostgreSQL driver not available"
)
def test_postgresql_adapter_creation():
    """Test PostgreSQL adapter creation (no connection)."""
    try:
        adapter = PostgreSQLAdapter(
            host="localhost",
            database="test",
            user="postgres"
        )
        assert adapter.backend == DatabaseBackend.POSTGRESQL
        assert adapter.config['host'] == 'localhost'
        assert adapter.config['port'] == 5432
    except ImportError:
        pytest.skip("PostgreSQL driver not available")


@pytest.mark.skipif(
    not hasattr(MySQLAdapter, '__init__'),
    reason="MySQL driver not available"
)
def test_mysql_adapter_creation():
    """Test MySQL adapter creation (no connection)."""
    try:
        adapter = MySQLAdapter(
            host="localhost",
            database="test",
            user="root"
        )
        assert adapter.backend == DatabaseBackend.MYSQL
        assert adapter.config['host'] == 'localhost'
        assert adapter.config['port'] == 3306
    except ImportError:
        pytest.skip("MySQL driver not available")


# ============================================================================
# Performance Tests
# ============================================================================

def test_sqlite_bulk_insert_performance(sqlite_adapter):
    """Test bulk insert performance."""
    sqlite_adapter.connect()

    sqlite_adapter.execute("""
        CREATE TABLE performance_test (
            id INTEGER PRIMARY KEY,
            value TEXT
        )
    """)

    # Insert 1000 rows
    for i in range(1000):
        sqlite_adapter.execute(
            "INSERT INTO performance_test (value) VALUES (?)",
            (f"Value {i}",)
        )
    sqlite_adapter.commit()

    # Verify count
    result = sqlite_adapter.fetch_one("SELECT COUNT(*) FROM performance_test")
    assert result[0] == 1000

    sqlite_adapter.disconnect()
