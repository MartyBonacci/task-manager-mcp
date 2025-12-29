"""
Comprehensive health check endpoints for Task Manager MCP Server.

Provides detailed health status including database connectivity,
external service availability, and system metrics.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.

    Returns minimal health status for load balancers and monitoring tools.
    Does not check dependencies for fast response time.

    Returns:
        Health status: {"status": "healthy"}
    """
    return {"status": "healthy"}


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """
    Detailed health check with dependency validation.

    Checks:
    - Application status
    - Database connectivity
    - Configuration validity
    - External service availability (optional)

    Returns:
        Detailed health status with component checks

    Example Response:
        {
            "status": "healthy",
            "timestamp": "2025-12-29T03:00:00Z",
            "version": "1.0.0",
            "environment": "production",
            "checks": {
                "database": {"status": "healthy", "latency_ms": 5.2},
                "configuration": {"status": "healthy"},
                "oauth": {"status": "healthy"}
            }
        }
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database connectivity
    db_status = await check_database(db)
    health_status["checks"]["database"] = db_status

    if db_status["status"] != "healthy":
        health_status["status"] = "degraded"

    # Check configuration
    config_status = check_configuration()
    health_status["checks"]["configuration"] = config_status

    if config_status["status"] != "healthy":
        health_status["status"] = "degraded"

    # Check OAuth configuration
    oauth_status = check_oauth_config()
    health_status["checks"]["oauth"] = oauth_status

    if oauth_status["status"] != "healthy":
        health_status["status"] = "degraded"

    return health_status


async def check_database(db: AsyncSession) -> dict[str, Any]:
    """
    Check database connectivity and response time.

    Args:
        db: Database session

    Returns:
        Database health status with latency
    """
    import time

    try:
        start_time = time.time()

        # Execute simple query
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        latency_ms = (time.time() - start_time) * 1000

        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "database_type": "postgresql" if "postgresql" in settings.DATABASE_URL else "sqlite",
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def check_configuration() -> dict[str, Any]:
    """
    Validate critical configuration settings.

    Returns:
        Configuration health status
    """
    try:
        # Check critical settings
        required_settings = [
            "DATABASE_URL",
            "SECRET_KEY",
            "ENCRYPTION_KEY",
        ]

        missing_settings = []
        for setting in required_settings:
            if not getattr(settings, setting, None):
                missing_settings.append(setting)

        if missing_settings:
            return {
                "status": "unhealthy",
                "error": f"Missing required settings: {', '.join(missing_settings)}",
            }

        return {"status": "healthy", "settings_validated": len(required_settings)}

    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def check_oauth_config() -> dict[str, Any]:
    """
    Validate OAuth configuration.

    Returns:
        OAuth configuration health status
    """
    try:
        from app.config.oauth import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

        if not GOOGLE_CLIENT_ID:
            return {"status": "unhealthy", "error": "Missing GOOGLE_CLIENT_ID"}

        if not GOOGLE_CLIENT_SECRET:
            return {"status": "unhealthy", "error": "Missing GOOGLE_CLIENT_SECRET"}

        return {
            "status": "healthy",
            "provider": "google",
            "client_id": GOOGLE_CLIENT_ID[:10] + "...",  # Partially masked
        }

    except Exception as e:
        logger.error(f"OAuth config health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@router.get("/health/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    """
    Kubernetes readiness probe endpoint.

    Checks if the application is ready to serve traffic.
    Returns 200 if ready, 503 if not ready.

    Returns:
        Readiness status
    """
    try:
        # Check database connection
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        from fastapi import HTTPException

        raise HTTPException(status_code=503, detail="Not ready")


@router.get("/health/liveness")
async def liveness_check() -> dict[str, str]:
    """
    Kubernetes liveness probe endpoint.

    Checks if the application is alive and not deadlocked.
    Returns 200 if alive, 503 if dead.

    Returns:
        Liveness status
    """
    # Simple liveness check - if we can respond, we're alive
    return {"status": "alive"}
