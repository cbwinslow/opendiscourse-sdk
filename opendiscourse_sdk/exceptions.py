"""
Exception classes for the OpenDiscourse SDK.

This module defines all custom exceptions used throughout the SDK.
All exceptions inherit from OpenDiscourseSDKError for easy catching.

The exception hierarchy is:
    OpenDiscourseSDKError
    ├── APIError (HTTP errors from API)
    │   ├── AuthenticationError (401/403)
    │   ├── RateLimitError (429)
    │   └── NotFoundError (404)
    └── ValidationError (Data validation errors)

Author: OpenDiscourse Team
License: MIT
"""

from typing import Any, Dict, Optional


class OpenDiscourseSDKError(Exception):
    """
    Base exception for all OpenDiscourse SDK errors.
    
    All custom exceptions in the SDK inherit from this class,
    allowing users to catch all SDK-related errors with a single except clause.
    
    Attributes:
        message: Human-readable error message
        details: Additional error details (optional)
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Initialize the base exception.
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return a string representation of the error."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class APIError(OpenDiscourseSDKError):
    """
    Exception raised for API-related errors.
    
    This exception is raised when the API returns an error response.
    It includes the HTTP status code and response details.
    
    Attributes:
        message: Human-readable error message
        status_code: HTTP status code from the API
        response: The full response object (optional)
        details: Additional error details
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        response: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize an API error.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code from the API response
            response: The full response object from requests
            details: Optional dictionary with additional error context
        """
        self.status_code = status_code
        self.response = response
        super().__init__(message, details)

    def __str__(self) -> str:
        """Return a string representation including the status code."""
        return f"[HTTP {self.status_code}] {self.message}"


class AuthenticationError(APIError):
    """
    Exception raised for authentication failures.
    
    This exception is raised when:
    - API key is missing or invalid (401)
    - API key lacks required permissions (403)
    
    Example:
        >>> client = CongressClient(api_key="invalid_key")
        >>> try:
        ...     bills = client.bills.list(congress=118)
        ... except AuthenticationError as e:
        ...     print(f"Authentication failed: {e}")
    """

    def __init__(
        self,
        message: str = "Authentication failed. Please check your API key.",
        status_code: int = 401,
        response: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize an authentication error.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code (401 or 403)
            response: The full response object from requests
            details: Optional dictionary with additional error context
        """
        super().__init__(message, status_code, response, details)


class RateLimitError(APIError):
    """
    Exception raised when API rate limit is exceeded.
    
    This exception is raised when the API returns a 429 status code,
    indicating that too many requests have been made in a given timeframe.
    
    Attributes:
        retry_after: Number of seconds to wait before retrying (if provided by API)
    
    Example:
        >>> try:
        ...     for i in range(1000):
        ...         bills = client.bills.get(congress=118, bill_type="hr", number=i)
        ... except RateLimitError as e:
        ...     print(f"Rate limit exceeded. Retry after {e.retry_after} seconds")
        ...     time.sleep(e.retry_after)
    """

    def __init__(
        self,
        message: str = "API rate limit exceeded.",
        retry_after: Optional[int] = None,
        response: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a rate limit error.
        
        Args:
            message: Human-readable error message
            retry_after: Number of seconds to wait before retrying
            response: The full response object from requests
            details: Optional dictionary with additional error context
        """
        self.retry_after = retry_after
        super().__init__(message, 429, response, details)

    def __str__(self) -> str:
        """Return a string representation including retry time."""
        base_msg = super().__str__()
        if self.retry_after:
            return f"{base_msg} - Retry after {self.retry_after} seconds"
        return base_msg


class NotFoundError(APIError):
    """
    Exception raised when a requested resource is not found.
    
    This exception is raised when the API returns a 404 status code,
    indicating that the requested resource does not exist.
    
    Example:
        >>> try:
        ...     bill = client.bills.get(congress=118, bill_type="hr", number=99999)
        ... except NotFoundError:
        ...     print("Bill not found")
    """

    def __init__(
        self,
        message: str = "Requested resource not found.",
        response: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a not found error.
        
        Args:
            message: Human-readable error message
            response: The full response object from requests
            details: Optional dictionary with additional error context
        """
        super().__init__(message, 404, response, details)


class ValidationError(OpenDiscourseSDKError):
    """
    Exception raised for data validation errors.
    
    This exception is raised when:
    - Input parameters fail validation
    - Response data doesn't match expected schema
    - Pydantic model validation fails
    
    Example:
        >>> try:
        ...     bills = client.bills.list(congress="invalid")  # Should be int
        ... except ValidationError as e:
        ...     print(f"Validation error: {e}")
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize a validation error.
        
        Args:
            message: Human-readable error message
            field: Name of the field that failed validation (optional)
            details: Optional dictionary with additional error context
        """
        self.field = field
        if field and details is None:
            details = {"field": field}
        super().__init__(message, details)
