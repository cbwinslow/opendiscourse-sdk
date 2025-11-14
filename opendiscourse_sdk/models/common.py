"""
Common Pydantic models shared across all APIs.

This module defines base models and common response structures
that are used by multiple API clients.

Author: OpenDiscourse Team
License: MIT
"""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, ConfigDict

# Type variable for generic pagination
T = TypeVar("T")


class BaseResponse(BaseModel):
    """
    Base response model for all API responses.
    
    Provides common configuration for all response models.
    """
    
    model_config = ConfigDict(
        # Allow extra fields that aren't defined in the model
        extra="allow",
        # Convert attribute names from camelCase to snake_case
        populate_by_name=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
    )


class ErrorResponse(BaseResponse):
    """
    Standard error response from APIs.
    
    Attributes:
        error: Error message
        code: Error code (optional)
        details: Additional error details (optional)
    
    Example:
        >>> response = ErrorResponse(
        ...     error="Resource not found",
        ...     code="NOT_FOUND",
        ...     details={"resource_id": "123"}
        ... )
    """
    
    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseResponse):
    """
    Standard success response from APIs.
    
    Attributes:
        message: Success message
        data: Response data (optional)
    
    Example:
        >>> response = SuccessResponse(
        ...     message="Operation completed successfully",
        ...     data={"id": "123", "status": "active"}
        ... )
    """
    
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


class BasePaginatedResponse(BaseResponse, Generic[T]):
    """
    Base paginated response model.
    
    Provides pagination metadata for list endpoints.
    
    Attributes:
        results: List of items in current page
        count: Total number of items across all pages
        next: URL for next page (if available)
        previous: URL for previous page (if available)
        page: Current page number (optional)
        page_size: Number of items per page (optional)
        total_pages: Total number of pages (optional)
    
    Example:
        >>> from opendiscourse_sdk.models.congress import Bill
        >>> response = BasePaginatedResponse[Bill](
        ...     results=[bill1, bill2, bill3],
        ...     count=100,
        ...     page=1,
        ...     page_size=10,
        ...     total_pages=10
        ... )
    """
    
    results: List[T] = Field(default_factory=list, description="List of results")
    count: int = Field(0, description="Total number of results")
    next: Optional[str] = Field(None, description="URL for next page")
    previous: Optional[str] = Field(None, description="URL for previous page")
    page: Optional[int] = Field(None, description="Current page number")
    page_size: Optional[int] = Field(None, description="Number of items per page")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


class Address(BaseModel):
    """
    Physical address model.
    
    Used for member offices, committee locations, etc.
    
    Attributes:
        street: Street address
        city: City name
        state: State/province
        zip_code: Postal/ZIP code
        country: Country code (default: US)
    """
    
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State or province")
    zip_code: Optional[str] = Field(None, description="Postal/ZIP code", alias="zipCode")
    country: str = Field("US", description="Country code")
    
    model_config = ConfigDict(populate_by_name=True)


class ContactInfo(BaseModel):
    """
    Contact information model.
    
    Used for members, staff, and offices.
    
    Attributes:
        phone: Phone number
        fax: Fax number
        email: Email address
        website: Website URL
        social_media: Social media handles
    """
    
    phone: Optional[str] = Field(None, description="Phone number")
    fax: Optional[str] = Field(None, description="Fax number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    social_media: Optional[Dict[str, str]] = Field(
        None,
        description="Social media handles",
        alias="socialMedia"
    )
    
    model_config = ConfigDict(populate_by_name=True)


class DateRange(BaseModel):
    """
    Date range model.
    
    Used for terms, sessions, and time periods.
    
    Attributes:
        start_date: Start date
        end_date: End date (optional for ongoing periods)
    """
    
    start_date: datetime = Field(..., description="Start date", alias="startDate")
    end_date: Optional[datetime] = Field(None, description="End date", alias="endDate")
    
    model_config = ConfigDict(populate_by_name=True)
    
    @property
    def is_active(self) -> bool:
        """Check if the date range is currently active."""
        now = datetime.now()
        if self.end_date:
            return self.start_date <= now <= self.end_date
        return self.start_date <= now


class Link(BaseModel):
    """
    URL link model.
    
    Used for references to related resources.
    
    Attributes:
        url: URL to the resource
        title: Link title/description
        type: Link type (e.g., 'api', 'web', 'pdf')
    """
    
    url: str = Field(..., description="URL to the resource")
    title: Optional[str] = Field(None, description="Link title or description")
    type: Optional[str] = Field(None, description="Link type")


class Identifier(BaseModel):
    """
    External identifier model.
    
    Used to track IDs in different systems (e.g., bioguide, govtrack).
    
    Attributes:
        system: Identifier system name
        value: Identifier value
    """
    
    system: str = Field(..., description="Identifier system name")
    value: str = Field(..., description="Identifier value")


class Metadata(BaseModel):
    """
    Generic metadata model.
    
    Used for storing arbitrary key-value metadata.
    
    Attributes:
        source: Data source
        retrieved_at: Timestamp when data was retrieved
        version: Data version
        extra: Additional metadata fields
    """
    
    source: Optional[str] = Field(None, description="Data source")
    retrieved_at: Optional[datetime] = Field(
        None,
        description="Timestamp when data was retrieved",
        alias="retrievedAt"
    )
    version: Optional[str] = Field(None, description="Data version")
    extra: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    model_config = ConfigDict(populate_by_name=True)


class Statistics(BaseModel):
    """
    Statistics model for aggregated data.
    
    Used for vote counts, sponsorship counts, etc.
    
    Attributes:
        total: Total count
        breakdown: Breakdown by category
        percentage: Percentage value (0-100)
    """
    
    total: int = Field(0, description="Total count")
    breakdown: Optional[Dict[str, int]] = Field(None, description="Breakdown by category")
    percentage: Optional[float] = Field(None, description="Percentage value", ge=0, le=100)
