"""
Pydantic models for GovInfo.gov API.

This module defines all data models for the GovInfo.gov API including:
- Collections and packages
- Documents and granules
- Bulk data downloads

Author: OpenDiscourse Team
License: MIT
"""

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, ConfigDict

from opendiscourse_sdk.enums import GovInfoCollection, DocumentFormat
from opendiscourse_sdk.models.common import BaseResponse


class PackageSummary(BaseResponse):
    """
    Summary information for a GovInfo package.
    
    Attributes:
        package_id: Unique package identifier
        title: Document title
        collection_code: Collection this package belongs to
        date_issued: Date document was issued
        last_modified: Last modification timestamp
        download_urls: URLs for downloading in different formats
    """
    
    package_id: str = Field(..., description="Package ID", alias="packageId")
    title: str = Field(..., description="Document title")
    collection_code: GovInfoCollection = Field(..., description="Collection code", alias="collectionCode")
    date_issued: Optional[date] = Field(None, description="Issue date", alias="dateIssued")
    last_modified: Optional[datetime] = Field(None, description="Last modified", alias="lastModified")
    download_urls: Dict[str, HttpUrl] = Field(default_factory=dict, description="Download URLs", alias="downloadUrls")
    
    model_config = ConfigDict(populate_by_name=True)


class Package(BaseResponse):
    """
    Complete package information with metadata.
    
    Attributes:
        package_id: Unique package identifier
        title: Document title
        collection_code: Collection code
        date_issued: Issue date
        last_modified: Last modification timestamp
        congress: Congress number (if applicable)
        chamber: Chamber (if applicable)
        bill_type: Bill type (if applicable)
        bill_number: Bill number (if applicable)
        doc_class: Document class
        download: Download URLs by format
        metadata: Additional metadata
        summary: Package summary
        related_packages: Related package IDs
    """
    
    package_id: str = Field(..., description="Package ID", alias="packageId")
    title: str = Field(..., description="Document title")
    collection_code: GovInfoCollection = Field(..., description="Collection", alias="collectionCode")
    date_issued: Optional[date] = Field(None, description="Issue date", alias="dateIssued")
    last_modified: Optional[datetime] = Field(None, description="Last modified", alias="lastModified")
    congress: Optional[int] = Field(None, description="Congress number")
    chamber: Optional[str] = Field(None, description="Chamber")
    bill_type: Optional[str] = Field(None, description="Bill type", alias="billType")
    bill_number: Optional[str] = Field(None, description="Bill number", alias="billNumber")
    doc_class: Optional[str] = Field(None, description="Document class", alias="docClass")
    download: Dict[str, HttpUrl] = Field(default_factory=dict, description="Download URLs")
    metadata: Dict[str, any] = Field(default_factory=dict, description="Metadata")
    summary: Optional[str] = Field(None, description="Summary")
    related_packages: List[str] = Field(default_factory=list, description="Related packages", alias="relatedPackages")
    
    model_config = ConfigDict(populate_by_name=True)


class Collection(BaseResponse):
    """
    GovInfo collection information.
    
    Attributes:
        collection_code: Unique collection code
        collection_name: Collection display name
        package_count: Number of packages in collection
        granule_count: Number of granules in collection
        description: Collection description
    """
    
    collection_code: GovInfoCollection = Field(..., description="Collection code", alias="collectionCode")
    collection_name: str = Field(..., description="Collection name", alias="collectionName")
    package_count: Optional[int] = Field(None, description="Package count", alias="packageCount")
    granule_count: Optional[int] = Field(None, description="Granule count", alias="granuleCount")
    description: Optional[str] = Field(None, description="Description")
    
    model_config = ConfigDict(populate_by_name=True)


class PackageListResponse(BaseResponse):
    """Response from packages list endpoint."""
    
    packages: List[PackageSummary] = Field(default_factory=list, description="Packages")
    count: int = Field(0, description="Total count")
    next_page: Optional[str] = Field(None, description="Next page", alias="nextPage")
    offset_mark: Optional[str] = Field(None, description="Offset mark for pagination", alias="offsetMark")
    
    model_config = ConfigDict(populate_by_name=True)


class CollectionListResponse(BaseResponse):
    """Response from collections list endpoint."""
    
    collections: List[Collection] = Field(default_factory=list, description="Collections")
    count: int = Field(0, description="Total count")
    
    model_config = ConfigDict(populate_by_name=True)
