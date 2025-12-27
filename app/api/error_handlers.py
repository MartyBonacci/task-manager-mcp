"""
Error handling middleware for Task Manager MCP Server.

Catches custom exceptions and formats them into consistent HTTP responses.
"""

import logging
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.exceptions import (
    DynamicClientException,
    MCPException,
    OAuthException,
    TaskManagerException,
)

logger = logging.getLogger(__name__)


async def task_manager_exception_handler(
    request: Request, exc: TaskManagerException
) -> JSONResponse:
    """
    Handle TaskManagerException and all subclasses.

    Returns consistent error response format:
    {
        "error": "error_type",
        "message": "Human-readable error message",
        "detail": {...additional context...}
    }
    """
    logger.error(
        f"{exc.__class__.__name__}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
    )

    error_response: dict[str, Any] = {
        "error": exc.__class__.__name__,
        "message": exc.message,
    }

    # Add detail if present
    if exc.detail:
        error_response["detail"] = exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def oauth_exception_handler(
    request: Request, exc: OAuthException
) -> JSONResponse:
    """
    Handle OAuth-specific exceptions.

    Returns OAuth 2.1-compliant error response:
    {
        "error": "oauth_error_code",
        "error_description": "Human-readable error message",
        "detail": {...additional context...}
    }
    """
    logger.error(
        f"OAuth Error - {exc.error_code}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
        },
    )

    error_response: dict[str, Any] = {
        "error": exc.error_code or "server_error",
        "error_description": exc.message,
    }

    # Add detail if present
    if exc.detail:
        error_response["detail"] = exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def dynamic_client_exception_handler(
    request: Request, exc: DynamicClientException
) -> JSONResponse:
    """
    Handle Dynamic Client Registration (RFC 7591) exceptions.

    Returns RFC 7591-compliant error response:
    {
        "error": "client_error_code",
        "error_description": "Human-readable error message",
        "detail": {...additional context...}
    }
    """
    logger.error(
        f"Dynamic Client Error - {exc.error_code}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "error_code": exc.error_code,
        },
    )

    error_response: dict[str, Any] = {
        "error": exc.error_code or "server_error",
        "error_description": exc.message,
    }

    # Add detail if present
    if exc.detail:
        error_response["detail"] = exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def mcp_exception_handler(request: Request, exc: MCPException) -> JSONResponse:
    """
    Handle MCP protocol exceptions.

    Returns MCP-compliant error response:
    {
        "error": {
            "code": -32600,
            "message": "Human-readable error message",
            "data": {...additional context...}
        }
    }
    """
    logger.error(
        f"MCP Error - code {exc.mcp_error_code}: {exc.message}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
            "mcp_error_code": exc.mcp_error_code,
        },
    )

    error_response: dict[str, Any] = {
        "error": {
            "code": exc.mcp_error_code,
            "message": exc.message,
        }
    }

    # Add data if detail present
    if exc.detail:
        error_response["error"]["data"] = exc.detail

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
    )


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.

    Returns validation error details:
    {
        "error": "validation_error",
        "message": "Request validation failed",
        "detail": [
            {
                "loc": ["field", "name"],
                "msg": "field required",
                "type": "value_error.missing"
            }
        ]
    }
    """
    logger.warning(
        f"Validation Error: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": exc.errors(),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "detail": exc.errors(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions.

    Catches all unhandled exceptions and returns a generic error response
    without exposing internal details.
    """
    logger.exception(
        f"Unhandled exception: {exc}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": exc.__class__.__name__,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )
