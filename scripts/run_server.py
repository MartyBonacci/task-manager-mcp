#!/usr/bin/env python3
"""
Task Manager MCP Server - Development Server Runner

This script starts the MCP server using uvicorn with appropriate settings
for local development.

Usage:
    python scripts/run_server.py

Environment Variables:
    HOST: Server host (default: from settings)
    PORT: Server port (default: from settings)
    RELOAD: Enable auto-reload on code changes (default: True in DEBUG mode)
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uvicorn

from app.config.settings import settings


def main() -> None:
    """
    Start the uvicorn server with appropriate configuration.
    """
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,  # Auto-reload in debug mode
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.DEBUG,  # Access logging in debug mode
    )


if __name__ == "__main__":
    main()
