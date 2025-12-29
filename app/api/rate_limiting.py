"""
Rate limiting middleware for Task Manager MCP Server.

Provides per-user rate limiting to prevent abuse and ensure fair resource usage.
Uses sliding window algorithm with Redis-like in-memory storage.
"""

import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.settings import settings

logger = logging.getLogger(__name__)


def get_user_id_or_ip(request: Request) -> str:
    """
    Extract user ID or IP address for rate limiting.

    Prioritizes authenticated user ID for fair per-user limits.
    Falls back to IP address for unauthenticated requests.

    Args:
        request: FastAPI request object

    Returns:
        User ID or IP address string
    """
    # Try to get user_id from request state (set by auth middleware)
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"

    # Fall back to IP address for unauthenticated requests
    return f"ip:{get_remote_address(request)}"


# Configure rate limiter
limiter = Limiter(
    key_func=get_user_id_or_ip,
    default_limits=[],  # No default limits, set per-route
    storage_uri="memory://",  # In-memory storage (use Redis in production for multi-instance)
    enabled=settings.ENVIRONMENT == "production",  # Only enable in production
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting enforcement.

    Tracks request counts per user/IP and enforces limits.
    Returns 429 Too Many Requests when limits are exceeded.
    """

    def __init__(self, app):
        """
        Initialize rate limiting middleware.

        Args:
            app: FastAPI application instance
        """
        super().__init__(app)
        self.request_counts: dict[str, list[float]] = defaultdict(list)
        self.window_size = 60  # 60 second window
        self.max_requests = 100  # 100 requests per minute per user

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check rate limits before processing request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response or 429 if rate limited

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Get identifier (user_id or IP)
        identifier = get_user_id_or_ip(request)
        current_time = time.time()

        # Clean old entries (outside window)
        cutoff_time = current_time - self.window_size
        self.request_counts[identifier] = [
            ts for ts in self.request_counts[identifier] if ts > cutoff_time
        ]

        # Check rate limit
        request_count = len(self.request_counts[identifier])

        if request_count >= self.max_requests:
            # Calculate retry-after time
            oldest_request = min(self.request_counts[identifier])
            retry_after = int(self.window_size - (current_time - oldest_request)) + 1

            logger.warning(
                f"Rate limit exceeded for {identifier}",
                extra={
                    "identifier": identifier,
                    "request_count": request_count,
                    "limit": self.max_requests,
                    "window": self.window_size,
                    "path": request.url.path,
                },
            )

            return Response(
                content='{"error": "rate_limit_exceeded", "message": "Too many requests. Please slow down."}',
                status_code=429,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + retry_after)),
                },
                media_type="application/json",
            )

        # Add request timestamp
        self.request_counts[identifier].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        remaining = self.max_requests - len(self.request_counts[identifier])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_size))

        return response


def configure_rate_limits(app: Any) -> None:
    """
    Configure rate limits for specific routes.

    Args:
        app: FastAPI application instance

    Example:
        configure_rate_limits(app)
    """
    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)

    logger.info(
        "Rate limiting configured",
        extra={
            "max_requests": 100,
            "window_seconds": 60,
            "enabled": settings.ENVIRONMENT == "production",
        },
    )
