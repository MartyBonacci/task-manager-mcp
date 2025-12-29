"""
Retry utilities for transient failure handling.

Provides decorators and utilities for retrying operations with exponential backoff.
Useful for database operations, external API calls, and other network operations.
"""

import logging
from typing import Any, Callable, Type

from tenacity import (
    AsyncRetrying,
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


# Common retry configuration for database operations
DATABASE_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=1, max=10),
    "retry": retry_if_exception_type((ConnectionError, TimeoutError)),
    "reraise": True,
}


# Common retry configuration for external API calls
API_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=2, min=2, max=30),
    "retry": retry_if_exception_type((ConnectionError, TimeoutError)),
    "reraise": True,
}


def retry_on_db_error(
    func: Callable | None = None,
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
) -> Callable:
    """
    Decorator for retrying database operations.

    Retries on connection errors and timeouts with exponential backoff.

    Args:
        func: Function to decorate (provided automatically)
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_db_error
        async def get_user(db, user_id):
            return await db.query(User).filter_by(id=user_id).first()
    """

    def decorator(f: Callable) -> Callable:
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            reraise=True,
        )(f)

    if func is None:
        return decorator
    return decorator(func)


def retry_on_api_error(
    func: Callable | None = None,
    max_attempts: int = 3,
    min_wait: int = 2,
    max_wait: int = 30,
    exceptions: tuple[Type[Exception], ...] | None = None,
) -> Callable:
    """
    Decorator for retrying external API calls.

    Retries on connection errors, timeouts, and custom exceptions with exponential backoff.

    Args:
        func: Function to decorate (provided automatically)
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Additional exception types to retry on

    Returns:
        Decorated function with retry logic

    Example:
        @retry_on_api_error(max_attempts=5, exceptions=(HttpError,))
        async def fetch_calendar_events(access_token):
            return await calendar_api.get_events(access_token)
    """
    retry_exceptions = (ConnectionError, TimeoutError)
    if exceptions:
        retry_exceptions = retry_exceptions + exceptions

    def decorator(f: Callable) -> Callable:
        return retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=2, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True,
        )(f)

    if func is None:
        return decorator
    return decorator(func)


async def retry_async(
    func: Callable,
    *args: Any,
    max_attempts: int = 3,
    min_wait: int = 1,
    max_wait: int = 10,
    retry_exceptions: tuple[Type[Exception], ...] = (ConnectionError, TimeoutError),
    **kwargs: Any,
) -> Any:
    """
    Retry an async function with exponential backoff.

    Args:
        func: Async function to retry
        *args: Positional arguments for func
        max_attempts: Maximum retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        retry_exceptions: Exception types to retry on
        **kwargs: Keyword arguments for func

    Returns:
        Result from successful function call

    Raises:
        RetryError: If all retry attempts fail

    Example:
        result = await retry_async(
            fetch_user_data,
            user_id,
            max_attempts=5,
            retry_exceptions=(NetworkError, TimeoutError)
        )
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(retry_exceptions),
        reraise=True,
    ):
        with attempt:
            logger.debug(
                f"Executing {func.__name__} (attempt {attempt.retry_state.attempt_number}/{max_attempts})"
            )
            result = await func(*args, **kwargs)
            return result

    # This code is never reached due to reraise=True, but satisfies type checker
    raise RetryError("All retry attempts failed")
