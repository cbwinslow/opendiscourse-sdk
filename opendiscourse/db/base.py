"""Base module for SQLAlchemy models and database configuration.

This module provides the base class for all SQLAlchemy models and handles
database connection and session management.
"""

"""Base database models and configuration for OpenDiscourse."""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, TypeVar

from sqlalchemy import Column, DateTime, Integer, create_engine, text
from sqlalchemy.orm import Session, scoped_session, sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeBase
from sqlalchemy.orm.decl_api import declared_attr as _declared_attr
from sqlalchemy.sql.schema import MetaData

if TYPE_CHECKING:
    from collections.abc import Iterator
    from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy metadata for database schema
metadata = MetaData()

# Type variable for SQLAlchemy models
ModelType = TypeVar("ModelType", bound="Base")

# Database connection URL from environment variables or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./opendiscourse.db")

# Configure SQLAlchemy engine with connection pooling and timeouts
engine_kwargs: dict[str, Any] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,  # Recycle connections after 5 minutes
    "pool_size": 5,  # Number of connections to keep open
    "max_overflow": 10,  # Max number of connections to create if pool is full
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",  # Log SQL queries
}

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory with scoped sessions for thread safety
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)

# Alias for type hints
_ModelT = TypeVar("_ModelT", bound="Base")


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models with common functionality.

    This class provides a foundation for all database models, including:
    - Automatic table naming
    - Common columns (id, created_at, updated_at)
    - Helper methods for CRUD operations
    - Type hints for better IDE support
    """

    __abstract__ = True

    # Configure metadata for all models
    metadata: MetaData = metadata

    # Type hints for SQLAlchemy columns
    id: int = Column(Integer, primary_key=True, autoincrement=True)
    created_at: datetime = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: datetime = Column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP"),
    )

    @_declared_attr
    def __tablename__(cls) -> str:  # type: ignore
        """Generate table name from class name.

        Converts CamelCase class names to snake_case table names.
        Example: 'UserProfile' -> 'user_profiles'
        """
        # Convert CamelCase to snake_case
        name = "".join(
            ["_" + c.lower() if c.isupper() else c for c in cls.__name__]
        ).lstrip("_")
        # Handle acronyms and make plural
        return f"{name}s"

    def to_dict(self, exclude: set[str] | None = None) -> dict[str, Any]:
        """Convert model instance to dictionary.

        Args:
            exclude: Set of field names to exclude from the result

        Returns:
            Dictionary representation of the model
        """
        if exclude is None:
            exclude = set()

        result: dict[str, Any] = {}
        for column in self.__table__.columns:  # type: ignore[attr-defined]
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Convert datetime to ISO format
                if hasattr(value, "isoformat"):
                    value = value.isoformat()
                result[column.name] = value
        return result

    @classmethod
    def from_dict(cls: type[_ModelT], data: dict[str, Any]) -> _ModelT:
        """Create a model instance from a dictionary.

        Args:
            data: Dictionary of field names and values

        Returns:
            New model instance
        """
        # Filter out any keys that aren't columns in the model
        columns = {c.name for c in cls.__table__.columns}  # type: ignore[attr-defined]
        filtered_data = {k: v for k, v in data.items() if k in columns}
        return cls(**filtered_data)

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model instance from a dictionary.

        Args:
            data: Dictionary of field names and new values
        """
        columns = {c.name for c in self.__table__.columns}  # type: ignore[attr-defined]
        for key, value in data.items():
            if key in columns and hasattr(self, key):
                setattr(self, key, value)


# Context manager for database sessions
@contextmanager
def get_db() -> Iterator[Session]:
    """Provide a transactional scope around a series of operations.

    Yields:
        SQLAlchemy database session

    Example:
        with get_db() as db:
            db.add(user)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Database error occurred")
        raise
    finally:
        db.close()

        # Add table name if available
        table_name = getattr(self.__class__, "__tablename__", None)
        if table_name:
            return f"<{table_name}({', '.join(attrs)})>"
        return f"<{self.__class__.__name__}({', '.join(attrs)})>"


# Make Base importable
__all__ = ["Base", "metadata", "engine", "get_db", "init_database"]
