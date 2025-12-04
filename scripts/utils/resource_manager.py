"""
Resource Manager for OpenDiscourse
Handles database connections, environment variables, and cleanup.
"""

import os
import sys
import atexit
import logging
from typing import Optional
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Load .env file
load_dotenv(PROJECT_ROOT / ".env")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ResourceManager")

# Global Database Connection
DB_CONNECTION = None

def get_db_connection():
    """
    Get or create a database connection.
    Returns a psycopg2 connection object.
    """
    global DB_CONNECTION

    if DB_CONNECTION is not None and not DB_CONNECTION.closed:
        return DB_CONNECTION

    try:
        import psycopg2

        db_config = {
            'dbname': os.getenv('DB_NAME', 'opendiscourse'),
            'user': os.getenv('DB_USER', 'cbwinslow'),
            'host': os.getenv('DB_HOST', '/var/run/postgresql'),
            'port': os.getenv('DB_PORT', '5432')
        }

        # Add password if present
        if os.getenv('DB_PASSWORD'):
            db_config['password'] = os.getenv('DB_PASSWORD')

        logger.info(f"Connecting to database: {db_config['dbname']} as {db_config['user']}")
        DB_CONNECTION = psycopg2.connect(**db_config)
        return DB_CONNECTION

    except ImportError:
        logger.error("psycopg2 not installed. Please run 'pip install psycopg2-binary'")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

def close_db_connection():
    """Close the database connection if it exists."""
    global DB_CONNECTION
    if DB_CONNECTION is not None and not DB_CONNECTION.closed:
        logger.info("Closing database connection...")
        DB_CONNECTION.close()
        DB_CONNECTION = None

def cleanup():
    """Perform all cleanup tasks."""
    close_db_connection()

# Register cleanup on exit
atexit.register(cleanup)

# Export API Keys for easy access
CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY")
OPENSTATES_API_KEY = os.getenv("OPENSTATES_API_KEY")
GOVINFO_API_KEY = os.getenv("GOVINFO_API_KEY")

if __name__ == "__main__":
    # Test connection
    conn = get_db_connection()
    print("✅ Database connection established successfully.")

    # Check API keys
    keys = {
        "Congress": CONGRESS_API_KEY,
        "OpenStates": OPENSTATES_API_KEY,
        "GovInfo": GOVINFO_API_KEY
    }

    print("\n🔑 API Keys Status:")
    for name, key in keys.items():
        status = "✅ Set" if key else "❌ Missing"
        print(f"  {name}: {status}")
