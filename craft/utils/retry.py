"""Retry utility with exponential backoff."""

import asyncio
import random
import time
import functools
from typing import Type, Tuple, Union, Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


def retry_with_backoff(
    retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retry_on: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,),
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.

    Args:
        retries: Maximum number of retries.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay in seconds.
        backoff_factor: Multiplier for the delay.
        jitter: Whether to add random jitter to the delay.
        retry_on: Exception type(s) to retry on.

    Returns:
        Decorated function.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = base_delay

            while True:
                try:
                    return func(*args, **kwargs)
                except retry_on as e:
                    attempt += 1
                    if attempt > retries:
                        logger.warning(f"Max retries ({retries}) exceeded for {func.__name__}. Last error: {e}")
                        raise e

                    # Calculate delay
                    delay = current_delay
                    if jitter:
                        delay *= (0.5 + random.random())
                    
                    logger.info(
                        f"Retry {attempt}/{retries} for {func.__name__} after {delay:.2f}s due to: {e}"
                    )
                    
                    time.sleep(delay)
                    
                    # Update delay for next iteration
                    current_delay = min(current_delay * backoff_factor, max_delay)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            current_delay = base_delay

            while True:
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    attempt += 1
                    if attempt > retries:
                        logger.warning(f"Max retries ({retries}) exceeded for {func.__name__}. Last error: {e}")
                        raise e

                    # Calculate delay
                    delay = current_delay
                    if jitter:
                        delay *= (0.5 + random.random())
                    
                    logger.info(
                        f"Retry {attempt}/{retries} for {func.__name__} after {delay:.2f}s due to: {e}"
                    )
                    
                    await asyncio.sleep(delay)
                    
                    # Update delay for next iteration
                    current_delay = min(current_delay * backoff_factor, max_delay)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator
