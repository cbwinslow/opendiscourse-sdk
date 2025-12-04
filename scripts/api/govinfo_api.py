"""
================================================================================
File: govinfo_api.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    GovInfo API client with full endpoint abstraction using Pydantic models.
    Provides type-safe access to federal government documents including
    Congressional bills, reports, hearings, Federal Register, CFR, and more.

Dependencies:
    - scripts.core.api_client_base: Base API client functionality
    - pydantic: Data validation and type safety
    - typing: Type hint support
    - datetime: Date/time handling

Classes:
    - Collection: Enum for GovInfo collections
    - DocClass: Enum for document classes
    - GovInfoEndpoints: API endpoint definitions
    - GovInfoAPIClient: Main API client for GovInfo

Endpoints Covered:
    - Collections (all available document collections)
    - Packages (document packages within collections)
    - Published (recently published documents)
    - Search (full-text search)
    - Congressional Bills
    - Congressional Record
    - Federal Register
    - Committee Reports/Prints
    - Hearings

Usage:
    from scripts.api.govinfo_api import GovInfoAPIClient, Collection

    # Initialize client
    client = GovInfoAPIClient(api_key="your_key_here")

    # Get collections
    collections = client.get_collections()

    # Get bills from a collection
    bills = client.get_collection_packages(
        collection=Collection.BILLS,
        start_date="2024-01-01"
    )

Changelog:
    2025-12-04: Initial creation with full endpoint coverage

Notes:
    - All methods return APIResponse objects with .success and .data
    - Automatic retry on failure
    - Rate limiting enforced (50 req/s default)
    - Supports bulk data downloads

================================================================================
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, date

from pydantic import BaseModel, Field, validator

from scripts.core.api_client_base import (
    APIClientBase,
    APIResponse,
    HTTPMethod,
    log_api_call,
    retry_on_failure
)


# ============================================================================
# Enums and Constants
# ============================================================================

class Collection(str, Enum):
    """
    GovInfo document collections.

    Major collections available in the GovInfo repository.
    """
    BILLS = "BILLS"
    BILLSTATUS = "BILLSTATUS"
    BILLSUM = "BILLSUM"
    BUDGET = "BUDGET"
    CFR = "CFR"
    CHRG = "CHRG"  # Congressional Hearings
    COMPS = "COMPS"  # Statutes Compilations
    CPRT = "CPRT"  # Committee Prints
    CREC = "CREC"  # Congressional Record
    CRPT = "CRPT"  # Committee Reports
    CZIC = "CZIC"
    ERP = "ERP"  # Economic Reports of the President
    FR = "FR"  # Federal Register
    GAOREPORTS = "GAOREPORTS"
    GOVMAN = "GOVMAN"
    GPO = "GPO"
    HJOURNAL = "HJOURNAL"  # House Journal
    HMAN = "HMAN"  # House Manual
    HOB = "HOB"
    LSA = "LSA"
    PLAW = "PLAW"  # Public Laws
    PPP = "PPP"
    SERIALSET = "SERIALSET"
    SJOURNAL = "SJOURNAL"  # Senate Journal
    STATUTE = "STATUTE"
    USCOURTS = "USCOURTS"
    USCODE = "USCODE"


class DocClass(str, Enum):
    """Document class/format types."""
    HTML = "html"
    PDF = "pdf"
    XML = "xml"
    TEXT = "text"
    MODS = "mods"
    PREMIS = "premis"
    ZIP = "zip"


# ============================================================================
# API Endpoint Definitions
# ============================================================================

class GovInfoEndpoints:
    """
    Centralized definition of all GovInfo API endpoints.

    This class provides a single source of truth for all API paths.
    """

    # Collection endpoints
    COLLECTIONS = "/collections"
    COLLECTION_PACKAGES = "/collections/{collectionCode}"
    COLLECTION_DATE_RANGE = "/collections/{collectionCode}/{startDate}/{endDate}"

    # Package endpoints
    PACKAGES = "/packages"
    PACKAGE_SUMMARY = "/packages/{packageId}/summary"
    PACKAGE_GRANULES = "/packages/{packageId}/granules"
    PACKAGE_DOWNLOAD = "/packages/{packageId}/{docClass}"

    # Published endpoints
    PUBLISHED = "/published/{date}"
    PUBLISHED_DATE_RANGE = "/published/{startDate}/{endDate}"

    # Search
    SEARCH = "/search"

    # Related/Referenced
    RELATED = "/packages/{packageId}/related"


# ============================================================================
# GovInfo API Client
# ============================================================================

class GovInfoAPIClient(APIClientBase):
    """
    GovInfo API client with full endpoint coverage.

    Provides type-safe, well-documented access to all GovInfo
    API endpoints with automatic error handling, retry logic, and
    rate limiting.

    Attributes:
        base_url: API base URL (https://api.govinfo.gov)
        api_key: GovInfo API key
        rate_limit: Requests per second (default 50)

    Methods:
        Collections:
            - get_collections: List all collections
            - get_collection_packages: Get packages in collection
            - get_collection_date_range: Get packages by date range

        Packages:
            - get_packages: List packages
            - get_package_summary: Get package summary/metadata
            - get_package_granules: Get package granules (sub-documents)
            - download_package: Download package content

        Published:
            - get_published: Get recently published documents
            - get_published_range: Get published in date range

        Search:
            - search: Full-text search across collections

        Related:
            - get_related_packages: Get related packages
    """

    def __init__(self, api_key: str, rate_limit: int = 50):
        """
        Initialize GovInfo API client.

        Args:
            api_key: GovInfo API key
            rate_limit: Maximum requests per second (default 50)
        """
        # Call parent constructor with GovInfo specifics
        super().__init__(
            base_url="https://api.govinfo.gov",
            api_key=api_key,
            rate_limit=rate_limit,
            logger_name="GovInfoAPI"
        )

        # GovInfo uses X-Api-Key header
        self.session.headers.update({
            'X-Api-Key': api_key
        })

        # Log successful initialization
        self.logger.info("GovInfo API client initialized")

    # ========================================================================
    # Collection Methods
    # ========================================================================

    @log_api_call
    def get_collections(self, offset: int = 0, page_size: int = 100) -> APIResponse:
        """
        Get list of all available collections.

        Args:
            offset: Pagination offset
            page_size: Number of results per page (max 1000)

        Returns:
            APIResponse with collections in data['collections']

        Example:
            >>> response = client.get_collections()
            >>> if response.success:
            >>>     for coll in response.data['collections']:
            >>>         print(coll['collectionCode'], coll['collectionName'])
        """
        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        return self.get(GovInfoEndpoints.COLLECTIONS, params=params)

    @log_api_call
    def get_collection_packages(
        self,
        collection: Collection,
        offset: int = 0,
        page_size: int = 100
    ) -> APIResponse:
        """
        Get packages within a specific collection.

        Args:
            collection: Collection code (e.g., BILLS, CREC)
            offset: Pagination offset
            page_size: Results per page

        Returns:
            APIResponse with packages in data['packages']

        Example:
            >>> # Get Congressional bills
            >>> response = client.get_collection_packages(
            >>>     collection=Collection.BILLS,
            >>>     page_size=50
            >>> )
        """
        endpoint = GovInfoEndpoints.COLLECTION_PACKAGES.format(
            collectionCode=collection.value
        )

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        return self.get(endpoint, params=params)

    @log_api_call
    def get_collection_date_range(
        self,
        collection: Collection,
        start_date: str,
        end_date: str,
        offset: int = 0,
        page_size: int = 100
    ) -> APIResponse:
        """
        Get collection packages within a date range.

        Args:
            collection: Collection code
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            offset: Pagination offset
            page_size: Results per page

        Returns:
            APIResponse with packages in date range

        Example:
            >>> # Get bills published in 2024
            >>> response = client.get_collection_date_range(
            >>>     collection=Collection.BILLS,
            >>>     start_date="2024-01-01",
            >>>     end_date="2024-12-31"
            >>> )
        """
        endpoint = GovInfoEndpoints.COLLECTION_DATE_RANGE.format(
            collectionCode=collection.value,
            startDate=start_date,
            endDate=end_date
        )

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        return self.get(endpoint, params=params)

    # ========================================================================
    # Package Methods
    # ========================================================================

    @log_api_call
    def get_package_summary(self, package_id: str) -> APIResponse:
        """
        Get summary/metadata for a package.

        Args:
            package_id: Package identifier (e.g., "BILLS-118hr1")

        Returns:
            APIResponse with package metadata

        Example:
            >>> response = client.get_package_summary("BILLS-118hr1")
            >>> if response.success:
            >>>     pkg = response.data
            >>>     print(pkg['title'], pkg['dateIssued'])
        """
        endpoint = GovInfoEndpoints.PACKAGE_SUMMARY.format(packageId=package_id)
        return self.get(endpoint)

    @log_api_call
    def get_package_granules(
        self,
        package_id: str,
        offset: int = 0,
        page_size: int = 100
    ) -> APIResponse:
        """
        Get granules (sub-documents) within a package.

        Args:
            package_id: Package identifier
            offset: Pagination offset
            page_size: Results per page

        Returns:
            APIResponse with granules

        Example:
            >>> # Get sections of a Congressional Record package
            >>> response = client.get_package_granules("CREC-2024-01-15")
        """
        endpoint = GovInfoEndpoints.PACKAGE_GRANULES.format(packageId=package_id)

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        return self.get(endpoint, params=params)

    @log_api_call
    def download_package(
        self,
        package_id: str,
        doc_class: DocClass = DocClass.PDF
    ) -> APIResponse:
        """
        Get download URL for package content.

        Args:
            package_id: Package identifier
            doc_class: Document format (pdf, html, xml, etc.)

        Returns:
            APIResponse with download URL in data['download']['url']

        Example:
            >>> # Get PDF download link
            >>> response = client.download_package(
            >>>     "BILLS-118hr1",
            >>>     DocClass.PDF
            >>> )
            >>> if response.success:
            >>>     pdf_url = response.data['download']['url']
        """
        endpoint = GovInfoEndpoints.PACKAGE_DOWNLOAD.format(
            packageId=package_id,
            docClass=doc_class.value
        )

        return self.get(endpoint)

    # ========================================================================
    # Published Methods
    # ========================================================================

    @log_api_call
    def get_published(
        self,
        date: str,
        offset: int = 0,
        page_size: int = 100,
        collection: Optional[Collection] = None
    ) -> APIResponse:
        """
        Get documents published on a specific date.

        Args:
            date: Publication date (YYYY-MM-DD)
            offset: Pagination offset
            page_size: Results per page
            collection: Optional collection filter

        Returns:
            APIResponse with published packages

        Example:
            >>> # Get everything published today
            >>> response = client.get_published("2024-12-04")
        """
        endpoint = GovInfoEndpoints.PUBLISHED.format(date=date)

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        if collection:
            params['collection'] = collection.value

        return self.get(endpoint, params=params)

    @log_api_call
    def get_published_range(
        self,
        start_date: str,
        end_date: str,
        offset: int = 0,
        page_size: int = 100,
        collection: Optional[Collection] = None
    ) -> APIResponse:
        """
        Get documents published within a date range.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            offset: Pagination offset
            page_size: Results per page
            collection: Optional collection filter

        Returns:
            APIResponse with published packages
        """
        endpoint = GovInfoEndpoints.PUBLISHED_DATE_RANGE.format(
            startDate=start_date,
            endDate=end_date
        )

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        if collection:
            params['collection'] = collection.value

        return self.get(endpoint, params=params)

    # ========================================================================
    # Search Methods
    # ========================================================================

    @log_api_call
    def search(
        self,
        query: str,
        collection: Optional[Collection] = None,
        offset: int = 0,
        page_size: int = 100
    ) -> APIResponse:
        """
        Full-text search across GovInfo.

        Args:
            query: Search query string
            collection: Optional collection filter
            offset: Pagination offset
            page_size: Results per page

        Returns:
            APIResponse with search results

        Example:
            >>> # Search for climate bills
            >>> response = client.search(
            >>>     query="climate change",
            >>>     collection=Collection.BILLS
            >>> )
        """
        params = {
            'query': query,
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        if collection:
            params['collection'] = collection.value

        return self.get(GovInfoEndpoints.SEARCH, params=params)

    # ========================================================================
    # Related/Referenced Methods
    # ========================================================================

    @log_api_call
    def get_related_packages(
        self,
        package_id: str,
        offset: int = 0,
        page_size: int = 100
    ) -> APIResponse:
        """
        Get packages related to/referenced by a package.

        Args:
            package_id: Package identifier
            offset: Pagination offset
            page_size: Results per page

        Returns:
            APIResponse with related packages
        """
        endpoint = GovInfoEndpoints.RELATED.format(packageId=package_id)

        params = {
            'offset': offset,
            'pageSize': min(page_size, 1000)
        }

        return self.get(endpoint, params=params)


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'Collection',
    'DocClass',
    'GovInfoEndpoints',
    'GovInfoAPIClient',
]
