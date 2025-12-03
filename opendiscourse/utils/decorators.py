import functools
import logging
import time
from typing import Callable, ParamSpec, TypeVar

from integration_constants import BACKOFF_FACTOR, MAX_RETRIES, RETRY_DELAY_SECONDS

T = TypeVar("T")
P = ParamSpec("P")


def retry(
    max_retries: int = MAX_RETRIES,
    delay: int = RETRY_DELAY_SECONDS,
    backoff: float = BACKOFF_FACTOR,
    exceptions: tuple = (Exception,),
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries (in seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
                    logging.warning(
                        f"Attempt {attempt + 1} failed for {func.__name__}. Retrying in {current_delay} seconds..."
                    )
            return None

        return wrapper

    return decorator
