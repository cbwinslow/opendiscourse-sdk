"""
Congress.gov API client with sophisticated error handling and retry logic.
"""

import time
import requests
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from datetime import datetime, timedelta
import logging

from ..models.api_models import (
    APIResponse,
    CongressMember,
    CongressBill,
    MemberResponse,
    BillResponse,
    APIConfig
)
from ..utils.logger import get_logger
from ..utils.config import get_config


class RateLimiter:
    """Sophisticated rate limiting with exponential backoff."""

    def __init__(self, requests_per_second: int):
        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = None
        self.request_times: List[datetime] = []
        self.logger = get_logger(__name__)

    def wait(self):
        """Wait if necessary to respect rate limit."""
        now = datetime.now()

        # Clean old request times (older than 1 second)
        cutoff = now - timedelta(seconds=1)
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check if we're at the limit
        if len(self.request_times) >= self.requests_per_second:
            sleep_time = (self.request_times[0] + timedelta(seconds=1) - now).total_seconds()
            if sleep_time > 0:
                self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f} seconds")
                time.sleep(sleep_time)

        # Record this request
        self.request_times.append(now)


class RetryStrategy:
    """Sophisticated retry strategy with delegate functions."""

    def __init__(self, max_retries: int = 3, backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retry_conditions: List[Callable[[Exception], bool]] = []
        self.retry_callbacks: List[Callable[[int, Exception, Dict], None]] = []
        self.logger = get_logger(__name__)

    def add_retry_condition(self, condition: Callable[[Exception], bool]):
        """Add a retry condition delegate function."""
        self.retry_conditions.append(condition)

    def add_retry_callback(self, callback: Callable[[int, Exception, Dict], None]):
        """Add a retry callback delegate function."""
        self.retry_callbacks.append(callback)

    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if we should retry based on exception and attempt."""
        if attempt >= self.max_retries:
            return False

        # Check custom retry conditions
        for condition in self.retry_conditions:
            try:
                if condition(exception):
                    return True
            except Exception as e:
                self.logger.warning(f"Retry condition failed: {e}")

        # Default retry conditions
        if isinstance(exception, requests.exceptions.Timeout):
            return True
        elif isinstance(exception, requests.exceptions.ConnectionError):
            return True
        elif isinstance(exception, requests.exceptions.HTTPError):
            if hasattr(exception, 'response') and exception.response is not None:
                status_code = exception.response.status_code
                # Retry on 5xx errors and 429 (rate limit)
                if 500 <= status_code < 600 or status_code == 429:
                    return True

        return False

    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return self.backoff_factor ** attempt

    def execute_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic."""
        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self.should_retry(e, attempt):
                    break

                # Calculate backoff
                backoff = self.calculate_backoff(attempt)
                self.logger.warning(f"Retry attempt {attempt + 1}/{self.max_retries + 1} after {backoff:.2f}s: {e}")

                # Call retry callbacks
                context = kwargs.get('context', {})
                for callback in self.retry_callbacks:
                    try:
                        callback(attempt + 1, e, context)
                    except Exception as cb_e:
                        self.logger.warning(f"Retry callback failed: {cb_e}")

                # Wait before retry
                time.sleep(backoff)

        # All retries exhausted
        raise last_exception


def api_error_handler(func):
    """Decorator for API error handling."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except requests.exceptions.RequestException as e:
            logger = get_logger(__name__)
            logger.error(f"API request failed: {e}")
            raise
        except Exception as e:
            logger = get_logger(__name__)
            logger.error(f"Unexpected error in API call: {e}")
            raise
    return wrapper


class CongressAPIClient:
    """Sophisticated Congress.gov API client with full abstraction."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[APIConfig] = None):
        """Initialize API client with configuration."""
        self.config = config or get_config().api
        if api_key:
            self.config.api_key = api_key

        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': self.config.api_key,
            'Accept': 'application/json',
            'User-Agent': f'congress-cli/1.0.0'
        })

        # Initialize components
        self.rate_limiter = RateLimiter(self.config.rate_limit_per_second)
        self.retry_strategy = RetryStrategy(
            max_retries=self.config.max_retries,
            backoff_factor=self.config.retry_backoff_factor
        )

        # Setup default retry conditions
        self._setup_default_retry_conditions()

        self.logger = get_logger(__name__)
        self.request_count = 0
        self.error_count = 0
        self.start_time = datetime.now()

    def _setup_default_retry_conditions(self):
        """Setup default retry conditions."""
        def rate_limit_error(e: Exception) -> bool:
            """Retry on rate limit errors."""
            if isinstance(e, requests.exceptions.HTTPError):
                if hasattr(e, 'response') and e.response is not None:
                    return e.response.status_code == 429
            return False

        def server_error(e: Exception) -> bool:
            """Retry on server errors."""
            if isinstance(e, requests.exceptions.HTTPError):
                if hasattr(e, 'response') and e.response is not None:
                    return 500 <= e.response.status_code < 600
            return False

        self.retry_strategy.add_retry_condition(rate_limit_error)
        self.retry_strategy.add_retry_condition(server_error)

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make API request with rate limiting and retry logic."""
        url = f"{self.config.base_url}/{endpoint}"

        def _request():
            # Rate limiting
            self.rate_limiter.wait()

            # Make request
            self.logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                params=params,
                timeout=self.config.timeout_seconds
            )

            # Check for errors
            response.raise_for_status()

            # Parse JSON
            data = response.json()

            # Update statistics
            self.request_count += 1

            return data

        # Execute with retry
        try:
            return self.retry_strategy.execute_with_retry(_request, context={'endpoint': endpoint})
        except Exception as e:
            self.error_count += 1
            raise

    @api_error_handler
    def get_members(self, congress: int, offset: int = 0, limit: int = 250) -> APIResponse:
        """Get Congress members with pagination."""
        params = {
            'limit': limit,
            'offset': offset
        }

        self.logger.info(f"Fetching members for Congress {congress}, offset {offset}")
        data = self._make_request(f"member/congress/{congress}", params)

        return APIResponse(**data)

    @api_error_handler
    def get_member(self, bioguide_id: str) -> MemberResponse:
        """Get detailed information for a specific member."""
        self.logger.info(f"Fetching member details for {bioguide_id}")
        data = self._make_request(f"member/{bioguide_id}")

        return MemberResponse(**data)

    @api_error_handler
    def get_bills(self, congress: int, offset: int = 0, limit: int = 250) -> APIResponse:
        """Get Congress bills with pagination."""
        params = {
            'limit': limit,
            'offset': offset
        }

        self.logger.info(f"Fetching bills for Congress {congress}, offset {offset}")
        data = self._make_request(f"bill/congress/{congress}", params)

        return APIResponse(**data)

    @api_error_handler
    def get_bill(self, bill_id: str) -> BillResponse:
        """Get detailed information for a specific bill."""
        self.logger.info(f"Fetching bill details for {bill_id}")
        data = self._make_request(f"bill/{bill_id}")

        return BillResponse(**data)

    @api_error_handler
    def get_bills_by_member(self, bioguide_id: str, congress: Optional[int] = None) -> APIResponse:
        """Get bills sponsored by a specific member."""
        params = {}
        if congress:
            params['congress'] = congress

        self.logger.info(f"Fetching bills for member {bioguide_id}")
        data = self._make_request(f"member/{bioguide_id}/bills", params)

        return APIResponse(**data)

    @api_error_handler
    def search_bills(self, query: str, congress: Optional[int] = None, limit: int = 250) -> APIResponse:
        """Search bills by query string."""
        params = {
            'query': query,
            'limit': limit
        }
        if congress:
            params['congress'] = congress

        self.logger.info(f"Searching bills with query: {query}")
        data = self._make_request("bill/search", params)

        return APIResponse(**data)

    def get_api_statistics(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        elapsed_time = (datetime.now() - self.start_time).total_seconds()

        return {
            'requests_made': self.request_count,
            'errors_encountered': self.error_count,
            'success_rate': ((self.request_count - self.error_count) / self.request_count * 100) if self.request_count > 0 else 0,
            'requests_per_second': self.request_count / elapsed_time if elapsed_time > 0 else 0,
            'elapsed_time_seconds': elapsed_time,
            'rate_limit': self.config.rate_limit_per_second,
            'max_retries': self.config.max_retries
        }

    def test_connection(self) -> bool:
        """Test API connection and authentication."""
        try:
            # Make a simple request to test connection
            self._make_request("bill?limit=1")
            self.logger.info("API connection test successful")
            return True
        except Exception as e:
            self.logger.error(f"API connection test failed: {e}")
            return False

    def close(self):
        """Close the session and cleanup resources."""
        if self.session:
            self.session.close()

        # Log final statistics
        stats = self.get_api_statistics()
        self.logger.info(f"API session closed. Statistics: {stats}")


class CongressAPIBatchProcessor:
    """Batch processor for efficient bulk operations."""

    def __init__(self, client: CongressAPClient, batch_size: int = 100):
        self.client = client
        self.batch_size = batch_size
        self.logger = get_logger(__name__)

        # Delegate functions for custom processing
        self.batch_processors: Dict[str, Callable[[List[Dict]], List[Dict]]] = {}
        self.error_handlers: Dict[str, Callable[[Exception, Dict], bool]] = {}

    def register_batch_processor(self, data_type: str, processor: Callable[[List[Dict]], List[Dict]]):
        """Register a batch processor delegate function."""
        self.batch_processors[data_type] = processor

    def register_error_handler(self, error_type: str, handler: Callable[[Exception, Dict], bool]):
        """Register an error handler delegate function."""
        self.error_handlers[error_type] = handler

    def process_members_batch(self, members_data: List[Dict]) -> List[CongressMember]:
        """Process a batch of member data."""
        processed_members = []

        # Apply custom processor if registered
        if 'members' in self.batch_processors:
            members_data = self.batch_processors['members'](members_data)

        for member_data in members_data:
            try:
                member = CongressMember(**member_data)
                processed_members.append(member)
            except Exception as e:
                # Handle error
                error_handled = False
                error_type = type(e).__name__

                if error_type in self.error_handlers:
                    error_handled = self.error_handlers[error_type](e, member_data)

                if not error_handled:
                    self.logger.error(f"Failed to process member data: {e}")
                    raise

        return processed_members

    def process_bills_batch(self, bills_data: List[Dict]) -> List[CongressBill]:
        """Process a batch of bill data."""
        processed_bills = []

        # Apply custom processor if registered
        if 'bills' in self.batch_processors:
            bills_data = self.batch_processors['bills'](bills_data)

        for bill_data in bills_data:
            try:
                bill = CongressBill(**bill_data)
                processed_bills.append(bill)
            except Exception as e:
                # Handle error
                error_handled = False
                error_type = type(e).__name__

                if error_type in self.error_handlers:
                    error_handled = self.error_handlers[error_type](e, bill_data)

                if not error_handled:
                    self.logger.error(f"Failed to process bill data: {e}")
                    raise

        return processed_bills

    def fetch_all_members(self, congress: int, progress_callback: Optional[Callable] = None) -> List[CongressMember]:
        """Fetch all members for a congress with automatic pagination."""
        all_members = []
        offset = 0

        while True:
            # Get batch
            response = self.client.get_members(congress, offset, self.batch_size)

            if not response.results:
                break

            # Process batch
            members = self.process_members_batch(response.results)
            all_members.extend(members)

            # Call progress callback
            if progress_callback:
                progress_callback(len(members), len(all_members), response.count)

            # Check if we're done
            if offset + len(response.results) >= response.count:
                break

            # Move to next batch
            offset += len(response.results)

        return all_members

    def fetch_all_bills(self, congress: int, progress_callback: Optional[Callable] = None) -> List[CongressBill]:
        """Fetch all bills for a congress with automatic pagination."""
        all_bills = []
        offset = 0

        while True:
            # Get batch
            response = self.client.get_bills(congress, offset, self.batch_size)

            if not response.results:
                break

            # Process batch
            bills = self.process_bills_batch(response.results)
            all_bills.extend(bills)

            # Call progress callback
            if progress_callback:
                progress_callback(len(bills), len(all_bills), response.count)

            # Check if we're done
            if offset + len(response.results) >= response.count:
                break

            # Move to next batch
            offset += len(response.results)

        return all_bills
