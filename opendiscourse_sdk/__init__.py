"""
OpenDiscourse SDK - A Python library for interacting with government legislative APIs.

This SDK provides a unified interface for accessing data from:
- Congress.gov API (Federal legislative data)
- GovInfo.gov API (Government publications and documents)
- OpenStates API (State-level legislative data)

The SDK follows object-oriented programming principles with:
- Strong typing using Pydantic models
- Comprehensive error handling
- Detailed documentation
- PyPI-ready packaging

Example:
    >>> from opendiscourse_sdk import CongressClient, GovInfoClient, OpenStatesClient
    >>> congress = CongressClient(api_key="your_key")
    >>> bills = congress.bills.list(congress=118, bill_type="hr", limit=10)
    >>> for bill in bills:
    ...     print(f"{bill.bill_number}: {bill.title}")

Author: OpenDiscourse Team
License: MIT
Version: 1.0.0
"""

try:
    from opendiscourse_sdk.congress.client import CongressClient
    from opendiscourse_sdk.exceptions import (
        APIError,
        AuthenticationError,
        NotFoundError,
        OpenDiscourseSDKError,
        RateLimitError,
        ValidationError,
    )
    from opendiscourse_sdk.govinfo.client import GovInfoClient
    from opendiscourse_sdk.openstates.client import OpenStatesClient
except ImportError as e:
    # Fallback if dependencies aren't installed
    import warnings
    warnings.warn(f"Some SDK components could not be imported: {e}")
    CongressClient = None
    GovInfoClient = None
    OpenStatesClient = None

__version__ = "1.0.0"
__author__ = "OpenDiscourse Team"
__license__ = "MIT"

__all__ = [
    # Clients
    "CongressClient",
    "GovInfoClient",
    "OpenStatesClient",
    # Exceptions
    "OpenDiscourseSDKError",
    "APIError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    # Metadata
    "__version__",
    "__author__",
    "__license__",
]
