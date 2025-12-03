import logging
import os
import time
from datetime import datetime
from typing import Optional, TypeVar

import psycopg2
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from psycopg2 import connect
from requests.adapters import HTTPAdapter
from typing_extensions import TypedDict
from urllib3 import Retry


# Type definitions for better type hints
class PackageMetadata(TypedDict):
    packageId: str
    collectionCode: Optional[str]
    granuleDate: Optional[str]
    documentType: Optional[str]


class DocumentMetadata(TypedDict):
    title: str
    source_url: str
    source_id: str
    source_type: str
    source_date: str
    source_collection: str
    created_at: datetime
    document_type: Optional[str]
    type: Optional[str]


T = TypeVar("T")


def create_retry_session() -> requests.Session:
    """Create a session with retry logic for API requests."""
    retry = Retry(
        total=5,  # Increased retry attempts
        backoff_factor=2,  # Exponential backoff
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],  # Allow retries for both GET and POST
        raise_on_status=False,  # Don't raise immediately on 5xx errors
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=10,
        pool_maxsize=10,  # Connection pool size
    )

    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    # Add headers
    session.headers.update(
        {"Accept": "application/json", "X-Api-Key": os.getenv("GOVINFO_API_KEY", "")}
    )

    return session


# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("scrape_documents.log"), logging.StreamHandler()],
)

# Load environment variables
load_dotenv()


class DatabaseConnection:
    """Context manager for database connections."""

    def __init__(self):
        load_dotenv()
        self.conn = None
        try:
            self.conn = connect(
                dbname=os.getenv("POSTGRES_DB"),
                user=os.getenv("POSTGRES_USER"),
                password=os.getenv("POSTGRES_PASSWORD"),
                host=os.getenv("POSTGRES_HOST"),
                port=os.getenv("POSTGRES_PORT"),
            )
        except Exception as e:
            logger.error("Database connection error: %s", str(e))
            if self.conn:
                self.conn.close()
                self.conn = None
            raise

    def __enter__(self) -> psycopg2.extensions.connection:
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            try:
                if exc_type is not None:
                    self.conn.rollback()
                else:
                    self.conn.commit()
            except Exception as e:
                logger.error("Error during database transaction: %s", str(e))
            finally:
                try:
                    self.conn.close()
                except Exception as e:
                    logger.error("Error closing database connection: %s", str(e))


def scrape_documents() -> None:
    """Scrape government documents and save to database."""
    try:
        # Get the API key from environment variables
        api_key = os.getenv("GOVINFO_API_KEY")
        if not api_key:
            logger.error("GOVINFO_API_KEY not found in environment variables")
            return

        # Set up session with retry logic
        session = create_retry_session()

        # Set up headers
        headers = {"Accept": "application/json", "X-Api-Key": api_key}

        try:
            # Use the session with retry logic
            response = session.get(
                "https://api.govinfo.gov/v1/packages",
                headers=headers,
                params={"collectionCode": "BILLS"},
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error("API request error: %s", str(e))
            raise
        except ValueError as e:
            logger.error("Error parsing JSON response: %s", str(e))
            raise
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            raise

        logger.debug(f"API response status: {response.status_code}")
        logger.debug(f"API response content: {response.text}")
        packages = response.json().get("packages", [])
        if not packages:
            logger.info("No packages found in response")
            return

        for package in packages:
            package_id = package.get("packageId")
            if not package_id:
                logger.warning(f"Package ID not found in package: {package}")
                continue

            # Get package details
            package_url = f"https://api.govinfo.gov/v1/package/{package_id}"
            try:
                package_response = session.get(package_url, headers=headers)
                package_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("API request error: %s", str(e))
                raise
            except ValueError as e:
                logger.error("Error parsing JSON response: %s", str(e))
                raise
            except Exception as e:
                logger.error("Unexpected error: %s", str(e))
                raise

            logger.debug(f"Package response status: {package_response.status_code}")
            logger.debug(f"Package response content: {package_response.text}")
            package_data = package_response.json()

            # Get document details
            document_url = package_data.get("packageLink")
            if not document_url:
                logger.warning(f"Document URL not found for package: {package_id}")
                continue

            try:
                document_response = session.get(document_url)
                document_response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error("API request error: %s", str(e))
                raise
            except ValueError as e:
                logger.error("Error parsing JSON response: %s", str(e))
                raise
            except Exception as e:
                logger.error("Unexpected error: %s", str(e))
                raise

            logger.debug(f"Document response status: {document_response.status_code}")
            document_content = document_response.text

            try:
                soup = BeautifulSoup(document_content, "html.parser")
                title = soup.title.string if soup.title else "Untitled Document"
            except Exception as e:
                logger.error("Error parsing document %s: %s", document_url, str(e))
                continue

            metadata = DocumentMetadata(
                title=title,
                source_url=document_url,
                source_id=package_id,
                source_type="govinfo",
                source_date=package_data.get("dateIssued"),
                source_collection=package.get("collectionCode"),
                created_at=datetime.now(),
                document_type=package.get("documentType"),
            )

            # Save document
            try:
                with DatabaseConnection() as db:
                    doc_id = save_document(document_content, metadata, db)
                if doc_id:
                    logger.info(
                        "Successfully saved document '%s' with ID %s",
                        metadata["title"],
                        doc_id,
                    )
                else:
                    logger.error("Failed to save document: %s", metadata["title"])
            except psycopg2.Error as e:
                logger.error(
                    "Database error saving document %s: %s", document_url, str(e)
                )
                continue
            except Exception as e:
                logger.error(
                    "Unexpected error saving document %s: %s", document_url, str(e)
                )
                continue

            # Add rate limiting
            time.sleep(1)  # Wait 1 second between requests

    except Exception as e:
        logger.error("Error scraping government database: %s", str(e))


def save_document(
    content: str,
    metadata: DocumentMetadata,
    db: Optional[psycopg2.extensions.connection],
) -> Optional[str]:
    """Save document to PostgreSQL database.

    Args:
        content: The document content
        metadata: Dictionary containing document metadata

    Returns:
        The ID of the saved document

    Raises:
        psycopg2.Error: If there's a database error
        Exception: For other unexpected errors
    """
    if not db:
        logger.error("No database connection provided")
        return None

    try:
        with db.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO documents (title, content, source_url, source_id, source_type, source_date, source_collection, created_at, document_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    metadata.get("title", "Untitled Document"),
                    content,
                    metadata["source_url"],
                    metadata["source_id"],
                    metadata["source_type"],
                    metadata["source_date"],
                    metadata["source_collection"],
                    metadata["created_at"],
                    metadata.get("document_type"),
                ),
            )
            result = cursor.fetchone()
            if not result:
                logger.error("No ID returned from database insert")
                return None

            doc_id = result[0]
            if not doc_id:
                logger.error("No document ID returned from database")
                return None

            db.commit()
            return str(doc_id)

    except psycopg2.Error as e:
        logger.error("Database error saving document: %s", str(e))
        if db:
            db.rollback()
        return None
    except Exception as e:
        logger.error("Unexpected error saving document: %s", str(e))
        if db:
            db.rollback()
        return None


def main() -> None:
    """Main function to run the scraper."""
    try:
        logger.info("Starting document scraping...")
        scrape_documents()
        logger.info("Document scraping completed")
    except Exception as e:
        logger.error("Error in main: %s", str(e))


if __name__ == "__main__":
    main()
