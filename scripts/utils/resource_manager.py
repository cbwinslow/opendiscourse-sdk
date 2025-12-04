"""
Enhanced Resource Manager using Pydantic Configuration.

Provides backward compatibility with existing code while leveraging
the new configuration system.
"""

import os
import atexit
from typing import Optional, Dict, Any
from pathlib import Path

import psycopg2
from psycopg2 import pool
from dotenv import load_dotenv


# Load environment variables
env_file = Path(__file__).parent.parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)


# Try to import new config system
try:
    from scripts.core.config import get_settings
    _HAS_PYDANTIC = True
except ImportError:
    _HAS_PYDANTIC = False
    get_settings = None


# Global connection pool
_connection_pool: Optional[pool.SimpleConnectionPool] = None


def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for a service.

    Args:
        service: Service name (congress, openstates, govinfo)

    Returns:
        API key or None
    """
    if _HAS_PYDANTIC and get_settings:
        settings = get_settings()
        if service.lower() == 'congress':
            api_config = settings.congress_api
        elif service.lower() == 'openstates':
            api_config = settings.openstates_api
        elif service.lower() == 'govinfo':
            api_config = settings.govinfo_api
        else:
            return None

        if api_config.api_key:
            return api_config.api_key.get_secret_value()

    # Fallback to environment variables
    key_map = {
        'congress': ['CONGRESS_API_KEY', 'CONGRESS_GOV_API_KEY'],
        'openstates': ['OPENSTATES_API_KEY'],
        'govinfo': ['GOVINFO_API_KEY'],
    }

    for env_var in key_map.get(service.lower(), []):
        key = os.getenv(env_var)
        if key:
            return key

    return None


def get_database_config() -> Dict[str, Any]:
    """
    Get database configuration.

    Returns:
        Database configuration dictionary
    """
    if _HAS_PYDANTIC and get_settings:
        settings = get_settings()
        return {
            'host': settings.database.host,
            'port': settings.database.port,
            'database': settings.database.name,
            'user': settings.database.user,
            'password': settings.database.password.get_secret_value() if settings.database.password else None,
        }

    # Fallback to environment variables
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'database': os.getenv('DB_NAME', 'opendiscourse'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD'),
    }


def get_connection_pool(min_conn: int = 1, max_conn: int = 10) -> pool.SimpleConnectionPool:
    """
    Get or create connection pool.

    Args:
        min_conn: Minimum connections
        max_conn: Maximum connections

    Returns:
        Connection pool
    """
    global _connection_pool

    if _connection_pool is None:
        db_config = get_database_config()

        # Remove None password
        if db_config.get('password') is None:
            db_config.pop('password', None)

        _connection_pool = pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            **db_config
        )

        # Register cleanup
        atexit.register(cleanup_pool)

    return _connection_pool


def get_connection():
    """
    Get a database connection from the pool.

    Returns:
        Database connection
    """
    connection_pool = get_connection_pool()
    return connection_pool.getconn()


def return_connection(conn):
    """
    Return a connection to the pool.

    Args:
        conn: Database connection to return
    """
    if _connection_pool:
        _connection_pool.putconn(conn)


def cleanup_pool():
    """Close all connections in the pool."""
    global _connection_pool
    if _connection_pool:
        _connection_pool.closeall()
        _connection_pool = None


# Backward compatibility - expose API keys as module variables
CONGRESS_API_KEY = get_api_key('congress')
OPENSTATES_API_KEY = get_api_key('openstates')
GOVINFO_API_KEY = get_api_key('govinfo')


__all__ = [
    'get_api_key',
    'get_database_config',
    'get_connection_pool',
    'get_connection',
    'return_connection',
    'cleanup_pool',
    'CONGRESS_API_KEY',
    'OPENSTATES_API_KEY',
    'GOVINFO_API_KEY',
]
