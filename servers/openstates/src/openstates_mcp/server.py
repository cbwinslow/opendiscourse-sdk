import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
project_root = Path(__file__).parents[4]
sys.path.append(str(project_root))

from mcp.server.fastmcp import FastMCP

# Import ingestion logic
try:
    from scripts.ingest_openstates_bills_incremental import IncrementalOpenStatesBillsIngestor
    from scripts.bulk_ingest_votes import VoteIngestionAPI
    from scripts.ingest_openstates_people import OpenStatesPeopleIngestor
    from scripts.openstates_committees_ingestion import OpenStatesCommitteesIngestor
    from scripts.enhanced_openstates_ingestion import (
        OpenStatesRateLimitManager, OpenStatesPaginationManager,
        OpenStatesProgressMonitor
    )
    from scripts.ingestion_config import validate_all_api_keys
    import psycopg2
except ImportError as e:
    logging.error(f"Failed to import ingestion scripts: {e}")
    pass

mcp = FastMCP("openstates-ingestion")

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "mcp_openstates.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("openstates-mcp")

@mcp.tool()
def ingest_bills(jurisdiction: str) -> str:
    """
    Ingest bills for a specific jurisdiction.

    Args:
        jurisdiction: The jurisdiction code (e.g., 'ca', 'tx', 'ny').
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        ingestor = IncrementalOpenStatesBillsIngestor()
        result = ingestor.ingest_jurisdiction_bills(jurisdiction)

        if result["status"] == "completed" or result["status"] == "already_completed":
            return (
                f"Successfully ingested bills for {jurisdiction}.\n"
                f"Processed: {result.get('records_processed', 0)}\n"
                f"Skipped: {result.get('records_skipped', 0)}"
            )
        else:
            return f"Ingestion failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Error executing ingest_bills: {str(e)}"

@mcp.tool()
def ingest_votes(jurisdiction: str, year: int) -> str:
    """
    Ingest votes for a specific jurisdiction and year.

    Args:
        jurisdiction: The jurisdiction code.
        year: The year to ingest votes for.
    """
    try:
        ingestion = VoteIngestionAPI()
        total_records = ingestion.ingest_openstates_votes(jurisdiction, year)
        return f"Successfully ingested {total_records} votes for {jurisdiction}, year {year}."
    except Exception as e:
        return f"Error executing ingest_votes: {str(e)}"

@mcp.tool()
def ingest_people(jurisdiction: str) -> str:
    """
    Ingest people for a specific jurisdiction.

    Args:
        jurisdiction: The jurisdiction code (e.g., 'ca', 'tx').
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        db_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        ingestor = OpenStatesPeopleIngestor(db_params)
        stats = ingestor.ingest_people(jurisdiction)

        return (
            f"Successfully ingested people for {jurisdiction}.\n"
            f"Processed: {stats['total_processed']}\n"
            f"Failed: {stats['total_failed']}\n"
            f"Success Rate: {stats['success_rate']:.1f}%"
        )
    except Exception as e:
        return f"Error executing ingest_people: {str(e)}"

@mcp.tool()
def ingest_committees(jurisdiction: str) -> str:
    """
    Ingest committees for a specific jurisdiction.

    Args:
        jurisdiction: The jurisdiction code.
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        # Initialize components
        rate_manager = OpenStatesRateLimitManager()
        pagination_manager = OpenStatesPaginationManager()
        progress_monitor = OpenStatesProgressMonitor()

        db_conn = psycopg2.connect(
            database=os.getenv('DB_NAME', 'cbwinslow'),
            user=os.getenv('DB_USER', 'cbwinslow')
        )

        try:
            ingestor = OpenStatesCommitteesIngestor(
                db_conn, rate_manager, pagination_manager, progress_monitor
            )
            result = ingestor.ingest_committees_with_details(jurisdiction)

            return (
                f"Successfully ingested committees for {jurisdiction}.\n"
                f"Total Processed: {result['total_processed']}\n"
                f"Phases Completed: {result['phases_completed']}/{result['phases_total']}"
            )
        finally:
            db_conn.close()

    except Exception as e:
        return f"Error executing ingest_committees: {str(e)}"

@mcp.tool()
def get_jurisdiction_status(jurisdiction: str) -> str:
    """
    Get the current ingestion status for bills of a specific jurisdiction.

    Args:
        jurisdiction: The jurisdiction code.
    """
    try:
        ingestor = IncrementalOpenStatesBillsIngestor()
        params = ingestor.get_next_ingestion_params(jurisdiction)

        return (
            f"Status for {jurisdiction} Bills:\n"
            f"  Next Page: {params['next_page']}\n"
            f"  Completed: {params['is_completed']}\n"
            f"  Total Processed: {params['total_processed']}\n"
            f"  Last Run: {params['last_run']}"
        )
    except Exception as e:
        return f"Error getting status: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
