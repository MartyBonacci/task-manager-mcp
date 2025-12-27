"""
Session service for managing OAuth 2.1 session lifecycle.

This service handles session creation, validation, refresh, and cleanup
with encrypted token storage.
"""

import secrets
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.encryption import decrypt_token, encrypt_token
from app.db.models import Session


def generate_session_id() -> str:
    """
    Generate cryptographically secure session ID.

    Returns:
        43-character URL-safe session ID
    """
    return secrets.token_urlsafe(32)


async def create_session(
    db: AsyncSession,
    user_id: str,
    access_token: str,
    refresh_token: str,
    expires_at: datetime,
    user_agent: Optional[str] = None,
) -> Session:
    """
    Create new session with encrypted tokens.

    Args:
        db: Database session
        user_id: Google user ID (sub claim)
        access_token: OAuth access token (will be encrypted)
        refresh_token: OAuth refresh token (will be encrypted)
        expires_at: Access token expiration timestamp
        user_agent: User agent string from request (optional)

    Returns:
        Created Session instance
    """
    # Encrypt tokens before storage
    encrypted_access = encrypt_token(access_token)
    encrypted_refresh = encrypt_token(refresh_token)

    # Create session
    session = Session(
        session_id=generate_session_id(),
        user_id=user_id,
        access_token=encrypted_access,
        refresh_token=encrypted_refresh,
        expires_at=expires_at,
        user_agent=user_agent,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
    """
    Get session by ID.

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        Session if found, None otherwise
    """
    stmt = select(Session).where(Session.session_id == session_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_decrypted_access_token(
    db: AsyncSession, session_id: str
) -> Optional[str]:
    """
    Get decrypted access token for a session.

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        Decrypted access token if session exists, None otherwise
    """
    session = await get_session(db, session_id)
    if session:
        return decrypt_token(session.access_token)
    return None


async def get_decrypted_refresh_token(
    db: AsyncSession, session_id: str
) -> Optional[str]:
    """
    Get decrypted refresh token for a session.

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        Decrypted refresh token if session exists, None otherwise
    """
    session = await get_session(db, session_id)
    if session:
        return decrypt_token(session.refresh_token)
    return None


async def validate_session(db: AsyncSession, session_id: str) -> bool:
    """
    Check if session is valid (exists and not expired).

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        True if session is valid, False otherwise
    """
    session = await get_session(db, session_id)

    if not session:
        return False

    # Check if expired (handle both timezone-aware and naive datetimes)
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        # Database stored naive datetime, assume UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        return False

    # Update last activity
    session.last_activity = now
    await db.commit()

    return True


async def refresh_session(
    db: AsyncSession,
    session_id: str,
    new_access_token: str,
    new_expires_at: datetime,
) -> Optional[Session]:
    """
    Update session with new access token after refresh.

    Args:
        db: Database session
        session_id: Session ID
        new_access_token: New OAuth access token (will be encrypted)
        new_expires_at: New expiration timestamp

    Returns:
        Updated Session if found, None otherwise
    """
    session = await get_session(db, session_id)

    if not session:
        return None

    # Encrypt new access token
    encrypted_access = encrypt_token(new_access_token)

    # Update session
    session.access_token = encrypted_access
    session.expires_at = new_expires_at
    session.last_activity = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(session)
    return session


async def delete_session(db: AsyncSession, session_id: str) -> bool:
    """
    Delete session (logout).

    Args:
        db: Database session
        session_id: Session ID

    Returns:
        True if session was deleted, False if not found
    """
    stmt = delete(Session).where(Session.session_id == session_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def cleanup_expired_sessions(db: AsyncSession) -> int:
    """
    Delete all expired sessions.

    This should be run periodically (e.g., daily cron job) to clean up
    expired sessions and prevent database bloat.

    Args:
        db: Database session

    Returns:
        Number of sessions deleted
    """
    # SQLite stores naive datetimes, so we need to use naive datetime for comparison
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = delete(Session).where(Session.expires_at <= now)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount
