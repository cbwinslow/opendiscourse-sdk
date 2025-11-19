"""Bulk data ingestion from Congress.gov and GovInfo APIs.

This module provides functionality for ingesting large volumes of congressional
and government documents from multiple sources including Congress.gov API and
GovInfo bulk data endpoints.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, TypedDict
from xml.etree import ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from opendiscourse.ingestion.document_ingestion import DocumentMetadata, _save_document
except ImportError:
    # Fallback if module is not available
    class DocumentMetadata(TypedDict, total=False):
        """Metadata used when saving documents."""
        title: str
        source_url: str
        source_id: str
        source_type: str
        source_date: str
        source_collection: str
        created_at: datetime
        document_type: Optional[str]

    def _save_document(content: str, metadata: DocumentMetadata) -> Optional[int]:
        """Fallback save function - logs only."""
        logger.info("Document would be saved: %s", metadata.get("title", "Untitled"))
        return 1  # Return dummy ID for testing

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_TIMEOUT = 30
RATE_LIMIT_DELAY = 0.5  # seconds between requests
DEFAULT_DATA_DIR = "data/bulk_ingestion"


class BulkDataIngester:
    """Handles bulk data ingestion from multiple government data sources."""

    def __init__(
        self,
        govinfo_api_key: Optional[str] = None,
        congress_api_key: Optional[str] = None,
        data_dir: str = DEFAULT_DATA_DIR,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """Initialize the bulk data ingester.

        Args:
            govinfo_api_key: API key for GovInfo API (defaults to env var)
            congress_api_key: API key for Congress.gov API (defaults to env var)
            data_dir: Directory to store downloaded data
            timeout: Request timeout in seconds
        """
        self.govinfo_api_key = govinfo_api_key or os.getenv("GOVINFO_API_KEY")
        self.congress_api_key = congress_api_key or os.getenv("CONGRESS_API_KEY")
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.session = self._create_session()

        # API endpoints
        self.govinfo_base_url = "https://api.govinfo.gov"
        self.congress_base_url = "https://api.congress.gov/v3"

        # Statistics
        self.stats = {
            "total_documents": 0,
            "successful_ingestions": 0,
            "failed_ingestions": 0,
            "skipped_documents": 0
        }

    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic."""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def ingest_govinfo_collection(
        self,
        collection_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """Ingest documents from a GovInfo collection.

        Args:
            collection_code: Collection code (e.g., 'BILLS', 'FR', 'CREC')
            start_date: Start date in YYYY-MM-DD format (defaults to 30 days ago)
            end_date: End date in YYYY-MM-DD format (defaults to today)
            limit: Maximum number of documents to ingest (None for all)

        Returns:
            Dictionary with ingestion statistics
        """
        if not self.govinfo_api_key:
            logger.error("GOVINFO_API_KEY not configured")
            return self.stats

        # Set default dates
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

        logger.info(
            "Starting bulk ingestion for collection %s from %s to %s",
            collection_code, start_date, end_date
        )

        # Get packages in collection
        packages_url = f"{self.govinfo_base_url}/collections/{collection_code}/{start_date}/{end_date}"
        headers = {"X-Api-Key": self.govinfo_api_key}

        try:
            response = self.session.get(
                packages_url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            packages_data = response.json()

            packages = packages_data.get("packages", [])
            if limit:
                packages = packages[:limit]

            logger.info("Found %d packages to process", len(packages))

            # Process each package
            for idx, package in enumerate(packages, 1):
                package_id = package.get("packageId")
                if not package_id:
                    continue

                logger.info("Processing package %d/%d: %s", idx, len(packages), package_id)
                self._ingest_govinfo_package(package_id, collection_code)
                time.sleep(RATE_LIMIT_DELAY)

        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch collection %s: %s", collection_code, e)

        return self.stats

    def _ingest_govinfo_package(self, package_id: str, collection_code: str) -> bool:
        """Ingest a single GovInfo package.

        Args:
            package_id: Package identifier
            collection_code: Collection code

        Returns:
            True if successful, False otherwise
        """
        self.stats["total_documents"] += 1

        try:
            # Get package summary
            summary_url = f"{self.govinfo_base_url}/packages/{package_id}/summary"
            headers = {"X-Api-Key": self.govinfo_api_key}

            response = self.session.get(
                summary_url,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            package_data = response.json()

            # Get document content (try different formats)
            content = self._fetch_package_content(package_id)
            if not content:
                logger.warning("No content available for package %s", package_id)
                self.stats["skipped_documents"] += 1
                return False

            # Prepare metadata
            metadata: DocumentMetadata = {
                "title": package_data.get("title", package_id),
                "source_url": f"https://www.govinfo.gov/content/pkg/{package_id}",
                "source_id": package_id,
                "source_type": "govinfo_bulk",
                "source_date": package_data.get("dateIssued", ""),
                "source_collection": collection_code,
                "created_at": datetime.now(),
                "document_type": package_data.get("docClass", ""),
            }

            # Save to database
            doc_id = _save_document(content, metadata)
            if doc_id:
                logger.info("Successfully ingested package %s (doc_id: %s)", package_id, doc_id)
                self.stats["successful_ingestions"] += 1
                return True
            else:
                logger.error("Failed to save package %s to database", package_id)
                self.stats["failed_ingestions"] += 1
                return False

        except Exception as e:
            logger.error("Error processing package %s: %s", package_id, e)
            self.stats["failed_ingestions"] += 1
            return False

    def _fetch_package_content(self, package_id: str) -> Optional[str]:
        """Fetch content for a package, trying multiple formats.

        Args:
            package_id: Package identifier

        Returns:
            Content string or None if not available
        """
        headers = {"X-Api-Key": self.govinfo_api_key}

        # Try different content formats in order of preference
        formats = ["htm", "txt", "xml", "pdf"]

        for fmt in formats:
            try:
                content_url = f"{self.govinfo_base_url}/packages/{package_id}/{fmt}"
                response = self.session.get(
                    content_url,
                    headers=headers,
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    if fmt == "xml":
                        # Parse and prettify XML
                        try:
                            root = ET.fromstring(response.text)
                            return ET.tostring(root, encoding="unicode")
                        except ET.ParseError:
                            return response.text
                    else:
                        return response.text

            except requests.exceptions.RequestException:
                continue

        return None

    def ingest_congress_bills(
        self,
        congress_number: int,
        bill_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Dict[str, int]:
        """Ingest bills from Congress.gov API.

        Args:
            congress_number: Congress number (e.g., 118 for 118th Congress)
            bill_type: Optional bill type filter (e.g., 'hr', 's', 'hjres', 'sjres')
            limit: Maximum number of bills to ingest (None for all)

        Returns:
            Dictionary with ingestion statistics
        """
        if not self.congress_api_key:
            logger.error("CONGRESS_API_KEY not configured")
            return self.stats

        logger.info(
            "Starting bulk ingestion for Congress %d bills%s",
            congress_number,
            f" (type: {bill_type})" if bill_type else ""
        )

        # Build API URL
        if bill_type:
            url = f"{self.congress_base_url}/bill/{congress_number}/{bill_type}"
        else:
            url = f"{self.congress_base_url}/bill/{congress_number}"

        params = {"api_key": self.congress_api_key, "format": "json"}

        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            bills = data.get("bills", [])
            if limit:
                bills = bills[:limit]

            logger.info("Found %d bills to process", len(bills))

            for idx, bill in enumerate(bills, 1):
                bill_number = bill.get("number")
                bill_type_code = bill.get("type")

                if not bill_number or not bill_type_code:
                    continue

                logger.info("Processing bill %d/%d: %s-%s", idx, len(bills), bill_type_code, bill_number)
                self._ingest_congress_bill(congress_number, bill_type_code, bill_number)
                time.sleep(RATE_LIMIT_DELAY)

        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch bills: %s", e)

        return self.stats

    def _ingest_congress_bill(self, congress: int, bill_type: str, bill_number: int) -> bool:
        """Ingest a single bill from Congress.gov.

        Args:
            congress: Congress number
            bill_type: Bill type code
            bill_number: Bill number

        Returns:
            True if successful, False otherwise
        """
        self.stats["total_documents"] += 1

        try:
            # Get bill details
            url = f"{self.congress_base_url}/bill/{congress}/{bill_type}/{bill_number}"
            params = {"api_key": self.congress_api_key, "format": "json"}

            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            bill_data = response.json().get("bill", {})

            # Extract bill text
            title = bill_data.get("title", f"{bill_type.upper()}{bill_number}")
            text_versions = bill_data.get("textVersions", {}).get("textVersions", [])

            if not text_versions:
                logger.warning("No text versions for bill %s%d", bill_type, bill_number)
                self.stats["skipped_documents"] += 1
                return False

            # Get the latest text version
            latest_version = text_versions[0]
            text_url = latest_version.get("formats", [{}])[0].get("url")

            if not text_url:
                logger.warning("No text URL for bill %s%d", bill_type, bill_number)
                self.stats["skipped_documents"] += 1
                return False

            # Fetch bill text
            text_response = self.session.get(text_url, timeout=self.timeout)
            text_response.raise_for_status()
            content = text_response.text

            # Prepare metadata
            metadata: DocumentMetadata = {
                "title": title,
                "source_url": bill_data.get("url", ""),
                "source_id": f"{congress}-{bill_type}-{bill_number}",
                "source_type": "congress_bill",
                "source_date": bill_data.get("introducedDate", ""),
                "source_collection": f"congress-{congress}",
                "created_at": datetime.now(),
                "document_type": "bill",
            }

            # Save to database
            doc_id = _save_document(content, metadata)
            if doc_id:
                logger.info("Successfully ingested bill %s-%d (doc_id: %s)", bill_type, bill_number, doc_id)
                self.stats["successful_ingestions"] += 1
                return True
            else:
                logger.error("Failed to save bill %s-%d to database", bill_type, bill_number)
                self.stats["failed_ingestions"] += 1
                return False

        except Exception as e:
            logger.error("Error processing bill %s-%d: %s", bill_type, bill_number, e)
            self.stats["failed_ingestions"] += 1
            return False

    def print_statistics(self):
        """Print ingestion statistics."""
        print("\n" + "="*60)
        print("Bulk Data Ingestion Statistics")
        print("="*60)
        print(f"Total documents processed: {self.stats['total_documents']}")
        print(f"Successful ingestions:     {self.stats['successful_ingestions']}")
        print(f"Failed ingestions:         {self.stats['failed_ingestions']}")
        print(f"Skipped documents:         {self.stats['skipped_documents']}")

        if self.stats['total_documents'] > 0:
            success_rate = (self.stats['successful_ingestions'] / self.stats['total_documents']) * 100
            print(f"Success rate:              {success_rate:.1f}%")
        print("="*60 + "\n")


def main():
    """Main function for bulk data ingestion."""
    import argparse

    parser = argparse.ArgumentParser(description="Bulk data ingestion for OpenDiscourse")
    parser.add_argument(
        "--source",
        choices=["govinfo", "congress"],
        required=True,
        help="Data source to ingest from"
    )
    parser.add_argument(
        "--collection",
        help="GovInfo collection code (e.g., BILLS, FR, CREC)"
    )
    parser.add_argument(
        "--congress",
        type=int,
        help="Congress number for Congress.gov API (e.g., 118)"
    )
    parser.add_argument(
        "--bill-type",
        help="Bill type for Congress.gov API (e.g., hr, s)"
    )
    parser.add_argument(
        "--start-date",
        help="Start date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--end-date",
        help="End date in YYYY-MM-DD format"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Maximum number of documents to ingest"
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="Directory for storing data"
    )

    args = parser.parse_args()

    # Initialize ingester
    ingester = BulkDataIngester(data_dir=args.data_dir)

    try:
        if args.source == "govinfo":
            if not args.collection:
                parser.error("--collection required for govinfo source")

            ingester.ingest_govinfo_collection(
                collection_code=args.collection,
                start_date=args.start_date,
                end_date=args.end_date,
                limit=args.limit
            )

        elif args.source == "congress":
            if not args.congress:
                parser.error("--congress required for congress source")

            ingester.ingest_congress_bills(
                congress_number=args.congress,
                bill_type=args.bill_type,
                limit=args.limit
            )

    except KeyboardInterrupt:
        logger.info("\nIngestion interrupted by user")
    except Exception as e:
        logger.error("Fatal error during ingestion: %s", e, exc_info=True)
    finally:
        ingester.print_statistics()


if __name__ == "__main__":
    main()
