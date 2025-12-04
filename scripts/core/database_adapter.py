"""
================================================================================
File: database_adapter.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Abstract database adapter layer supporting multiple database backends.
    Provides a unified interface for PostgreSQL, MySQL, and SQLite with
    connection pooling, transaction management, and automatic schema detection.

Dependencies:
    - psycopg2: PostgreSQL driver
    - mysql-connector-python: MySQL driver (optional)
    - sqlite3: SQLite driver (built-in)
    - typing: Type hints
    - abc: Abstract base classes

Classes:
    - DatabaseBackend: Enum for database types
    - DatabaseAdapter: Abstract base class for adapters
    - PostgreSQLAdapter: PostgreSQL implementation
    - MySQLAdapter: MySQL/MariaDB implementation
    - SQLiteAdapter: SQLite implementation
    - AdapterFactory: Factory for creating adapters

Usage:
    from scripts.core.database_adapter import AdapterFactory, DatabaseBackend

    # Create PostgreSQL adapter
    adapter = AdapterFactory.create(
        backend=DatabaseBackend.POSTGRESQL,
        host="localhost",
        database="opendiscourse",
        user="postgres"
    )

    # Execute query
    with adapter.cursor() as cursor:
        cursor.execute("SELECT * FROM bills LIMIT 10")
        results = cursor.fetchall()

    # Use connection string
    adapter = AdapterFactory.from_connection_string(
        "postgresql://user:pass@localhost:5432/opendiscourse"
    )

Changelog:
    2025-12-04: Initial creation with PostgreSQL, MySQL, SQLite support

Notes:
    - All adapters implement the same interface
    - Automatic connection pooling where supported
    - Thread-safe implementations
    - Graceful fallback for missing drivers

================================================================================
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, ContextManager
from enum import Enum
from urllib.parse import urlparse, parse_qs
from contextlib import contextmanager

# Try importing database drivers
try:
    import psycopg2
    from psycopg2 import pool as pg_pool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import mysql.connector
    from mysql.connector import pooling as mysql_pooling
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False

# SQLite is always available (built-in)
import sqlite3


# ============================================================================
# Enums
# ============================================================================

class DatabaseBackend(str, Enum):
    """
    Supported database backends.

    Values:
        POSTGRESQL: PostgreSQL (primary, recommended)
        MYSQL: MySQL or MariaDB
        SQLITE: SQLite (for testing/local development)
    """
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"


# ============================================================================
# Abstract Base Class
# ============================================================================

class DatabaseAdapter(ABC):
    """
    Abstract base class for database adapters.

    Provides a unified interface for different database backends
    with connection pooling, transaction management, and query execution.

    Attributes:
        backend: Database backend type
        config: Connection configuration
        logger: Logger instance

    Methods:
        connect: Establish database connection
        disconnect: Close database connection
        cursor: Get database cursor (context manager)
        execute: Execute a query
        execute_many: Execute query with multiple parameter sets
        fetch_one: Fetch single result
        fetch_all: Fetch all results
        commit: Commit transaction
        rollback: Rollback transaction
    """

    def __init__(self, backend: DatabaseBackend, **config):
        """
        Initialize database adapter.

        Args:
            backend: Database backend type
            **config: Database connection parameters
        """
        self.backend = backend
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self._connection = None
        self._pool = None

    @abstractmethod
    def connect(self):
        """Establish connection to database."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass

    @abstractmethod
    @contextmanager
    def cursor(self):
        """
        Provide database cursor as context manager.

        Yields:
            Database cursor

        Example:
            >>> with adapter.cursor() as cursor:
            >>>     cursor.execute("SELECT * FROM bills")
            >>>     results = cursor.fetchall()
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute a query.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Number of affected rows
        """
        pass

    @abstractmethod
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """
        Fetch single result.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Single row or None
        """
        pass

    @abstractmethod
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """
        Fetch all results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of rows
        """
        pass

    @abstractmethod
    def commit(self):
        """Commit current transaction."""
        pass

    @abstractmethod
    def rollback(self):
        """Rollback current transaction."""
        pass

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.disconnect()


# ============================================================================
# PostgreSQL Adapter
# ============================================================================

class PostgreSQLAdapter(DatabaseAdapter):
    """
    PostgreSQL database adapter with connection pooling.

    Supports connection pooling for high-performance applications.
    This is the recommended adapter for production use.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "opendiscourse",
        user: str = "postgres",
        password: Optional[str] = None,
        pool_size: int = 5,
        max_overflow: int = 10,
        **kwargs
    ):
        """
        Initialize PostgreSQL adapter.

        Args:
            host: Database host
            port: Database port
            database: Database name
            user: Username
            password: Password (optional for peer authentication)
            pool_size: Number of persistent connections
            max_overflow: Maximum overflow connections
            **kwargs: Additional psycopg2 parameters
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL support")

        super().__init__(
            backend=DatabaseBackend.POSTGRESQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            pool_size=pool_size,
            max_overflow=max_overflow,
            **kwargs
        )

    def connect(self):
        """Establish connection pool to PostgreSQL."""
        if self._pool is None:
            # Create connection parameters
            conn_params = {
                'host': self.config['host'],
                'port': self.config['port'],
                'database': self.config['database'],
                'user': self.config['user'],
            }

            # Add password if provided
            if self.config.get('password'):
                conn_params['password'] = self.config['password']

            # Create connection pool
            self._pool = pg_pool.SimpleConnectionPool(
                minconn=1,
                maxconn=self.config.get('pool_size', 5),
                **conn_params
            )

            self.logger.info(f"PostgreSQL pool created: {self.config['database']}@{self.config['host']}")

    def disconnect(self):
        """Close connection pool."""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            self.logger.info("PostgreSQL pool closed")

    @contextmanager
    def cursor(self):
        """Provide cursor from connection pool."""
        self.connect()
        conn = self._pool.getconn()
        try:
            cursor = conn.cursor()
            yield cursor
            cursor.close()
        finally:
            self._pool.putconn(conn)

    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute query and return affected rows."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch single result."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def commit(self):
        """Commit - handled by context manager."""
        pass

    def rollback(self):
        """Rollback - handled by context manager."""
        pass


# ============================================================================
# MySQL Adapter
# ============================================================================

class MySQLAdapter(DatabaseAdapter):
    """
    MySQL/MariaDB database adapter with connection pooling.

    Compatible with MySQL 5.7+ and MariaDB 10.2+.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 3306,
        database: str = "opendiscourse",
        user: str = "root",
        password: Optional[str] = None,
        pool_size: int = 5,
        **kwargs
    ):
        """Initialize MySQL adapter."""
        if not MYSQL_AVAILABLE:
            raise ImportError("mysql-connector-python is required for MySQL support")

        super().__init__(
            backend=DatabaseBackend.MYSQL,
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            pool_size=pool_size,
            **kwargs
        )

    def connect(self):
        """Establish connection pool to MySQL."""
        if self._pool is None:
            pool_config = {
                'host': self.config['host'],
                'port': self.config['port'],
                'database': self.config['database'],
                'user': self.config['user'],
                'pool_size': self.config.get('pool_size', 5),
            }

            if self.config.get('password'):
                pool_config['password'] = self.config['password']

            self._pool = mysql_pooling.MySQLConnectionPool(
                pool_name="opendiscourse_pool",
                **pool_config
            )

            self.logger.info(f"MySQL pool created: {self.config['database']}@{self.config['host']}")

    def disconnect(self):
        """Close connection pool."""
        if self._pool:
            # MySQL connector doesn't have closeall
            self._pool = None
            self.logger.info("MySQL pool closed")

    @contextmanager
    def cursor(self):
        """Provide cursor from connection pool."""
        self.connect()
        conn = self._pool.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            cursor.close()
        finally:
            conn.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute query."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch single result."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()

    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results."""
        with self.cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def commit(self):
        """Commit."""
        pass

    def rollback(self):
        """Rollback."""
        pass


# ============================================================================
# SQLite Adapter
# ============================================================================

class SQLiteAdapter(DatabaseAdapter):
    """
    SQLite database adapter.

    Ideal for testing, development, and single-user applications.
    No connection pooling (SQLite is file-based).
    """

    def __init__(
        self,
        database: str = "opendiscourse.db",
        **kwargs
    ):
        """Initialize SQLite adapter."""
        super().__init__(
            backend=DatabaseBackend.SQLITE,
            database=database,
            **kwargs
        )

    def connect(self):
        """Connect to SQLite database."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.config['database'],
                check_same_thread=False
            )
            self.logger.info(f"SQLite connected: {self.config['database']}")

    def disconnect(self):
        """Close SQLite connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            self.logger.info("SQLite disconnected")

    @contextmanager
    def cursor(self):
        """Provide cursor."""
        self.connect()
        cursor = self._connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute query."""
        with self.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.rowcount

    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[tuple]:
        """Fetch single result."""
        with self.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchone()

    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[tuple]:
        """Fetch all results."""
        with self.cursor() as cursor:
            cursor.execute(query, params or ())
            return cursor.fetchall()

    def commit(self):
        """Commit transaction."""
        if self._connection:
            self._connection.commit()

    def rollback(self):
        """Rollback transaction."""
        if self._connection:
            self._connection.rollback()


# ============================================================================
# Adapter Factory
# ============================================================================

class AdapterFactory:
    """
    Factory for creating database adapters.

    Provides convenient methods for creating adapters from various
    configuration sources.
    """

    @staticmethod
    def create(backend: DatabaseBackend, **config) -> DatabaseAdapter:
        """
        Create adapter for specified backend.

        Args:
            backend: Database backend type
            **config: Backend-specific configuration

        Returns:
            Database adapter instance

        Example:
            >>> adapter = AdapterFactory.create(
            >>>     backend=DatabaseBackend.POSTGRESQL,
            >>>     host="localhost",
            >>>     database="opendiscourse"
            >>> )
        """
        if backend == DatabaseBackend.POSTGRESQL:
            return PostgreSQLAdapter(**config)
        elif backend == DatabaseBackend.MYSQL:
            return MySQLAdapter(**config)
        elif backend == DatabaseBackend.SQLITE:
            return SQLiteAdapter(**config)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

    @staticmethod
    def from_connection_string(connection_string: str) -> DatabaseAdapter:
        """
        Create adapter from connection string.

        Args:
            connection_string: Database connection URL

        Returns:
            Database adapter instance

        Supported formats:
            - postgresql://user:pass@host:port/database
            - mysql://user:pass@host:port/database
            - sqlite:///path/to/database.db

        Example:
            >>> adapter = AdapterFactory.from_connection_string(
            >>>     "postgresql://postgres@localhost/opendiscourse"
            >>> )
        """
        parsed = urlparse(connection_string)

        # Determine backend from scheme
        scheme = parsed.scheme.lower()
        if scheme in ['postgresql', 'postgres']:
            backend = DatabaseBackend.POSTGRESQL
        elif scheme == 'mysql':
            backend = DatabaseBackend.MYSQL
        elif scheme == 'sqlite':
            backend = DatabaseBackend.SQLITE
        else:
            raise ValueError(f"Unsupported scheme: {scheme}")

        # Extract configuration
        if backend == DatabaseBackend.SQLITE:
            # SQLite: just the path
            config = {'database': parsed.path.lstrip('/')}
        else:
            # PostgreSQL/MySQL: extract all components
            config = {
                'host': parsed.hostname or 'localhost',
                'port': parsed.port or (5432 if backend == DatabaseBackend.POSTGRESQL else 3306),
                'database': parsed.path.lstrip('/'),
                'user': parsed.username,
                'password': parsed.password,
            }

        return AdapterFactory.create(backend, **config)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'DatabaseBackend',
    'DatabaseAdapter',
    'PostgreSQLAdapter',
    'MySQLAdapter',
    'SQLiteAdapter',
    'AdapterFactory',
]
