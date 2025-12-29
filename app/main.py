"""
Task Manager MCP Server - Main Application

This is the main FastAPI application that implements the MCP protocol
for conversational task management.

MCP Protocol Version: 2025-06-18
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.clients import router as clients_router
from app.api.error_handlers import (
    dynamic_client_exception_handler,
    generic_exception_handler,
    mcp_exception_handler,
    oauth_exception_handler,
    task_manager_exception_handler,
    validation_exception_handler,
)
from app.api.health import router as health_router
from app.api.logging_middleware import RequestLoggingMiddleware
from app.api.middleware import require_authentication
from app.api.oauth import router as oauth_router
from app.api.rate_limiting import configure_rate_limits
from app.config.logging_config import setup_logging
from app.config.settings import settings
from app.db.database import get_db, init_db
from app.exceptions import (
    DynamicClientException,
    MCPException,
    OAuthException,
    TaskManagerException,
)
from app.mcp.handlers import TOOL_HANDLERS
from app.mcp.tools import TOOLS

# Configure structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    - Startup: Initialize database tables, configure middleware
    - Shutdown: Cleanup resources
    """
    # Startup
    logger.info("Starting Task Manager MCP Server...")
    logger.info(
        f"MCP Protocol Version: {settings.MCP_PROTOCOL_VERSION}",
        extra={"version": settings.VERSION, "environment": settings.ENVIRONMENT},
    )

    # Initialize database
    await init_db()
    logger.info("Database initialized successfully")

    yield

    # Shutdown
    logger.info("Shutting down Task Manager MCP Server...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="MCP Server for conversational task management",
    lifespan=lifespan,
)

# Register exception handlers
# Order matters: most specific first, generic last
app.add_exception_handler(OAuthException, oauth_exception_handler)
app.add_exception_handler(DynamicClientException, dynamic_client_exception_handler)
app.add_exception_handler(MCPException, mcp_exception_handler)
app.add_exception_handler(TaskManagerException, task_manager_exception_handler)
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Add middleware
# Order matters: middleware is applied in reverse order (last added = first executed)
app.add_middleware(RequestLoggingMiddleware, exclude_paths=["/health", "/health/liveness", "/health/readiness"])
configure_rate_limits(app)

logger.info(
    "Middleware configured",
    extra={
        "request_logging": True,
        "rate_limiting": settings.ENVIRONMENT == "production",
        "environment": settings.ENVIRONMENT,
    },
)

# Register routers
app.include_router(oauth_router)
app.include_router(clients_router)
app.include_router(health_router)


# Root endpoint (MCP protocol discovery)
@app.head("/")
async def protocol_discovery() -> dict[str, str]:
    """
    MCP protocol discovery endpoint.

    Returns MCP protocol version in response header.

    Headers:
        MCP-Protocol-Version: 2025-06-18

    Per MCP spec, this allows clients to discover MCP support.
    """
    return {"MCP-Protocol-Version": settings.MCP_PROTOCOL_VERSION}


@app.get("/")
async def root() -> dict[str, Any]:
    """
    Root endpoint - Server information.

    Returns:
        Server name, version, and status
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "protocol": settings.MCP_PROTOCOL_VERSION,
        "status": "operational",
    }


# MCP Protocol Endpoints

@app.post("/mcp/initialize")
async def mcp_initialize() -> dict[str, Any]:
    """
    MCP initialize endpoint.

    Client calls this to initiate MCP protocol handshake.

    Returns:
        MCP initialization response with protocol version and capabilities

    Example Response:
        {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "Task Manager MCP Server",
                "version": "0.1.0"
            }
        }
    """
    return {
        "protocolVersion": settings.MCP_PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {"name": settings.APP_NAME, "version": settings.VERSION},
    }


@app.post("/mcp/tools/list")
async def mcp_tools_list() -> dict[str, Any]:
    """
    MCP tools/list endpoint.

    Returns list of all available MCP tools with their schemas.

    Returns:
        Dictionary with tools array

    Example Response:
        {
            "tools": [
                {
                    "name": "task_create",
                    "description": "Create a new task...",
                    "inputSchema": {...}
                },
                ...
            ]
        }
    """
    return {"tools": TOOLS}


@app.post("/mcp/tools/call")
async def mcp_tools_call(
    request_obj: Request,
    request: dict[str, Any],
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(require_authentication),
) -> dict[str, Any]:
    """
    MCP tools/call endpoint.

    Executes an MCP tool with provided parameters.

    Args:
        request_obj: FastAPI Request object (for accessing auth headers)
        request: Tool call request with name and params
        db: Database session (injected)
        user_id: Authenticated user ID (injected)

    Returns:
        MCP tool response with content blocks

    Request Format:
        {
            "name": "task_create",
            "params": {
                "title": "New task",
                "priority": 4
            }
        }

    Response Format:
        {
            "content": [
                {
                    "type": "text",
                    "text": "{...JSON response...}"
                }
            ]
        }

    Raises:
        HTTPException: If tool not found or execution fails
    """
    from app.services.session_service import (
        get_decrypted_access_token,
        get_decrypted_refresh_token,
    )

    tool_name = request.get("name")
    params = request.get("params", {})

    if not tool_name:
        raise HTTPException(status_code=400, detail="Tool name is required")

    # Get tool handler
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

    # Inject OAuth tokens for task_schedule tool
    if tool_name == "task_schedule":
        # Get session_id from Authorization header
        auth_header = request_obj.headers.get("Authorization", "")
        session_id = auth_header.replace("Bearer ", "").strip() if auth_header else None

        if session_id:
            # Get decrypted OAuth tokens from session
            access_token = await get_decrypted_access_token(db, session_id)
            refresh_token = await get_decrypted_refresh_token(db, session_id)

            # Inject tokens into params
            params["_access_token"] = access_token
            params["_refresh_token"] = refresh_token

    # Execute tool handler
    try:
        logger.info(f"Executing tool: {tool_name} with params: {params}")
        response = await handler(db, user_id, params)
        return response.model_dump()
    except Exception as e:
        logger.error(f"Tool execution failed: {tool_name} - {e!s}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e!s}")


# Debug endpoint (only in debug mode)
if settings.DEBUG:

    @app.get("/debug/settings")
    async def debug_settings() -> dict[str, Any]:
        """
        Debug endpoint to view current settings.

        Only available when DEBUG=true.

        Returns:
            Application settings (excluding secrets)
        """
        return {
            "APP_NAME": settings.APP_NAME,
            "VERSION": settings.VERSION,
            "DEBUG": settings.DEBUG,
            "HOST": settings.HOST,
            "PORT": settings.PORT,
            "DATABASE_URL": settings.DATABASE_URL.split("///")[-1],  # Hide full path
            "MCP_PROTOCOL_VERSION": settings.MCP_PROTOCOL_VERSION,
            "MOCK_USER_ID": settings.MOCK_USER_ID,
            "LOG_LEVEL": settings.LOG_LEVEL,
        }
