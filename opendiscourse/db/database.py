"""Database connection and session management."""

import os
from collections.abc import Generator
from contextlib import contextmanager

from base import Base
from base import init_database as base_init_database
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Get database URL from environment variable
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/opendiscourse"
)

# Initialize the database
base_init_database(DATABASE_URL)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=5,  # Number of connections to keep open in the pool
    max_overflow=10,  # Max number of connections that can be created beyond pool_size
    pool_timeout=30,  # Seconds to wait before giving up on getting a connection
    pool_recycle=1800,  # Recycle connections after 30 minutes
    pool_pre_ping=True,  # Enable connection health checks
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,  # Prevent attribute refresh on commit
)


def get_db() -> Generator[Session, None, None]:
    """Get a database session.

    Yields:
        Session: A database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """Provide a database session for a single operation.

    Yields:
        Session: A database session

    Example:
        with get_db() as db:
            db.query(Entity).all()

    Note:
        The session is automatically closed when the context exits.
        Any uncommitted transactions will be rolled back.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Initialize the database by creating all tables.

    This should be called during application startup to ensure all
    database tables are created before the application starts handling requests.
    """
    # Import models here to ensure they are registered with SQLAlchemy

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Log successful initialization
    print("Database initialized successfully")


# Re-export from base module
__all__ = ["Base", "get_db", "SessionLocal", "init_db", "engine", "DATABASE_URL"]
