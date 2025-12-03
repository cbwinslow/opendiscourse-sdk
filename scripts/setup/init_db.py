#!/usr/bin/env python3
"""Initialize the database.

This script creates all database tables and performs any necessary
initial setup.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from opendiscourse.db.base_class import Base
from opendiscourse.db.session import engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db() -> None:
    """Initialize the database."""
    logger.info("Creating database tables...")

    try:
        # Import all models here to ensure they are registered with SQLAlchemy
        from opendiscourse.db import models  # noqa: F401

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def drop_db() -> None:
    """Drop all database tables."""
    logger.warning("Dropping all database tables...")

    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except Exception as e:
        logger.error(f"Error dropping database tables: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Initialize the database")
    parser.add_argument(
        "--drop",
        action="store_true",
        help="Drop all tables before creating them",
    )

    args = parser.parse_args()

    if args.drop:
        drop_db()

    init_db()
