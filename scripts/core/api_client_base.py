"""
================================================================================
File: api_client_base.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Abstract base class for API clients with comprehensive error handling,
    retry logic, rate limiting, and logging. Provides full abstraction of
    HTTP operations with Pydantic model validation.

Dependencies:
    - requests: HTTP client library
    - pydantic: Data validation and settings management
    - typing: Type hints
    - logging: Python logging framework
    - time: Sleep/retry functionality
    - functools: Decorator utilities

Classes:
    - APIEndpoint: Pydantic model for endpoint configuration
    - APIResponse: Pydantic model for API responses
    - APIClientBase: Abstract base class for all API clients

Usage:
    from scripts.core.api_client_base import APIClientBase, APIEndpoint

    class CongressAPIClient(APIClientBase):
        def __init__(self, api_key: str):
            super().__init__(
                base_url="https://api.congress.gov/v3",
                api_key=api_key,
                rate_limit=100
            )

Changelog:
    2025-12-04: Initial creation with full Pydantic integration

Notes:
    - All API calls are rate-limited
    - Automatic retry with exponential backoff
    - Comprehensive error logging
    - Type-safe with Pydantic models

================================================================================
"""

import time
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Callable
from functools import wraps
from datetime import datetime
from enum import Enum

import requests
from pydantic import BaseModel, Field, validator
from requests.exceptions import RequestException, HTTPError, Timeout


# ============================================================================
# Type Definitions and Enums
# ============================================================================

class HTTPMethod(str, Enum):
    """HTTP methods supported by the API client."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class RetryStrategy(str, Enum):
    """Retry strategy options."""
    EXPONENTIAL = "exponential"  # Exponential backoff (2^attempt * base_delay)
    LINEAR = "linear"            # Linear backoff (attempt * base_delay)
    FIXED = "fixed"              # Fixed delay between retries


# ============================================================================
# Pydantic Models
# ============================================================================

class APIEndpoint(BaseModel):
    """
    Pydantic model representing an API endpoint configuration.

    Attributes:
        path: REST endpoint path (e.g., "/bills")
        method: HTTP method to use
        requires_auth: Whether endpoint requires authentication
        rate_limit: Requests per second limit
        timeout: Request timeout in seconds
        description: Human-readable endpoint description
    """

    path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(default=HTTPMethod.GET, description="HTTP method")
    requires_auth: bool = Field(default=True, description="Requires authentication")
    rate_limit: int = Field(default=10, description="Requests per second")
    timeout: int = Field(default=30, description="Timeout in seconds")
    description: str = Field(default="", description="Endpoint description")

    @validator('path')
    def validate_path(cls, v):
        """Ensure path starts with forward slash."""
        if not v.startswith('/'):
            return f'/{v}'
        return v


class APIResponse(BaseModel):
    """
    Pydantic model representing an API response.

    Attributes:
        status_code: HTTP status code
        data: Response payload (JSON)
        headers: Response headers
        elapsed_ms: Request duration in milliseconds
        success: Whether request was successful
        error: Error message if failed
    """

    status_code: int = Field(..., description="HTTP status code")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")
    headers: Dict[str, str] = Field(default_factory=dict, description="Response headers")
    elapsed_ms: float = Field(..., description="Request duration (ms)")
    success: bool = Field(..., description="Request succeeded")
    error: Optional[str] = Field(default=None, description="Error message")

    class Config:
        # Allow arbitrary types for flexibility
        arbitrary_types_allowed = True


# ============================================================================
# Decorators
# ============================================================================

def log_api_call(func: Callable) -> Callable:
    """
    Decorator to log API calls with timing and error information.

    Args:
        func: Function to decorate (should be an API call method)

    Returns:
        Wrapped function with logging

    Usage:
        @log_api_call
        def get_bills(self, congress: int):
            ...
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Extract logger from self (API client instance)
        logger = getattr(self, 'logger', logging.getLogger(__name__))

        # Log function call with arguments
        func_name = func.__name__
        logger.debug(f"API call: {func_name}(args={args}, kwargs={kwargs})")

        # Track timing
        start_time = time.time()

        try:
            # Execute the actual API call
            result = func(self, *args, **kwargs)

            # Calculate elapsed time
            elapsed = (time.time() - start_time) * 1000  # Convert to ms

            # Log successful completion
            logger.info(f"API call completed: {func_name} ({elapsed:.2f}ms)")

            return result

        except Exception as e:
            # Calculate elapsed time for failed request
            elapsed = (time.time() - start_time) * 1000

            # Log error with context
            logger.error(
                f"API call failed: {func_name} ({elapsed:.2f}ms) - {type(e).__name__}: {str(e)}",
                exc_info=True
            )

            # Re-raise the exception
            raise

    return wrapper


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 2.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
    retry_on: tuple = (RequestException, Timeout)
):
    """
    Decorator to retry failed API calls with configurable strategy.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        strategy: Retry strategy (exponential, linear, fixed)
        retry_on: Exception types to retry on

    Returns:
        Decorator function

    Usage:
        @retry_on_failure(max_retries=3, strategy=RetryStrategy.EXPONENTIAL)
        def get_data(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get logger from instance
            logger = getattr(self, 'logger', logging.getLogger(__name__))

            # Iterate through retry attempts
            for attempt in range(max_retries + 1):
                try:
                    # Attempt the API call
                    return func(self, *args, **kwargs)

                except retry_on as e:
                    # Check if we have retries left
                    if attempt < max_retries:
                        # Calculate delay based on strategy
                        if strategy == RetryStrategy.EXPONENTIAL:
                            delay = base_delay * (2 ** attempt)
                        elif strategy == RetryStrategy.LINEAR:
                            delay = base_delay * (attempt + 1)
                        else:  # FIXED
                            delay = base_delay

                        # Log retry attempt
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {delay:.1f}s - Error: {type(e).__name__}"
                        )

                        # Sleep before retry
                        time.sleep(delay)
                    else:
                        # Max retries exceeded
                        logger.error(
                            f"Max retries ({max_retries}) exceeded for {func.__name__}"
                        )
                        raise

        return wrapper
    return decorator


def validate_response(schema: type[BaseModel]):
    """
    Decorator to validate API responses against a Pydantic schema.

    Args:
        schema: Pydantic model class to validate against

    Returns:
        Decorator function

    Usage:
        @validate_response(BillResponse)
        def get_bills(self):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Get the raw response
            response = func(self, *args, **kwargs)

            # Validate using Pydantic schema
            try:
                validated = schema(**response) if isinstance(response, dict) else schema(*response)
                return validated
            except Exception as e:
                logger = getattr(self, 'logger', logging.getLogger(__name__))
                logger.error(f"Response validation failed: {e}")
                raise ValueError(f"Invalid response format: {e}")

        return wrapper
    return decorator


