"""Database session management."""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from opendiscourse.core.config import settings

# Create database engine
engine = create_engine(
    str(settings.DATABASE_URI),
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Session: A database session

    Example:
        >>> with get_db() as db:
        ...     # Use the database session
        ...     result = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Context manager for database sessions
@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for database sessions.

    Yields:
        Session: A database session

    Example:
        >>> with get_db_context() as db:
        ...     # Use the database session
        ...     result = db.query(User).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
