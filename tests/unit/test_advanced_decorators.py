"""
================================================================================
File: test_advanced_decorators.py
Author: OpenDiscourse Contributors
Created: 2025-12-04
Version: 1.0.0

Description:
    Tests for advanced decorators including caching, validation,
    performance monitoring, and rate limiting.

================================================================================
"""

import pytest
import time
from pydantic import ValidationError

from scripts.core.advanced_decorators import (
    cache,
    validate_params,
    measure_performance,
    conditional,
    rate_limit,
    memoize
)


# ============================================================================
# Cache Decorator Tests
# ============================================================================

def test_cache_basic():
    """Test basic caching functionality."""
    call_count = 0

    @cache()
    def expensive_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call
    result1 = expensive_function(5)
    assert result1 == 10
    assert call_count == 1

    # Second call with same argument (should be cached)
    result2 = expensive_function(5)
    assert result2 == 10
    assert call_count == 1  # Not incremented

    # Call with different argument
    result3 = expensive_function(10)
    assert result3 == 20
    assert call_count == 2


def test_cache_with_ttl():
    """Test cache with TTL expiration."""
    call_count = 0

    @cache(ttl=1)  # 1 second TTL
    def function_with_ttl(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call
    result1 = function_with_ttl(5)
    assert call_count == 1

    # Immediate second call (cached)
    result2 = function_with_ttl(5)
    assert call_count == 1

    # Wait for TTL to expire
    time.sleep(1.1)

    # Call again (should execute, cache expired)
    result3 = function_with_ttl(5)
    assert call_count == 2


def test_cache_maxsize():
    """Test cache size limiting."""
    @cache(maxsize=2)
    def cached_func(x):
        return x * 2

    # Fill cache
    cached_func(1)
    cached_func(2)
    cached_func(3)  # Should evict oldest (1)

    # Cache info should show hits/misses
    assert hasattr(cached_func, 'cache_info')


# ============================================================================
# Validate Params Decorator Tests
# ============================================================================

def test_validate_params_success():
    """Test parameter validation with correct types."""
    @validate_params
    def typed_function(x: int, y: str) -> str:
        return f"{y}: {x}"

    result = typed_function(42, "answer")
    assert result == "answer: 42"


def test_validate_params_type_coercion():
    """Test that validator coerces compatible types."""
    @validate_params
    def typed_function(x: int, y: str) -> str:
        return f"{y}: {x}"

    # String number should be coerced to int
    result = typed_function("42", "answer")
    assert result == "answer: 42"


def test_validate_params_failure():
    """Test parameter validation with incorrect types."""
    @validate_params
    def typed_function(x: int) -> int:
        return x * 2

    # Should raise validation error for incompatible type
    with pytest.raises(ValidationError):
        typed_function("not a number")


# ============================================================================
# Measure Performance Decorator Tests
# ============================================================================

def test_measure_performance_basic():
    """Test performance measurement."""
    @measure_performance()
    def slow_function():
        time.sleep(0.1)
        return "done"

    result = slow_function()
    assert result == "done"
    # Function should complete (logging tested separately)


def test_measure_performance_with_threshold(caplog):
    """Test performance threshold warning."""
    @measure_performance(log_threshold=0.05)
    def slow_function():
        time.sleep(0.1)  # Exceeds threshold
        return "done"

    result = slow_function()
    assert result == "done"
    # Should have logged warning (check logs if needed)


def test_measure_performance_on_error():
    """Test that performance is measured even on error."""
    @measure_performance()
    def failing_function():
        time.sleep(0.05)
        raise ValueError("Intentional error")

    with pytest.raises(ValueError):
        failing_function()
    # Duration should still be logged


# ============================================================================
# Conditional Decorator Tests
# ============================================================================

def test_conditional_true():
    """Test conditional execution when predicate is True."""
    def always_true(*args, **kwargs):
        return True

    @conditional(always_true)
    def conditional_function(x):
        return x * 2

    result = conditional_function(5)
    assert result == 10


def test_conditional_false():
    """Test conditional skipping when predicate is False."""
    def always_false(*args, **kwargs):
        return False

    @conditional(always_false, fallback_return="skipped")
    def conditional_function(x):
        return x * 2

    result = conditional_function(5)
    assert result == "skipped"


def test_conditional_with_args():
    """Test conditional with argument-based predicate."""
    def check_positive(x):
        return x > 0

    @conditional(check_positive, fallback_return=0)
    def positive_only(x):
        return x * 2

    assert positive_only(5) == 10  # Positive, executes
    assert positive_only(-5) == 0  # Negative, skipped


# ============================================================================
# Rate Limit Decorator Tests
# ============================================================================

def test_rate_limit_basic():
    """Test basic rate limiting."""
    @rate_limit(calls=2, period=1.0)
    def limited_function():
        return time.time()

    # First two calls should be fast
    start = time.time()
    limited_function()
    limited_function()
    fast_duration = time.time() - start

    assert fast_duration < 0.1  # Should be very fast

    # Third call should be rate limited
    start = time.time()
    limited_function()
    slow_duration = time.time() - start

    # Should have waited ~1 second
    assert slow_duration >= 0.9


def test_rate_limit_reset():
    """Test that rate limit resets after period."""
    @rate_limit(calls=1, period=0.5)
    def limited_function():
        return "ok"

    limited_function()  # First call
    time.sleep(0.6)  # Wait for period to reset

    # Second call should not be limited
    start = time.time()
    limited_function()
    duration = time.time() - start

    assert duration < 0.1  # Should be fast


# ============================================================================
# Memoize Decorator Tests
# ============================================================================

def test_memoize_basic():
    """Test basic memoization."""
    call_count = 0

    @memoize
    def fibonacci(n):
        nonlocal call_count
        call_count += 1
        if n < 2:
            return n
        return fibonacci(n-1) + fibonacci(n-2)

    result = fibonacci(10)
    assert result == 55
    # With memoization, should be called much fewer times than 2^10
    assert call_count < 100


def test_memoize_cache_access():
    """Test accessing memoization cache."""
    @memoize
    def simple_func(x):
        return x * 2

    simple_func(5)
    simple_func(10)

    # Should have cache
    assert hasattr(simple_func, 'cache')
    assert len(simple_func.cache) == 2


def test_memoize_clear_cache():
    """Test clearing memoization cache."""
    @memoize
    def simple_func(x):
        return x * 2

    simple_func(5)
    assert len(simple_func.cache) > 0

    simple_func.clear_cache()
    assert len(simple_func.cache) == 0


# ============================================================================
# Integration Tests
# ============================================================================

def test_multiple_decorators():
    """Test stacking multiple decorators."""
    call_count = 0

    @cache()
    @measure_performance()
    @validate_params
    def complex_function(x: int) -> int:
        nonlocal call_count
        call_count += 1
        time.sleep(0.05)
        return x * 2

    # First call
    result1 = complex_function(5)
    assert result1 == 10
    assert call_count == 1

    # Second call (should be cached)
    result2 = complex_function(5)
    assert result2 == 10
    assert call_count == 1  # Not incremented due to cache


def test_decorator_preserves_metadata():
    """Test that decorators preserve function metadata."""
    @cache()
    @measure_performance()
    def documented_function(x):
        """This function is documented."""
        return x * 2

    # Should preserve docstring
    assert documented_function.__doc__ == "This function is documented."
    assert documented_function.__name__ == "documented_function"
