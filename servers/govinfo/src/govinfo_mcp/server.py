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
    from scripts.ingest_govinfo_bills import GovInfoBillsIngestor, GovInfoBillsConfig
    from scripts.bulk_ingest_votes import VoteIngestionAPI
    from scripts.ingest_govinfo_members import GovInfoMembersIngestor
    from scripts.ingestion_config import validate_all_api_keys
except ImportError as e:
    logging.error(f"Failed to import ingestion scripts: {e}")
    pass

mcp = FastMCP("govinfo-ingestion")

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "mcp_govinfo.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("govinfo-mcp")

@mcp.tool()
def ingest_bills(congress: int, batch_size: int = 50) -> str:
    """
    Ingest bills for a specific Congress from GovInfo.

    Args:
        congress: The Congress number (e.g., 117, 118).
        batch_size: Number of bills to fetch per API call.
    """
    try:
        # Validate API keys first
        key_validation = validate_all_api_keys()
        if not key_validation["valid"]:
            return f"Error: API key validation failed: {', '.join(key_validation['errors'])}"

        config = GovInfoBillsConfig(
            congress=congress,
            batch_size=batch_size,
            api_key=os.getenv("GOVINFO_API_KEY")
        )

        with GovInfoBillsIngestor(config) as ingestor:
            result = ingestor.ingest_govinfo_bills()

        if result["status"] == "completed":
            return (
                f"Successfully ingested GovInfo bills for Congress {congress}.\n"
                f"Total Processed: {result['total_processed']}\n"
                f"Collections Processed: {result['collections_processed']}"
            )
        else:
            return f"Ingestion failed: {result.get('error', 'Unknown error')}"

    except Exception as e:
        return f"Error executing ingest_bills: {str(e)}"

@mcp.tool()
def ingest_votes(collection: str, year: int) -> str:
    """
    Ingest votes for a specific collection and year from GovInfo.

    Args:
        collection: The collection code (e.g., 'BILLS', 'CREC').
        year: The year to ingest votes for.
    """
    try:
        ingestion = VoteIngestionAPI()
        total_records = ingestion.ingest_govinfo_votes(collection, year)
        return f"Successfully ingested {total_records} votes for {collection}, year {year}."
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

        db_params = {
            'database': os.getenv('DB_NAME', 'cbwinslow'),
            'user': os.getenv('DB_USER', 'cbwinslow')
        }
        ingestor = GovInfoMembersIngestor(db_params)
        stats = ingestor.ingest_congress_members(congress)

        return (
            f"Successfully ingested members for Congress {congress}.\n"
            f"Processed: {stats['total_processed']}\n"
            f"Failed: {stats['total_failed']}\n"
            f"Success Rate: {stats['success_rate']:.1f}%"
        )
    except Exception as e:
        return f"Error executing ingest_members: {str(e)}"

def main():
    mcp.run()

if __name__ == "__main__":
    main()
