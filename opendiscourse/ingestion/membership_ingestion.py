import logging
import requests
from typing import Optional


from vector_store.weaviate_manager import WeaviateManager

logger = logging.getLogger(__name__)


def ingest_membership_data(membership_data: dict) -> Optional[str]:
    """
    Ingest membership data into Weaviate.

    Args:
        membership_data: A dictionary containing membership information
                         formatted for the Weaviate Membership class.

    Returns:
        The ID of the added membership in Weaviate, or None if ingestion fails.
    """
    weaviate_manager = WeaviateManager()

    try:
        # Assuming membership_data is already in the correct format for Weaviate
        weaviate_manager.add_membership(membership_data)
        # Note: The add_membership function in weaviate_manager.py might need to be
        # updated to return the created object's ID if needed here.
        # For now, we'll assume successful addition if no exception is raised.
        logger.info("Successfully ingested membership data into Weaviate.")
        return membership_data.get("membership_id") # Return the ID if present in input
    except Exception as e:
        logger.error(f"Failed to ingest membership data into Weaviate: {e}")
        return None


def fetch_openstates_legislators(state: str, session: str, api_key: str) -> Optional[list]:
    """
    Fetch legislator data from the Open States API.

    Args:
        state: The state abbreviation (e.g., "ny").
        session: The legislative session (e.g., "2023-2024").
        api_key: Your Open States API key.

    Returns:
        A list of dictionaries representing legislator data, or None if the request fails.
    """
    base_url = "https://v3.openstates.org"
    endpoint = f"/legislators?jurisdiction={state}&session={session}&apikey={api_key}"
    url = f"{base_url}{endpoint}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()  # Raise an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data.get('results') # Open States API returns results in a 'results' key
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching Open States legislators for {state}/{session}: {e}")
        return None

