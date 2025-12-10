import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path to allow importing scripts
# Current file: servers/congress/src/congress_mcp/server.py
# Root: /home/cbwinslow/Videos/opendiscourse
project_root = Path(__file__).parents[4]
sys.path.append(str(project_root))

from mcp.server.fastmcp import FastMCP

# Import ingestion logic
try:
    from scripts.ingest_congress_bills import CongressBillsIngestor, CongressBillsConfig
    from scripts.bulk_ingest_votes import VoteIngestionAPI
    from scripts.ingest_congress_incremental import IncrementalCongressIngestor
    from scripts.ingestion_config import validate_all_api_keys
except ImportError as e:
    logging.error(f"Failed to import ingestion scripts: {e}")
    # We continue, but tools might fail if dependencies are missing
    pass

# Initialize FastMCP server
mcp = FastMCP("congress-ingestion")

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "mcp_congress.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("congress-mcp")

@mcp.tool()
def ingest_bills(congress: int, batch_size: int = 50) -> str:
    """
    Ingest bills for a specific Congress.

    Args:
        congress: The Congress number (e.g., 117, 118).
        batch_size: Number of bills to fetch per API call.
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        config = CongressBillsConfig(
            congress=congress,
            batch_size=batch_size,
            api_key=os.getenv("CONGRESS_API_KEY")
        )

        with CongressBillsIngestor(config) as ingestor:
            result = ingestor.ingest_congress_bills()

        if result["status"] == "completed":
            return f"Successfully ingested bills for Congress {congress}. Processed: {result['total_processed']}"
        else:
            return f"Ingestion failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Error executing ingest_bills: {str(e)}"

@mcp.tool()
def ingest_votes(congress: int, year: int) -> str:
    """
    Ingest votes for a specific Congress and year.

    Args:
        congress: The Congress number.
        year: The year to ingest votes for.
    """
    try:
        ingestion = VoteIngestionAPI()
        total_records = ingestion.ingest_congress_votes(congress, year)
        return f"Successfully ingested {total_records} votes for Congress {congress}, year {year}."
    except Exception as e:
        return f"Error executing ingest_votes: {str(e)}"

@mcp.tool()
def ingest_members(congress: int) -> str:
    """
    Ingest members for a specific Congress.

    Args:
        congress: The Congress number.
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        ingestor = IncrementalCongressIngestor()
        result = ingestor.ingest_congress_members(congress)

        if result["status"] == "completed" or result["status"] == "already_completed":
            return (
                f"Successfully ingested members for Congress {congress}.\n"
                f"Processed: {result.get('records_processed', 0)}\n"
                f"Skipped: {result.get('records_skipped', 0)}"
            )
        else:
            return f"Ingestion failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Error executing ingest_members: {str(e)}"

@mcp.tool()
def get_ingestion_status(congress: int) -> str:
    """
    Get the current ingestion status for bills of a specific Congress.

    Args:
        congress: The Congress number.
    """
    try:
        config = CongressBillsConfig(congress=congress)
        with CongressBillsIngestor(config) as ingestor:
            status = ingestor.get_checkpoint_status()

        return (
            f"Status for Congress {congress} Bills:\n"
            f"  Processed: {status['total_processed']}\n"
            f"  Estimated Total: {status['total_estimated']}\n"
            f"  Completion: {status['completion_percentage']:.1f}%\n"
            f"  Completed: {status['is_completed']}\n"
            f"  Last Update: {status['last_ingestion_at']}"
        )
    except Exception as e:
        return f"Error getting status: {str(e)}"

@mcp.resource("congress://votes/{congress}")
def get_votes_resource(congress: int) -> str:
    """
    Get a summary of votes for a specific Congress.
    """
    # This is a placeholder for a resource that would query the database
    # and return a JSON representation of votes.
    # For now, we'll return a static message or implement a simple query if needed.
    return f"Resource for Congress {congress} votes (Not implemented yet)"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