# ============================================================================
# Abstract Base Class
# ============================================================================

class APIClientBase(ABC):
    """
    Abstract base class for all API clients.

    Provides comprehensive functionality for:
    - HTTP requests with retry logic
    - Rate limiting
    - Error handling and logging
    - Response validation
    - Session management

    Attributes:
        base_url: Base URL for the API
        api_key: API authentication key
        rate_limit: Requests per second
        session: Requests session object
        logger: Python logger instance

    Methods:
        request: Make HTTP request with full error handling
        get: Convenience method for GET requests
        post: Convenience method for POST requests
        _apply_rate_limit: Apply rate limiting before requests
        _build_headers: Build request headers

    Subclasses must implement:
        - Endpoint-specific methods using decorators
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        rate_limit: int = 10,
        timeout: int = 30,
        logger_name: Optional[str] = None
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL for API endpoints
            api_key: API authentication key (can be None for public APIs)
            rate_limit: Maximum requests per second
            timeout: Default request timeout in seconds
            logger_name: Custom logger name (defaults to class name)
        """
        # Store configuration
        self.base_url = base_url.rstrip('/')  # Remove trailing slash
        self.api_key = api_key
        self.rate_limit = rate_limit
        self.timeout = timeout

        # Initialize HTTP session
        self.session = requests.Session()

        # Set up logging
        self.logger = logging.getLogger(logger_name or self.__class__.__name__)

        # Track last request time for rate limiting
        self._last_request_time = 0.0

        # Build default headers
        self._setup_session()

        # Log initialization
        self.logger.info(f"{self.__class__.__name__} initialized: {base_url}")

    def _setup_session(self):
        """Configure the HTTP session with default headers and settings."""
        # Set default headers
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': f'OpenDiscourse/2.0.0 ({self.__class__.__name__})'
        })

        # Add API key to headers if provided
        if self.api_key:
            self.session.headers.update({
                'X-API-Key': self.api_key,
                'Authorization': f'Bearer {self.api_key}'
            })

    def _apply_rate_limit(self):
        """
        Apply rate limiting before making a request.

        Ensures we don't exceed the configured rate limit by sleeping
        if necessary between requests.
        """
        # Calculate minimum time between requests
        min_interval = 1.0 / self.rate_limit

        # Calculate time since last request
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        # Sleep if we need to throttle
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.3f}s")
            time.sleep(sleep_time)

        # Update last request time
        self._last_request_time = time.time()

    @log_api_call
    @retry_on_failure(max_retries=3, strategy=RetryStrategy.EXPONENTIAL)
    def request(
        self,
        endpoint: str,
        method: HTTPMethod = HTTPMethod.GET,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make an HTTP request to the API.

        Args:
            endpoint: API endpoint path
            method: HTTP method to use
            params: Query parameters
            data: Request body data
            timeout: Request timeout (uses default if not specified)

        Returns:
            APIResponse object with response data

        Raises:
            RequestException: On request failures
            HTTPError: On HTTP errors
            Timeout: On request timeout
        """
        # Apply rate limiting
        self._apply_rate_limit()

        # Build full URL
        url = f"{self.base_url}{endpoint}"

        # Use provided timeout or default
        timeout = timeout or self.timeout

        # Log request details
        self.logger.debug(f"{method.value} {url} (params={params})")

        # Track request start time
        start_time = time.time()

        try:
            # Make the HTTP request
            response = self.session.request(
                method=method.value,
                url=url,
                params=params,
                json=data,
                timeout=timeout
            )

            # Calculate elapsed time
            elapsed_ms = (time.time() - start_time) * 1000

            # Raise exception for HTTP errors
            response.raise_for_status()

            # Parse JSON response
            response_data = response.json() if response.content else None

            # Build successful APIResponse
            return APIResponse(
                status_code=response.status_code,
                data=response_data,
                headers=dict(response.headers),
                elapsed_ms=elapsed_ms,
                success=True
            )

        except HTTPError as e:
            # HTTP error (4xx, 5xx)
            elapsed_ms = (time.time() - start_time) * 1000

            self.logger.error(
                f"HTTP error {e.response.status_code}: {url} - {str(e)}"
            )

            return APIResponse(
                status_code=e.response.status_code,
                data=None,
                headers=dict(e.response.headers) if e.response else {},
                elapsed_ms=elapsed_ms,
                success=False,
                error=str(e)
            )

        except Timeout as e:
            # Request timeout
            elapsed_ms = (time.time() - start_time) * 1000

            self.logger.error(f"Request timeout: {url} ({timeout}s)")

            return APIResponse(
                status_code=408,  # Request Timeout
                data=None,
                headers={},
                elapsed_ms=elapsed_ms,
                success=False,
                error=f"Request timeout after {timeout}s"
            )

        except RequestException as e:
            # Other request errors (network, etc.)
            elapsed_ms = (time.time() - start_time) * 1000

            self.logger.error(f"Request failed: {url} - {str(e)}")

            return APIResponse(
                status_code=0,
                data=None,
                headers={},
                elapsed_ms=elapsed_ms,
                success=False,
                error=str(e)
            )

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            timeout: Request timeout

        Returns:
            APIResponse object
        """
        return self.request(endpoint, HTTPMethod.GET, params=params, timeout=timeout)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None
    ) -> APIResponse:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            timeout: Request timeout

        Returns:
            APIResponse object
        """
        return self.request(endpoint, HTTPMethod.POST, params=params, data=data, timeout=timeout)

    def close(self):
        """Close the HTTP session and clean up resources."""
        if self.session:
            self.session.close()
            self.logger.info(f"{self.__class__.__name__} session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures session is closed."""
        self.close()


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'HTTPMethod',
    'RetryStrategy',
    'APIEndpoint',
    'APIResponse',
    'APIClientBase',
    'log_api_call',
    'retry_on_failure',
    'validate_response',
]
