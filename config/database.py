"""
Centralized Database Configuration for OpenDiscourse Ingestion System
Single source of truth for all database connections and configurations
"""

import os
import logging
import psycopg2
from psycopg2 import pool
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DatabaseBackend(Enum):
    POSTGRESQL = "postgresql"
    SUPABASE = "supabase"


@dataclass
class DatabaseConfig:
    """Database configuration data class"""

    host: str
    port: int
    database: str
    user: str
    password: Optional[str] = None
    sslmode: str = "prefer"
    connect_timeout: int = 30
    application_name: str = "opendiscourse_ingestion"
    pool_min: int = 1
    pool_max: int = 20
    backend: DatabaseBackend = DatabaseBackend.POSTGRESQL


class DatabaseManager:
    """Centralized database connection manager with connection pooling"""

    _instance: Optional["DatabaseManager"] = None
    _connection_pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None

    def __new__(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.config = self._load_config()
            self._connection_pool = None
            self._initialized = True

    def _load_config(self) -> DatabaseConfig:
        """Load database configuration from environment variables"""

        # Support multiple environment variable patterns for compatibility
        host = (
            os.getenv("DB_HOST")
            or os.getenv("POSTGRES_HOST")
            or os.getenv("SUPABASE_HOST")
            or "localhost"  # Will use docker exec fallback
        )

        port = int(
            os.getenv("DB_PORT")
            or os.getenv("POSTGRES_PORT")
            or os.getenv("SUPABASE_PORT")
            or "5432"
        )

        database = (
            os.getenv("DB_NAME")
            or os.getenv("POSTGRES_DB")
            or os.getenv("SUPABASE_DB")
            or "penpot"  # Default to penpot database since that's what's running
        )

        user = (
            os.getenv("DB_USER")
            or os.getenv("POSTGRES_USER")
            or os.getenv("SUPABASE_USER")
            or "penpot"  # Default to penpot user since that's what's running
        )

        user = (
            os.getenv("DB_USER")
            or os.getenv("POSTGRES_USER")
            or os.getenv("SUPABASE_USER")
            or "cbwinslow"
        )

        password = (
            os.getenv("DB_PASSWORD")
            or os.getenv("POSTGRES_PASSWORD")
            or os.getenv("SUPABASE_PASSWORD")
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or "penpot"  # Default to penpot password since that's what's running
        )

        # Detect backend type
        backend = DatabaseBackend.POSTGRESQL
        if "supabase" in host.lower() or os.getenv("SUPABASE_URL"):
            backend = DatabaseBackend.SUPABASE

        config = DatabaseConfig(
            host=host, port=port, database=database, user=user, password=password, backend=backend
        )

        logger.info(
            f"Database config loaded: {config.user}@{config.host}:{config.port}/{config.database} ({config.backend.value})"
        )
        return config

    def initialize_pool(self) -> None:
        """Initialize the connection pool"""
        if self._connection_pool is not None:
            return

        try:
            connection_string = self._build_connection_string()
            self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=self.config.pool_min, maxconn=self.config.pool_max, dsn=connection_string
            )
            logger.info(
                f"Connection pool initialized: {self.config.pool_min}-{self.config.pool_max} connections"
            )

            # Test connection
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    logger.info("Database connection test successful")

        except Exception as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        if self.config.backend == DatabaseBackend.SUPABASE:
            # Supabase often uses connection strings
            supabase_url = os.getenv("SUPABASE_URL")
            if supabase_url:
                return supabase_url

        # Standard PostgreSQL connection string
        conn_parts = [
            f"host={self.config.host}",
            f"port={self.config.port}",
            f"dbname={self.config.database}",
            f"user={self.config.user}",
            f"sslmode={self.config.sslmode}",
            f"connect_timeout={self.config.connect_timeout}",
            f"application_name={self.config.application_name}",
        ]

        if self.config.password:
            conn_parts.append(f"password={self.config.password}")

        return " ".join(conn_parts)

    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        if self._connection_pool is None:
            self.initialize_pool()

        connection = None
        try:
            connection = self._connection_pool.getconn()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                self._connection_pool.putconn(connection)

    @contextmanager
    def get_cursor(self, dict_cursor: bool = False):
        """Get a database cursor from a connection"""
        with self.get_connection() as connection:
            if dict_cursor:
                from psycopg2.extras import RealDictCursor

                cursor = connection.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = connection.cursor()

            try:
                yield cursor
                connection.commit()
            except Exception as e:
                connection.rollback()
                logger.error(f"Database cursor error: {e}")
                raise
            finally:
                cursor.close()

    def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]

                    cursor.execute("""
                        SELECT table_schema, table_name 
                        FROM information_schema.tables 
                        WHERE table_schema IN ('congress', 'govinfo', 'openstates', 'incremental', 'ingestion')
                        ORDER BY table_schema, table_name
                    """)
                    tables = cursor.fetchall()

                    return {
                        "status": "success",
                        "version": version,
                        "tables_count": len(tables),
                        "tables": [{"schema": row[0], "table": row[1]} for row in tables],
                        "config": {
                            "host": self.config.host,
                            "port": self.config.port,
                            "database": self.config.database,
                            "user": self.config.user,
                            "backend": self.config.backend.value,
                        },
                    }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "config": {
                    "host": self.config.host,
                    "port": self.config.port,
                    "database": self.config.database,
                    "user": self.config.user,
                    "backend": self.config.backend.value,
                },
            }

    def close_pool(self) -> None:
        """Close the connection pool"""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None
            logger.info("Connection pool closed")


# Global instance
db_manager = DatabaseManager()


# Convenience functions
def get_db_connection():
    """Get a database connection (backward compatibility)"""
    return db_manager.get_connection()


def get_db_cursor(dict_cursor: bool = False):
    """Get a database cursor (backward compatibility)"""
    return db_manager.get_cursor(dict_cursor=dict_cursor)


def test_database():
    """Test database connection"""
    return db_manager.test_connection()


def initialize_database():
    """Initialize database connection pool"""
    db_manager.initialize_pool()


# Legacy compatibility functions
def create_connection():
    """Legacy connection function - creates direct connection"""
    config = db_manager.config
    return psycopg2.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        sslmode=config.sslmode,
        connect_timeout=config.connect_timeout,
        application_name=config.application_name,
    )


if __name__ == "__main__":
    # Test database configuration
    logging.basicConfig(level=logging.INFO)

    print("Testing database configuration...")
    result = test_database()

    if result["status"] == "success":
        print("✅ Database connection successful!")
        print(f"   Version: {result['version']}")
        print(f"   Tables found: {result['tables_count']}")
        print(f"   Configuration: {result['config']}")
    else:
        print("❌ Database connection failed!")
        print(f"   Error: {result['error']}")
        print(f"   Configuration: {result['config']}")
