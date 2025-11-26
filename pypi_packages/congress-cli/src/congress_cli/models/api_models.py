"""
Pydantic models for Congress.gov API responses and data validation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re


class BillType(str, Enum):
    """Congress bill types."""
    HR = "hr"
    S = "s"
    HRES = "hres"
    SRES = "sres"
    HJRES = "hjres"
    SJRES = "sjres"
    HCONRES = "hconres"
    SCONRES = "sconres"


class Party(str, Enum):
    """Political parties."""
    DEMOCRAT = "D"
    REPUBLICAN = "R"
    INDEPENDENT = "I"
    LIBERTARIAN = "L"
    GREEN = "G"
    OTHER = "O"


class Chamber(str, Enum):
    """Congress chambers."""
    HOUSE = "House"
    SENATE = "Senate"


class CongressMember(BaseModel):
    """Congress member data model with validation."""

    bioguide_id: str = Field(..., description="Bioguide ID (unique identifier)")
    full_name: str = Field(..., description="Full name of the member")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    state: str = Field(..., description="State abbreviation (2 characters)")
    district: Optional[str] = Field(None, description="District number")
    party: Optional[Party] = Field(None, description="Political party")
    chamber: Chamber = Field(..., description="Chamber (House or Senate)")
    term_start: date = Field(..., description="Term start date")
    term_end: Optional[date] = Field(None, description="Term end date")
    url: Optional[str] = Field(None, description="Congress.gov URL")
    depiction: Optional[Dict[str, Any]] = Field(None, description="Member image data")

    @validator('bioguide_id')
    def validate_bioguide_id(cls, v):
        """Validate bioguide ID format."""
        if not re.match(r'^[A-Z0-9]{6,8}$', v):
            raise ValueError('Bioguide ID must be 6-8 alphanumeric characters')
        return v.upper()

    @validator('state')
    def validate_state(cls, v):
        """Validate state abbreviation."""
        if len(v) != 2 or not v.isalpha():
            raise ValueError('State must be 2-letter abbreviation')
        return v.upper()

    @validator('district')
    def validate_district(cls, v):
        """Validate district format."""
        if v is not None:
            if not re.match(r'^\d{1,2}$', v):
                raise ValueError('District must be 1-2 digits')
        return v

    @validator('term_start', 'term_end')
    def validate_dates(cls, v):
        """Validate date ranges."""
        if v and v > date.today():
            raise ValueError('Date cannot be in the future')
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }


class CongressBill(BaseModel):
    """Congress bill data model with validation."""

    bill_id: str = Field(..., description="Bill ID (e.g., 'hr118-1234')")
    title: str = Field(..., description="Bill title")
    congress: int = Field(..., description="Congress number (117, 118, etc.)")
    bill_type: BillType = Field(..., description="Bill type")
    chamber: Chamber = Field(..., description="Chamber")
    introduced_date: date = Field(..., description="Introduction date")
    sponsor_bioguide_id: Optional[str] = Field(None, description="Sponsor bioguide ID")
    cosponsors: List[Dict[str, Any]] = Field(default_factory=list, description="Cosponsors")
    committees: List[Dict[str, Any]] = Field(default_factory=list, description="Committees")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Bill actions")
    text_versions: List[Dict[str, Any]] = Field(default_factory=list, description="Text versions")
    latest_action: Optional[Dict[str, Any]] = Field(None, description="Latest action")
    status: Optional[str] = Field(None, description="Bill status")
    url: Optional[str] = Field(None, description="Congress.gov URL")

    @validator('bill_id')
    def validate_bill_id(cls, v):
        """Validate bill ID format."""
        if not re.match(r'^[a-z]{1,4}\d{3}-\d{4}$', v.lower()):
            raise ValueError('Bill ID must be in format like "hr118-1234"')
        return v.lower()

    @validator('congress')
    def validate_congress(cls, v):
        """Validate Congress number."""
        if v < 93 or v > 120:  # Reasonable range
            raise ValueError('Congress number must be between 93 and 120')
        return v

    @validator('sponsor_bioguide_id')
    def validate_sponsor_bioguide_id(cls, v):
        """Validate sponsor bioguide ID."""
        if v is not None:
            if not re.match(r'^[A-Z0-9]{6,8}$', v):
                raise ValueError('Sponsor bioguide ID must be 6-8 alphanumeric characters')
            return v.upper()
        return v

    @validator('introduced_date')
    def validate_introduced_date(cls, v):
        """Validate introduction date."""
        if v > date.today():
            raise ValueError('Introduction date cannot be in the future')
        return v

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat(),
            datetime: lambda v: v.isoformat(),
        }


class APIResponse(BaseModel):
    """Generic API response model for Congress.gov."""

    count: int = Field(..., description="Total number of results")
    next_offset: Optional[str] = Field(None, description="Next offset for pagination")
    next_url: Optional[str] = Field(None, description="Next URL for pagination")
    request: Dict[str, Any] = Field(..., description="Request metadata")
    results: List[Dict[str, Any]] = Field(..., description="API results")

    @validator('count')
    def validate_count(cls, v):
        """Validate result count."""
        if v < 0:
            raise ValueError('Count cannot be negative')
        return v

    @validator('results')
    def validate_results_not_empty(cls, v):
        """Validate results list."""
        if not isinstance(v, list):
            raise ValueError('Results must be a list')
        return v

    @validator('next_offset')
    def validate_next_offset(cls, v):
        """Validate next offset."""
        if v is not None:
            try:
                int(v)
            except ValueError:
                raise ValueError('Next offset must be a valid integer string')
        return v


class MemberResponse(BaseModel):
    """Specific response model for member endpoints."""

    member: CongressMember = Field(..., description="Member data")
    request: Dict[str, Any] = Field(..., description="Request metadata")


class BillResponse(BaseModel):
    """Specific response model for bill endpoints."""

    bill: CongressBill = Field(..., description="Bill data")
    request: Dict[str, Any] = Field(..., description="Request metadata")


class PaginationInfo(BaseModel):
    """Pagination information model."""

    count: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Current offset")
    next_offset: Optional[int] = Field(None, description="Next offset")
    prev_offset: Optional[int] = Field(None, description="Previous offset")
    total_pages: int = Field(..., description="Total number of pages")
    current_page: int = Field(..., description="Current page number")

    @validator('total_pages')
    def calculate_total_pages(cls, v, values):
        """Calculate total pages from count and limit."""
        if 'count' in values and 'limit' in values:
            calculated = (values['count'] + values['limit'] - 1) // values['limit']
            if v != calculated:
                raise ValueError('Total pages calculation mismatch')
        return v


class IngestionCheckpoint(BaseModel):
    """Ingestion checkpoint model."""

    data_source: str = Field(..., description="Data source name")
    data_type: str = Field(..., description="Data type (members, bills, etc.)")
    category: Optional[str] = Field(None, description="Category (congress number, etc.)")
    offset: str = Field(..., description="Current offset")
    total_processed: int = Field(..., description="Total items processed")
    last_ingestion_at: datetime = Field(..., description="Last ingestion timestamp")
    status: str = Field(..., description="Status (active, completed, failed)")
    created_at: datetime = Field(..., description="Checkpoint creation timestamp")
    updated_at: datetime = Field(..., description="Checkpoint update timestamp")

    @validator('status')
    def validate_status(cls, v):
        """Validate status value."""
        valid_statuses = ['active', 'completed', 'failed', 'paused']
        if v not in valid_statuses:
            raise ValueError(f'Status must be one of: {valid_statuses}')
        return v


class IngestionMetrics(BaseModel):
    """Ingestion performance metrics."""

    total_items: int = Field(..., description="Total items to process")
    processed_items: int = Field(..., description="Items processed so far")
    failed_items: int = Field(..., description="Items that failed")
    start_time: datetime = Field(..., description="Process start time")
    current_time: datetime = Field(..., description="Current time")
    items_per_second: float = Field(..., description="Processing rate")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        total_attempted = self.processed_items + self.failed_items
        if total_attempted == 0:
            return 100.0
        return (self.processed_items / total_attempted) * 100


class DatabaseConfig(BaseModel):
    """Database configuration model."""

    host: str = Field(..., description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    ssl_mode: str = Field(default="prefer", description="SSL mode")

    @validator('port')
    def validate_port(cls, v):
        """Validate port number."""
        if not 1 <= v <= 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v

    def get_connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return (
            f"postgresql://{self.username}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}?sslmode={self.ssl_mode}"
        )


class APIConfig(BaseModel):
    """API configuration model."""

    api_key: str = Field(..., description="API key")
    base_url: str = Field(..., description="Base URL")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    rate_limit_per_second: int = Field(default=10, description="Rate limit")
    max_retries: int = Field(default=3, description="Maximum retries")
    retry_backoff_factor: float = Field(default=2.0, description="Retry backoff factor")

    @validator('timeout_seconds')
    def validate_timeout(cls, v):
        """Validate timeout."""
        if v < 1 or v > 300:
            raise ValueError('Timeout must be between 1 and 300 seconds')
        return v

    @validator('rate_limit_per_second')
    def validate_rate_limit(cls, v):
        """Validate rate limit."""
        if v < 1 or v > 100:
            raise ValueError('Rate limit must be between 1 and 100 requests per second')
        return v


class IngestionConfig(BaseModel):
    """Ingestion configuration model."""

    database: DatabaseConfig = Field(..., description="Database configuration")
    api: APIConfig = Field(..., description="API configuration")
    batch_size: int = Field(default=100, description="Batch processing size")
    max_workers: int = Field(default=4, description="Maximum parallel workers")
    checkpoint_interval: int = Field(default=1000, description="Checkpoint save interval")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")
    log_level: str = Field(default="INFO", description="Log level")

    @validator('batch_size')
    def validate_batch_size(cls, v):
        """Validate batch size."""
        if v < 1 or v > 10000:
            raise ValueError('Batch size must be between 1 and 10000')
        return v

    @validator('max_workers')
    def validate_max_workers(cls, v):
        """Validate max workers."""
        if v < 1 or v > 32:
            raise ValueError('Max workers must be between 1 and 32')
        return v

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


# Type aliases for better readability
MemberList = List[CongressMember]
BillList = List[CongressBill]
APIResult = Union[APIResponse, MemberResponse, BillResponse]
