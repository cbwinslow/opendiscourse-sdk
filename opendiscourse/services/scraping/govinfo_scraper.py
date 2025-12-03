"""GovInfo scraper for OpenDiscourse.

This module provides functionality to scrape and process documents from the GovInfo API.
"""

# Standard library imports
import logging
import os
from typing import Optional
from urllib.parse import urljoin
from xml.etree import ElementTree as ET

# Third-party imports
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extensions import connection as PgConnection
from requests.adapters import HTTPAdapter
from requests.models import Response
from urllib3.util.retry import Retry

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default timeout for HTTP requests (in seconds)
DEFAULT_TIMEOUT = 30


class GOVInfoScraper:
    """Scraper for GovInfo API."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """Initialize the GOVInfoScraper.

        Args:
            api_key: Optional API key for GovInfo. If not provided, will use
                the GOVINFO_API_KEY environment variable.
            timeout: Timeout in seconds for HTTP requests. Defaults to 30 seconds.
        """
        self.api_key = api_key or os.getenv("GOVINFO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "No API key provided. Set GOVINFO_API_KEY environment variable or "
                "pass api_key parameter."
            )

        self.base_url = "https://api.govinfo.gov"
        self.timeout = timeout
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure a requests Session with retry logic.

        Returns:
            Configured requests.Session instance.
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Mount the retry strategy to both http and https
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set default headers
        session.headers.update(
            {
                "X-Api-Key": self.api_key,
                "User-Agent": "OpenDiscourse/1.0",
            }
        )

        return session

    def _make_request(self, endpoint: str, params: Optional[dict] = None) -> Response:
        """Make an HTTP GET request to the GovInfo API.

        Args:
            endpoint: API endpoint (e.g., '/collections/BILLS/2023-01-01')
            params: Optional query parameters

        Returns:
            Response object from requests

        Raises:
            requests.HTTPError: If the request fails
        """
        url = urljoin(self.base_url, endpoint)
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error("Request to %s failed: %s", url, str(e))
            raise


def get_db_connection() -> PgConnection:
    """Get a database connection.

    Returns:
        A connection to the PostgreSQL database.

    Raises:
        psycopg2.OperationalError: If the connection to the database fails.
    """
    try:
        return psycopg2.connect(
            dbname=os.getenv("DB_NAME", "opendiscourse"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
        )
    except psycopg2.Error as e:
        logger.error("Failed to connect to database: %s", str(e))
        raise


def fetch_govinfo_metadata() -> None:
    """Fetch metadata from GovInfo API.

    Fetches collections and their associated documents from the GovInfo API,
    processes them, and saves them to the database.

    Environment Variables:
        GOVINFO_API_KEY: API key for accessing the GovInfo API

    Raises:
        ValueError: If GOVINFO_API_KEY is not set
    """
    base_url = "https://api.govinfo.gov"
    api_key = os.getenv("GOVINFO_API_KEY")

    if not api_key:
        raise ValueError("GOVINFO_API_KEY environment variable not set")

    # Get collections
    collections_url = f"{base_url}/collections"
    params = {"api_key": api_key}

    try:
        response = requests.get(collections_url, params=params, timeout=30)
        response.raise_for_status()
        collections = response.json()
    except requests.RequestException as e:
        logger.error("Failed to fetch collections: %s", str(e))
        return

    # Process each collection
    for collection in collections.get("collections", []):
        collection_name = collection.get("collectionCode")
        if not collection_name:
            continue

        # Get documents for collection
        documents_url = f"{base_url}/packages"
        params = {
            "collectionCode": collection_name,
            "api_key": api_key,
        }

        try:
            response = requests.get(documents_url, params=params, timeout=30)
            response.raise_for_status()
            documents = response.json()
        except requests.RequestException as e:
            logger.error(
                "Failed to fetch documents for collection %s: %s",
                collection_name,
                str(e),
            )
            continue

        # Process each document
        for doc in documents.get("packages", []):
            try:
                # Get document details
                doc_id = doc.get("packageId")
                if not doc_id:
                    continue

                doc_url = f"{base_url}/packages/{doc_id}/summary"
                try:
                    doc_response = requests.get(
                        doc_url, params={"api_key": api_key}, timeout=30
                    )
                    doc_response.raise_for_status()
                    doc_details = doc_response.json()
                except requests.RequestException as e:
                    logger.error("Failed to fetch document %s: %s", doc_id, str(e))
                    continue

                # Parse XML content if available
                content_url = f"{base_url}/packages/{doc_id}/content-detail.xml"
                try:
                    content_response = requests.get(
                        content_url, params={"api_key": api_key}, timeout=30
                    )
                    content_response.raise_for_status()
                except requests.RequestException as e:
                    logger.warning(
                        "No content available for document %s: %s", doc_id, str(e)
                    )
                    content = ""

                if content_response.status_code == 200:
                    try:
                        root = ET.fromstring(content_response.text)
                        content = ET.tostring(root, encoding="unicode")
                    except ET.ParseError as e:
                        logger.warning(
                            "Failed to parse XML content for document %s: %s",
                            doc_id,
                            str(e),
                        )
                        content = content_response.text

                # Prepare metadata
                try:
                    metadata = {
                        "source": "govinfo",
                        "package_id": doc_id,
                        "collection": collection_name,
                        "title": doc_details.get("title", ""),
                        "date_issued": doc_details.get("dateIssued", ""),
                        "date_last_modified": doc_details.get("dateLastModified", ""),
                        "url": f"https://www.govinfo.gov/content/pkg/{doc_id}/html/{doc_id}.htm",
                    }

                    # Save to database
                    save_document(
                        title=doc_details.get("title", ""),
                        content=content,
                        metadata=metadata,
                    )

                    logger.info("Processed document: %s", doc_id)

                except Exception as e:
                    logger.error(
                        "Error processing document %s: %s",
                        doc_id,
                        str(e),
                        exc_info=True,
                    )

            except Exception as e:
                logger.error(
                    "Unexpected error processing document %s: %s",
                    doc.get("packageId", "unknown"),
                    str(e),
                    exc_info=True,
                )


def save_document(title: str, content: str, metadata: dict) -> Optional[int]:
    """Save document to PostgreSQL database.

    Args:
        title: The title of the document
        content: The content of the document
        metadata: Dictionary containing document metadata

    Returns:
        int: The ID of the inserted document, or None if the operation failed
    """
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert document
        cursor.execute(
            """
            INSERT INTO documents (
                title,
                content,
                metadata,
                created_at,
                updated_at
            ) VALUES (%s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            RETURNING id
            """,
            (title, content, metadata),
        )

        doc_id = cursor.fetchone()[0]
        conn.commit()
        return doc_id

    except psycopg2.Error as e:
        if conn:
            conn.rollback()
        logger.error(
            "Database error saving document '%s': %s",
            title[:50] + "..." if len(title) > 50 else title,
            str(e),
            exc_info=True,
        )
        return None
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error("Unexpected error saving document: %s", str(e), exc_info=True)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and not conn.closed:
            conn.close()


def main() -> None:
    """Run the GovInfo scraper.

    Loads environment variables and starts the scraping process.
    """
    try:
        load_dotenv()
        logger.info("Starting GovInfo scraper")
        fetch_govinfo_metadata()
        logger.info("GovInfo scraper finished successfully")
    except Exception as e:
        logger.critical("GovInfo scraper failed: %s", str(e), exc_info=True)
        raise


if __name__ == "__main__":
    main()
