"""
GovInfo.gov API client implementation.

This module provides a Python client for interacting with the GovInfo.gov API.
It handles government documents, collections, and bulk data downloads.

Example:
    >>> from opendiscourse_sdk import GovInfoClient
    >>> client = GovInfoClient(api_key="your_key")
    >>> 
    >>> # List recent bills
    >>> packages = client.packages.list(
    ...     collection="BILLS",
    ...     start_date="2024-01-01"
    ... )
    >>> 
    >>> # Get a specific package
    >>> package = client.packages.get("BILLS-118hr1")
    >>> print(package.title)

Author: OpenDiscourse Team
License: MIT
"""

import os
from datetime import date
from typing import Optional

from opendiscourse_sdk.base import BaseClient
from opendiscourse_sdk.enums import GovInfoCollection, DocumentFormat
from opendiscourse_sdk.models.govinfo import (
    Collection,
    CollectionListResponse,
    Package,
    PackageListResponse,
    PackageSummary,
)


class PackagesResource:
    """
    Resource handler for package operations.
    
    Provides methods to interact with GovInfo packages (documents).
    
    Attributes:
        client: Parent GovInfoClient instance
    """
    
    def __init__(self, client: "GovInfoClient") -> None:
        """
        Initialize the packages resource.
        
        Args:
            client: Parent GovInfoClient instance
        """
        self.client = client
    
    def list(
        self,
        collection: GovInfoCollection,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        offset_mark: str = "*",
        page_size: int = 100,
    ) -> PackageListResponse:
        """
        List packages from a collection.
        
        Args:
            collection: Collection code (e.g., "BILLS", "FR", "CREC")
            start_date: Start date in YYYY-MM-DD format (for date-based collections)
            end_date: End date in YYYY-MM-DD format
            offset_mark: Pagination offset mark (use "*" for first page)
            page_size: Number of results per page (max: 1000)
        
        Returns:
            PackageListResponse with list of packages
        
        Example:
            >>> # Get bills from January 2024
            >>> packages = client.packages.list(
            ...     collection="BILLS",
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31"
            ... )
        """
        # Build endpoint
        if start_date:
            endpoint = f"/collections/{collection}/{start_date}"
            if end_date:
                endpoint = f"{endpoint}/{end_date}"
        else:
            endpoint = f"/collections/{collection}"
        
        # Build parameters
        params = {
            "offsetMark": offset_mark,
            "pageSize": min(page_size, 1000),  # API max is 1000
        }
        
        # Make request
        response_data = self.client.get(endpoint, params=params)
        return self.client.validate_response(response_data, PackageListResponse)
    
    def get(self, package_id: str) -> Package:
        """
        Get detailed information about a specific package.
        
        Args:
            package_id: Package identifier (e.g., "BILLS-118hr1")
        
        Returns:
            Package object with full details
        
        Example:
            >>> package = client.packages.get("BILLS-118hr1")
            >>> print(f"Title: {package.title}")
            >>> print(f"Issued: {package.date_issued}")
        """
        endpoint = f"/packages/{package_id}/summary"
        response_data = self.client.get(endpoint)
        return self.client.validate_response(response_data, Package)
    
    def get_content(
        self,
        package_id: str,
        content_type: DocumentFormat = DocumentFormat.XML,
    ) -> str:
        """
        Get the content of a package in specified format.
        
        Args:
            package_id: Package identifier
            content_type: Desired format (xml, htm, txt, pdf)
        
        Returns:
            Package content as string
        
        Example:
            >>> # Get bill text as XML
            >>> content = client.packages.get_content(
            ...     "BILLS-118hr1",
            ...     content_type="xml"
            ... )
        """
        endpoint = f"/packages/{package_id}/{content_type.value}"
        
        # Get response as text instead of JSON
        response = self.client.session.get(
            self.client._build_url(endpoint),
            params=self.client._prepare_params(),
            headers=self.client._prepare_headers(),
            timeout=self.client.timeout,
        )
        
        if response.status_code == 200:
            return response.text
        else:
            # Handle error using standard error handling
            return self.client._handle_response(response)


class CollectionsResource:
    """
    Resource handler for collection operations.
    
    Provides methods to interact with GovInfo collections.
    
    Attributes:
        client: Parent GovInfoClient instance
    """
    
    def __init__(self, client: "GovInfoClient") -> None:
        """
        Initialize the collections resource.
        
        Args:
            client: Parent GovInfoClient instance
        """
        self.client = client
    
    def list(self) -> CollectionListResponse:
        """
        List all available GovInfo collections.
        
        Returns:
            CollectionListResponse with list of collections
        
        Example:
            >>> collections = client.collections.list()
            >>> for collection in collections.collections:
            ...     print(f"{collection.collection_code}: {collection.collection_name}")
        """
        endpoint = "/collections"
        response_data = self.client.get(endpoint)
        return self.client.validate_response(response_data, CollectionListResponse)
    
    def get(self, collection_code: GovInfoCollection) -> Collection:
        """
        Get information about a specific collection.
        
        Args:
            collection_code: Collection code (e.g., "BILLS")
        
        Returns:
            Collection object with details
        
        Example:
            >>> collection = client.collections.get("BILLS")
            >>> print(f"Package count: {collection.package_count}")
        """
        endpoint = f"/collections/{collection_code}"
        response_data = self.client.get(endpoint)
        return self.client.validate_response(response_data, Collection)


class GovInfoClient(BaseClient):
    """
    Main client for GovInfo.gov API.
    
    Provides access to government publications and documents including:
    - Congressional bills and documents
    - Federal Register
    - Code of Federal Regulations
    - US Code
    - And 100+ other collections
    
    The client uses resource-based organization:
    - client.packages: Package/document operations
    - client.collections: Collection operations
    
    Attributes:
        packages: PackagesResource for package operations
        collections: CollectionsResource for collection operations
    
    Example:
        >>> from opendiscourse_sdk import GovInfoClient
        >>> 
        >>> # Initialize client
        >>> client = GovInfoClient(api_key="your_key")
        >>> 
        >>> # List collections
        >>> collections = client.collections.list()
        >>> 
        >>> # Get packages from a collection
        >>> packages = client.packages.list("BILLS", start_date="2024-01-01")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3,
    ) -> None:
        """
        Initialize the GovInfo.gov API client.
        
        Args:
            api_key: GovInfo.gov API key (or set GOVINFO_API_KEY env var)
            timeout: Request timeout in seconds (default: 30)
            rate_limit_delay: Delay between requests in seconds (default: 0.5)
            max_retries: Maximum number of retry attempts (default: 3)
        """
        # Get API key from parameter or environment
        api_key = api_key or os.getenv("GOVINFO_API_KEY")
        
        # Initialize base client
        super().__init__(
            base_url="https://api.govinfo.gov",
            api_key=api_key,
            timeout=timeout,
            rate_limit_delay=rate_limit_delay,
            max_retries=max_retries,
        )
        
        # Initialize resources
        self.packages = PackagesResource(self)
        self.collections = CollectionsResource(self)
    
    def _prepare_headers(self, headers: Optional[dict] = None) -> dict:
        """
        Prepare request headers for GovInfo API.
        
        GovInfo uses X-Api-Key header instead of query parameter.
        """
        headers = super()._prepare_headers(headers)
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        return headers
    
    def _prepare_params(self, params: Optional[dict] = None) -> dict:
        """
        Prepare request parameters for GovInfo API.
        
        GovInfo uses header authentication, so we don't add api_key to params.
        """
        prepared_params = params.copy() if params else {}
        # Remove None values
        prepared_params = {k: v for k, v in prepared_params.items() if v is not None}
        return prepared_params
