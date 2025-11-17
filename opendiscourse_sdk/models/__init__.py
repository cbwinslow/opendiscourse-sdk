"""
Pydantic models for the OpenDiscourse SDK.

This package contains all data models used throughout the SDK.
Models are organized by API source:
- common: Shared models used across multiple APIs
- congress: Models for Congress.gov API
- govinfo: Models for GovInfo.gov API
- openstates: Models for OpenStates API

All models use Pydantic for:
- Automatic validation
- Type safety
- JSON serialization/deserialization
- Documentation generation

Author: OpenDiscourse Team
License: MIT
"""

# Import common models that are used across multiple APIs
from opendiscourse_sdk.models.common import (
    BasePaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)

__all__ = [
    "BasePaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
]
