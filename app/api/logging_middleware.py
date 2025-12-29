"""
Request/Response logging middleware with correlation IDs.

Provides structured logging for all HTTP requests with unique correlation IDs
for distributed tracing and debugging.
"""

import logging
import time
import uuid
from contextvars import ContextVar
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message

# Context variable for correlation ID (thread-safe)
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

logger = logging.getLogger(__name__)


def get_correlation_id() -> str:
    """
    Get the current request's correlation ID.

    Returns:
        Correlation ID string, or empty string if not set
    """
    return correlation_id_var.get()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.

    Features:
    - Generates unique correlation ID for each request
    - Logs request details (method, path, headers)
    - Logs response details (status code, duration)
    - Includes correlation ID in all logs
    - Excludes health check endpoint from logging (configurable)
    """

    def __init__(self, app, exclude_paths: list[str] | None = None):
        """
        Initialize request logging middleware.

        Args:
            app: FastAPI application instance
            exclude_paths: List of paths to exclude from logging (e.g., ["/health"])
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # Generate correlation ID
        correlation_id = str(uuid.uuid4())
        correlation_id_var.set(correlation_id)

        # Add correlation ID to request state
        request.state.correlation_id = correlation_id

        # Start timing
        start_time = time.time()

        # Log incoming request
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
        )

        # Process request and capture response
        try:
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log response
            logger.info(
                f"Response: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
            )

            raise


class ResponseBodyLogger(BaseHTTPMiddleware):
    """
    Middleware for logging response bodies (for debugging).

    WARNING: Only enable this in development! Logging response bodies
    can expose sensitive data and significantly increase log volume.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Capture and log response body.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            HTTP response
        """
        response = await call_next(request)

        # Only log in debug mode
        from app.config.settings import settings

        if not settings.DEBUG:
            return response

        # Capture response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk

        # Log response body (truncated if too long)
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        body_preview = response_body[:500].decode("utf-8", errors="replace")

        logger.debug(
            "Response body",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "body_length": len(response_body),
                "body_preview": body_preview,
            },
        )

        # Reconstruct response with body
        async def response_body_iterator():
            yield response_body

        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
