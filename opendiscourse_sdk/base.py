"""
Base client class for all API clients in the OpenDiscourse SDK.

This module provides the BaseClient class which handles:
- HTTP request/response management
- Authentication
- Rate limiting
- Retry logic with exponential backoff
- Error handling and exception mapping
- Response validation

All API-specific clients (Congress, GovInfo, OpenStates) inherit from this base class.

Author: OpenDiscourse Team
License: MIT
"""

import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from pydantic import BaseModel
from pydantic import ValidationError as PydanticValidationError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from opendiscourse_sdk.exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)

# Configure logging
logger = logging.getLogger(__name__)


class BaseClient:
    """
    Base client for making HTTP requests to government APIs.
    
    This class provides common functionality for all API clients including:
    - Automatic retry with exponential backoff
    - Rate limiting
    - Error handling
    - Response validation
    - Session management
    
    Attributes:
        base_url: Base URL for the API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        session: Requests session with retry logic
        rate_limit_delay: Delay between requests to avoid rate limiting
    
    Example:
        This class is not meant to be used directly. Use specific clients:
        >>> from opendiscourse_sdk import CongressClient
        >>> client = CongressClient(api_key="your_key")
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        rate_limit_delay: float = 0.5,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
    ) -> None:
        """
        Initialize the base client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication (optional, can use env var)
            timeout: Request timeout in seconds (default: 30)
            rate_limit_delay: Delay between requests in seconds (default: 0.5)
            max_retries: Maximum number of retry attempts (default: 3)
            backoff_factor: Multiplier for exponential backoff (default: 1.0)
        
        Raises:
            AuthenticationError: If API key is required but not provided
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time = 0.0

        # Create session with retry logic
        self.session = self._create_session(
            max_retries=max_retries,
            backoff_factor=backoff_factor
        )

        logger.debug(f"Initialized {self.__class__.__name__} with base_url: {base_url}")

    def _create_session(self, max_retries: int, backoff_factor: float) -> requests.Session:
        """
        Create a requests session with automatic retry logic.
        
        The retry strategy will automatically retry on:
        - Connection errors
        - Timeout errors
        - HTTP 429 (rate limit)
        - HTTP 500, 502, 503, 504 (server errors)
        
        Args:
            max_retries: Maximum number of retry attempts
            backoff_factor: Multiplier for exponential backoff
        
        Returns:
            Configured requests.Session object
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
            raise_on_status=False,  # We'll handle status codes manually
        )

        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _enforce_rate_limit(self) -> None:
        """
        Enforce rate limiting by adding delay between requests.
        
        This method ensures that requests are not sent too quickly,
        respecting the API's rate limits.
        """
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from base URL and endpoint.
        
        Args:
            endpoint: API endpoint path (e.g., "/bills/118/hr/1")
        
        Returns:
            Complete URL
        """
        return urljoin(self.base_url + "/", endpoint.lstrip("/"))

    def _prepare_headers(self, headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Prepare request headers including authentication.
        
        Args:
            headers: Optional additional headers
        
        Returns:
            Dictionary of headers to include in request
        """
        default_headers = {
            "Accept": "application/json",
            "User-Agent": "OpenDiscourse-SDK/1.0.0",
        }

        if headers:
            default_headers.update(headers)

        return default_headers

    def _prepare_params(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare request parameters including API key.
        
        Args:
            params: Optional query parameters
        
        Returns:
            Dictionary of parameters to include in request
        """
        prepared_params = params.copy() if params else {}

        # Add API key if configured
        if self.api_key:
            prepared_params["api_key"] = self.api_key

        # Remove None values
        prepared_params = {k: v for k, v in prepared_params.items() if v is not None}

        return prepared_params

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions for errors.
        
        Args:
            response: Response object from requests
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            AuthenticationError: For 401/403 errors
            NotFoundError: For 404 errors
            RateLimitError: For 429 errors
            APIError: For other HTTP errors
            ValidationError: For invalid JSON response
        """
        # Log response details
        logger.debug(
            f"Response: {response.status_code} from {response.url} "
            f"(elapsed: {response.elapsed.total_seconds():.2f}s)"
        )

        # Handle successful responses
        if response.status_code in (200, 201):
            try:
                return response.json()
            except ValueError as e:
                raise ValidationError(
                    "Invalid JSON in response",
                    details={"error": str(e), "content": response.text[:200]}
                )

        # Handle error responses
        error_message = f"API request failed with status {response.status_code}"

        try:
            error_data = response.json()
            if "message" in error_data:
                error_message = error_data["message"]
            elif "error" in error_data:
                error_message = error_data["error"]
        except ValueError:
            error_data = {"content": response.text[:200]}

        # Map status codes to specific exceptions
        if response.status_code in (401, 403):
            raise AuthenticationError(
                error_message,
                status_code=response.status_code,
                response=response,
                details=error_data
            )
        elif response.status_code == 404:
            raise NotFoundError(
                error_message,
                response=response,
                details=error_data
            )
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise RateLimitError(
                error_message,
                retry_after=retry_after_int,
                response=response,
                details=error_data
            )
        else:
            raise APIError(
                error_message,
                status_code=response.status_code,
                response=response,
                details=error_data
            )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        This is the core method that handles all HTTP communication.
        It enforces rate limiting, adds authentication, and handles errors.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Optional query parameters
            data: Optional request body data
            headers: Optional request headers
        
        Returns:
            Parsed JSON response as dictionary
        
        Raises:
            Various exceptions based on response (see _handle_response)
        """
        # Enforce rate limiting
        self._enforce_rate_limit()

        # Build request
        url = self._build_url(endpoint)
        prepared_headers = self._prepare_headers(headers)
        prepared_params = self._prepare_params(params)

        logger.debug(f"Making {method} request to {url}")

        try:
            # Make request
            response = self.session.request(
                method=method,
                url=url,
                params=prepared_params,
                json=data,
                headers=prepared_headers,
                timeout=self.timeout,
            )

            # Handle response
            return self._handle_response(response)

        except requests.exceptions.Timeout as e:
            raise APIError(
                f"Request timed out after {self.timeout} seconds",
                status_code=0,
                details={"error": str(e)}
            )
        except requests.exceptions.ConnectionError as e:
            raise APIError(
                "Failed to connect to API",
                status_code=0,
                details={"error": str(e)}
            )
        except requests.exceptions.RequestException as e:
            raise APIError(
                f"Request failed: {str(e)}",
                status_code=0,
                details={"error": str(e)}
            )

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a GET request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            headers: Optional request headers
        
        Returns:
            Parsed JSON response as dictionary
        """
        return self._request("GET", endpoint, params=params, headers=headers)

    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a POST request to the API.
        
        Args:
            endpoint: API endpoint path
            data: Optional request body data
            params: Optional query parameters
            headers: Optional request headers
        
        Returns:
            Parsed JSON response as dictionary
        """
        return self._request("POST", endpoint, params=params, data=data, headers=headers)

    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a PUT request to the API.
        
        Args:
            endpoint: API endpoint path
            data: Optional request body data
            params: Optional query parameters
            headers: Optional request headers
        
        Returns:
            Parsed JSON response as dictionary
        """
        return self._request("PUT", endpoint, params=params, data=data, headers=headers)

    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Make a DELETE request to the API.
        
        Args:
            endpoint: API endpoint path
            params: Optional query parameters
            headers: Optional request headers
        
        Returns:
            Parsed JSON response as dictionary
        """
        return self._request("DELETE", endpoint, params=params, headers=headers)

    def validate_response(
        self,
        data: Dict[str, Any],
        model: type[BaseModel]
    ) -> BaseModel:
        """
        Validate API response against a Pydantic model.
        
        Args:
            data: Response data to validate
            model: Pydantic model class to validate against
        
        Returns:
            Validated model instance
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            return model(**data)
        except PydanticValidationError as e:
            raise ValidationError(
                f"Response validation failed for {model.__name__}",
                details={"errors": e.errors()}
            )

    def close(self) -> None:
        """
        Close the HTTP session and release resources.
        
        This should be called when the client is no longer needed,
        or use the client as a context manager.
        """
        if self.session:
            self.session.close()
            logger.debug(f"Closed session for {self.__class__.__name__}")

    def __enter__(self) -> "BaseClient":
        """Enter context manager."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and close session."""
        self.close()
