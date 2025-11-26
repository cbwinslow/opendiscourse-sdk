#!/usr/bin/env python3
"""
Rate Limiting Utilities for API Ingestion
Implements token bucket algorithm for rate limiting across multiple APIs
"""

import time
import threading
from typing import Dict, Optional
from functools import wraps

class TokenBucket:
    """Token bucket implementation for rate limiting"""

    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket

        Args:
            rate: Tokens per second (rate limit)
            capacity: Maximum bucket capacity (burst capacity)
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False if insufficient tokens
        """
        with self.lock:
            now = time.time()
            # Add tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_token(self, tokens: int = 1) -> None:
        """Wait until sufficient tokens are available"""
        while not self.consume(tokens):
            # Calculate wait time needed
            with self.lock:
                needed = tokens - self.tokens
                wait_time = needed / self.rate
            time.sleep(wait_time)

class RateLimiter:
    """Multi-API rate limiter with token bucket algorithm"""

    def __init__(self):
        self.limiters: Dict[str, TokenBucket] = {}
        self._setup_default_limits()

    def _setup_default_limits(self):
        """Setup default rate limits for each API"""
        # Congress.gov: 120 requests per minute = 2 per second
        self.limiters['congress.gov'] = TokenBucket(rate=2.0, capacity=10)

        # OpenStates.org: 100 requests per minute = 1.67 per second
        self.limiters['openstates.org'] = TokenBucket(rate=1.67, capacity=8)

        # GovInfo.gov: 100 requests per minute = 1.67 per second
        self.limiters['govinfo.gov'] = TokenBucket(rate=1.67, capacity=8)

        # Generic limiter for unknown APIs
        self.limiters['default'] = TokenBucket(rate=1.0, capacity=5)

    def get_limiter(self, api_name: str) -> TokenBucket:
        """Get rate limiter for specific API"""
        return self.limiters.get(api_name, self.limiters['default'])

    def wait(self, api_name: str, tokens: int = 1) -> None:
        """Wait for rate limit clearance"""
        limiter = self.get_limiter(api_name)
        limiter.wait_for_token(tokens)

    def can_proceed(self, api_name: str, tokens: int = 1) -> bool:
        """Check if request can proceed without waiting"""
        limiter = self.get_limiter(api_name)
        return limiter.consume(tokens)

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(api_name: str, tokens: int = 1):
    """Decorator for rate limiting function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter.wait(api_name, tokens)
            return func(*args, **kwargs)
        return wrapper
    return decorator

class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts based on response headers"""

    def __init__(self, api_name: str, base_rate: float, capacity: int):
        self.api_name = api_name
        self.base_rate = base_rate
        self.current_rate = base_rate
        self.capacity = capacity
        self.bucket = TokenBucket(base_rate, capacity)
        self.consecutive_errors = 0
        self.max_errors = 3

    def update_from_response(self, response_headers: Dict[str, str]):
        """Update rate limit based on response headers"""
        # Check for rate limit headers
        remaining = response_headers.get('X-RateLimit-Remaining')
        reset = response_headers.get('X-RateLimit-Reset')

        if remaining and reset:
            try:
                remaining_int = int(remaining)
                reset_time = int(reset)
                current_time = int(time.time())

                if reset_time > current_time:
                    time_window = reset_time - current_time
                    if time_window > 0:
                        # Adjust rate based on remaining quota
                        new_rate = max(0.1, remaining_int / time_window)
                        self.current_rate = min(self.base_rate, new_rate)
                        self.bucket.rate = self.current_rate
            except (ValueError, TypeError):
                pass

    def handle_error(self, status_code: int):
        """Handle rate limit errors"""
        if status_code == 429:  # Too Many Requests
            self.consecutive_errors += 1
            if self.consecutive_errors >= self.max_errors:
                # Reduce rate significantly
                self.current_rate = max(0.1, self.current_rate * 0.5)
                self.bucket.rate = self.current_rate
                self.consecutive_errors = 0
        elif 200 <= status_code < 300:
            # Success, reset error counter
            self.consecutive_errors = 0

    def wait_for_token(self, tokens: int = 1) -> None:
        """Wait with adaptive rate limiting"""
        self.bucket.wait_for_token(tokens)

# Adaptive rate limiters for each API
adaptive_limiters = {
    'congress.gov': AdaptiveRateLimiter('congress.gov', 2.0, 10),
    'openstates.org': AdaptiveRateLimiter('openstates.org', 1.67, 8),
    'govinfo.gov': AdaptiveRateLimiter('govinfo.gov', 1.67, 8),
}
