"""
Authentication middleware for OAuth 2.1 session validation.

Validates session tokens and attaches user_id to request state.
"""

from typing import Optional

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.services.session_service import get_session, validate_session


async def get_current_user_id(request: Request) -> Optional[str]:
    """
    Extract and validate session from request headers.

    Looks for Authorization: Bearer <session_id> header,
    validates session, and returns user_id if valid.

    Args:
        request: FastAPI request object

    Returns:
        user_id if authenticated, None otherwise

    Raises:
        HTTPException: If session is invalid or expired
    """
    # Get Authorization header
    authorization = request.headers.get("Authorization")

    if not authorization:
        return None

    # Parse Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format (expected 'Bearer <session_id>')",
        )

    session_id = authorization.replace("Bearer ", "").strip()

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing session ID in authorization header",
        )

    # Get database session
    db: AsyncSession
    async for db_session in get_db():
        db = db_session
        break

    # Validate session
    is_valid = await validate_session(db, session_id)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    # Get user_id from session
    session = await get_session(db, session_id)

    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found",
        )

    return session.user_id


async def require_authentication(request: Request) -> str:
    """
    Require valid authentication.

    This is a FastAPI dependency that can be used in route handlers
    to enforce authentication.

    Args:
        request: FastAPI request object

    Returns:
        user_id of authenticated user

    Raises:
        HTTPException: If not authenticated or session invalid

    Example:
        @router.get("/tasks")
        async def list_tasks(
            user_id: str = Depends(require_authentication)
        ):
            # user_id is guaranteed to be valid here
            ...
    """
    user_id = await get_current_user_id(request)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id
