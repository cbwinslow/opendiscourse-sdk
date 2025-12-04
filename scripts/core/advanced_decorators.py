"""
================================================================================
File: advanced_decorators.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Last Modified: 2025-12-04
Version: 2.0.0

Description:
    Advanced decorators for caching, parameter validation, and performance
    monitoring. Extends the base decorator set with production-ready utilities.

Dependencies:
    - functools: Decorator utilities and caching
    - typing: Type hints
    - time: Performance measurement
    - logging: Debug logging
    - pydantic: Parameter validation

Decorators:
    - @cache: Response caching with TTL
    - @validate_params: Parameter validation using Pydantic
    - @measure_performance: Performance profiling
    - @conditional: Conditional execution based on predicate

Usage:
    from scripts.core.advanced_decorators import cache, validate_params

    # Cache API responses
    @cache(ttl=3600)  # 1 hour
    def get_bills(congress):
        # Expensive API call
        return api_client.get_bills(congress)

    # Validate parameters
    @validate_params
    def process_bill(bill_id: str, congress: int):
        # Parameters validated automatically
        ...

Changelog:
    2025-12-04: Initial creation

================================================================================
"""

import logging
import time
from functools import wraps, lru_cache
from typing import Callable, Any, Optional, Dict, Type
from datetime import datetime, timedelta

from pydantic import BaseModel, ValidationError, validate_arguments


# ============================================================================
# Caching Decorator
# ============================================================================

def cache(ttl: Optional[int] = None, maxsize: int = 128):
    """
    Cache function results with optional TTL (time-to-live).

    Combines functools.lru_cache with TTL support for expiring
    cached entries after a specified time.

    Args:
        ttl: Time-to-live in seconds (None = never expire)
        maxsize: Maximum cache entries (LRU eviction)

    Returns:
        Decorator function

    Usage:
        @cache(ttl=3600, maxsize=256)  # Cache for 1 hour
        def expensive_operation(param):
            # Cached result
            return result
    """
    def decorator(func: Callable) -> Callable:
        # Use lru_cache for efficient caching
        cached_func = lru_cache(maxsize=maxsize)(func)

        # Store cache timestamps if TTL enabled
        if ttl is not None:
            cache_times: Dict[tuple, datetime] = {}

            @wraps(func)
            def wrapper(*args, **kwargs):
                # Create cache key
                cache_key = (args, tuple(sorted(kwargs.items())))

                # Check if cached and not expired
                if cache_key in cache_times:
                    cached_time = cache_times[cache_key]
                    age = (datetime.now() - cached_time).total_seconds()

                    if age > ttl:
                        # Expired, remove from cache
                        cached_func.cache_clear()
                        del cache_times[cache_key]
                        logger = logging.getLogger(func.__module__)
                        logger.debug(f"Cache expired for {func.__name__}")

                # Store cache time for new entries
                result = cached_func(*args, **kwargs)
                cache_times[cache_key] = datetime.now()

                return result

            # Expose cache info
            wrapper.cache_info = cached_func.cache_info
            wrapper.cache_clear = cached_func.cache_clear

            return wrapper
        else:
            # No TTL, just use lru_cache
            return cached_func

    return decorator


# ============================================================================
# Parameter Validation Decorator
# ============================================================================

def validate_params(func: Callable) -> Callable:
    """
    Validate function parameters using type hints and Pydantic.

    Automatically validates parameters based on type annotations.
    Raises ValidationError if validation fails.

    Args:
        func: Function to validate

    Returns:
        Wrapped function with validation

    Usage:
        @validate_params
        def process_data(user_id: int, name: str, active: bool = True):
            # Parameters validated automatically
            ...
    """
    # Use Pydantic's validate_arguments decorator
    return validate_arguments(func)


# ============================================================================
# Performance Monitoring Decorator
# ============================================================================

def measure_performance(log_threshold: Optional[float] = None):
    """
    Measure and log function execution time.

    Logs execution time for profiling and performance monitoring.
    Optionally warns if execution exceeds threshold.

    Args:
        log_threshold: Warn if execution exceeds this many seconds

    Returns:
        Decorator function

    Usage:
        @measure_performance(log_threshold=1.0)  # Warn if >1s
        def slow_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)

            # Start timing
            start_time = time.time()

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Calculate duration
                duration = time.time() - start_time

                # Log performance
                if log_threshold and duration > log_threshold:
                    logger.warning(
                        f"{func.__name__} took {duration:.2f}s (threshold: {log_threshold}s)"
                    )
                else:
                    logger.debug(f"{func.__name__} completed in {duration:.2f}s")

                return result

            except Exception as e:
                # Log duration even on failure
                duration = time.time() - start_time
                logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
                raise

        return wrapper
    return decorator


# ============================================================================
# Conditional Execution Decorator
# ============================================================================

def conditional(predicate: Callable[..., bool], fallback_return: Any = None):
    """
    Execute function only if predicate returns True.

    Useful for conditional feature execution, environment checks, etc.

    Args:
        predicate: Function that returns bool (receives same args as wrapped func)
        fallback_return: Value to return if predicate is False

    Returns:
        Decorator function

    Usage:
        def is_production():
            return os.getenv('ENV') == 'production'

        @conditional(is_production, fallback_return={'status': 'disabled'})
        def production_only_feature():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check predicate
            if predicate(*args, **kwargs):
                return func(*args, **kwargs)
            else:
                logger = logging.getLogger(func.__module__)
                logger.debug(f"Skipping {func.__name__} (predicate failed)")
                return fallback_return

        return wrapper
    return decorator


# ============================================================================
# Rate Limiting Decorator
# ============================================================================

def rate_limit(calls: int, period: float):
    """
    Rate limit function calls.

    Limits function to 'calls' invocations per 'period' seconds.
    Blocks if rate limit would be exceeded.

    Args:
        calls: Maximum calls allowed
        period: Time period in seconds

    Returns:
        Decorator function

    Usage:
        @rate_limit(calls=10, period=1.0)  # 10 calls per second
        def api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        call_times: list[float] = []

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal call_times

            # Current time
            now = time.time()

            # Remove old calls outside the period
            call_times = [t for t in call_times if now - t < period]

            # Check if we can make another call
            if len(call_times) >= calls:
                # Calculate wait time
                oldest_call = call_times[0]
                wait_time = period - (now - oldest_call)

                if wait_time > 0:
                    logger = logging.getLogger(func.__module__)
                    logger.debug(f"Rate limit: sleeping {wait_time:.2f}s")
                    time.sleep(wait_time)

                # Remove the oldest call
                call_times.pop(0)

            # Record this call
            call_times.append(time.time())

            # Execute function
            return func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Memoization Decorator (Simple)
# ============================================================================

def memoize(func: Callable) -> Callable:
    """
    Simple memoization decorator (infinite cache).

    Caches all function results permanently. Use with caution
    on functions with many unique inputs.

    Args:
        func: Function to memoize

    Returns:
        Memoized function

    Usage:
        @memoize
        def fibonacci(n):
            if n < 2:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
    """
    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create cache key
        key = (args, tuple(sorted(kwargs.items())))

        if key not in cache:
            cache[key] = func(*args, **kwargs)

        return cache[key]

    # Expose cache clearing
    wrapper.cache = cache
    wrapper.clear_cache = lambda: cache.clear()

    return wrapper


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    'cache',
    'validate_params',
    'measure_performance',
    'conditional',
    'rate_limit',
    'memoize',
]
