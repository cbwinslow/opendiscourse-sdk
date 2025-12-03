"""
Retry decorator for handling transient failures with exponential backoff and jitter.

This module provides a configurable retry decorator that can be used to automatically
retry failed function calls with exponential backoff and jitter to avoid thundering herd problems.

Example usage:
    ```python
    from opendiscourse.utils.retry_decorator import retry_with_backoff
    
    @retry_with_backoff(max_retries=3, backoff_factor=2)
    def api_call():
        # Some API call that might fail
        pass
    
    @retry_with_backoff(
        max_retries=5,
        backoff_factor=1.5,
        exceptions=(requests.ConnectionError, requests.Timeout),
        jitter=True,
        log_level='info'
    )
    def network_operation():
        # Network operation with custom retry configuration
        pass
    ```
"""

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

# Default logger for the retry decorator
logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    max_backoff: float = 60.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    jitter: bool = True,
    log_level: str = "warning",
) -> Callable[[Callable], Callable]:
    """
    Decorator that retries a function call with exponential backoff and optional jitter.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Factor by which delay increases after each retry (default: 1.0)
        max_backoff: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Exception types to catch and retry on (default: Exception)
        jitter: Whether to add random jitter to delay to avoid thundering herd (default: True)
        log_level: Logging level for retry messages ('debug', 'info', 'warning', 'error')
    
    Returns:
        Decorated function that will retry on specified exceptions
        
    Raises:
        The original exception if all retry attempts are exhausted
        
    Example:
        @retry_with_backoff(max_retries=3, backoff_factor=2, jitter=True)
        def unreliable_api_call():
            # Function that might fail temporarily
            response = requests.get("https://api.example.com/data")
            response.raise_for_status()
            return response.json()
    """
    # Validate parameters
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    if backoff_factor < 0:
        raise ValueError("backoff_factor must be non-negative")
    if max_backoff <= 0:
        raise ValueError("max_backoff must be positive")
    
    # Convert log level string to logging constant
    log_levels = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
    }
    
    if log_level.lower() not in log_levels:
        raise ValueError(f"Invalid log_level. Must be one of: {list(log_levels.keys())}")
    
    log_level_const = log_levels[log_level.lower()]
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    # Don't retry on the last attempt
                    if attempt == max_retries:
                        logger.log(
                            log_level_const,
                            "Function %s failed after %d attempts. Final exception: %s",
                            func.__name__,
                            max_retries + 1,
                            str(e)
                        )
                        raise e
                    
                    # Calculate delay with exponential backoff
                    delay = min(backoff_factor * (2 ** attempt), max_backoff)
                    
                    # Add jitter if enabled to avoid thundering herd
                    if jitter:
                        # Add random jitter of ±25% of the delay
                        jitter_range = delay * 0.25
                        delay += random.uniform(-jitter_range, jitter_range)
                        delay = max(0, delay)  # Ensure delay is not negative
                    
                    logger.log(
                        log_level_const,
                        "Function %s failed on attempt %d/%d with %s: %s. Retrying in %.2f seconds...",
                        func.__name__,
                        attempt + 1,
                        max_retries + 1,
                        type(e).__name__,
                        str(e),
                        delay
                    )
                    
                    time.sleep(delay)
            
            # This should never be reached due to the raise in the loop,
            # but included for completeness
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def retry_on_connection_error(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    jitter: bool = True
) -> Callable[[Callable], Callable]:
    """
    Convenience decorator for retrying on common connection errors.
    
    This is a specialized version of retry_with_backoff that targets common
    network and connection-related exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        backoff_factor: Factor by which delay increases after each retry (default: 2.0)
        jitter: Whether to add random jitter to delay (default: True)
    
    Returns:
        Decorated function that will retry on connection errors
    """
    try:
        import requests
        connection_exceptions = (
            ConnectionError,
            TimeoutError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException,
        )
    except ImportError:
        # If requests is not available, use built-in exceptions only
        connection_exceptions = (ConnectionError, TimeoutError)
    
    return retry_with_backoff(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        exceptions=connection_exceptions,
        jitter=jitter,
        log_level="warning"
    )


def retry_on_database_error(
    max_retries: int = 2,
    backoff_factor: float = 1.5,
    jitter: bool = True
) -> Callable[[Callable], Callable]:
    """
    Convenience decorator for retrying on database connection errors.
    
    This is a specialized version of retry_with_backoff that targets common
    database-related exceptions.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 2)
        backoff_factor: Factor by which delay increases after each retry (default: 1.5)
        jitter: Whether to add random jitter to delay (default: True)
    
    Returns:
        Decorated function that will retry on database errors
    """
    try:
        import psycopg2
        db_exceptions = (
            psycopg2.OperationalError,
            psycopg2.InterfaceError,
        )
    except ImportError:
        # If psycopg2 is not available, use generic exceptions
        db_exceptions = (ConnectionError,)
    
    return retry_with_backoff(
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        exceptions=db_exceptions,
        jitter=jitter,
        log_level="warning"
    )