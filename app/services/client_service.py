"""
Dynamic client service for RFC 7591 client registration.

Manages OAuth client registration for mobile and native applications
using dynamic client registration protocol.
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DynamicClient


def generate_client_id() -> str:
    """
    Generate unique client ID for registered client.

    Returns:
        32-character URL-safe client ID
    """
    return f"client_{secrets.token_urlsafe(24)}"


def generate_client_secret() -> str:
    """
    Generate client secret for confidential clients.

    Returns:
        43-character URL-safe client secret
    """
    return secrets.token_urlsafe(32)


async def register_client(
    db: AsyncSession,
    platform: str,
    redirect_uris: list[str],
    expires_in_days: int = 365,
) -> tuple[DynamicClient, str]:
    """
    Register new OAuth client (RFC 7591).

    Args:
        db: Database session
        platform: Client platform (ios, android, macos, windows, linux, cli)
        redirect_uris: List of allowed redirect URIs
        expires_in_days: Days until client registration expires (default: 365)

    Returns:
        tuple[DynamicClient, str]: Registered client and plain text client secret

    Example:
        client, secret = await register_client(
            db,
            platform="ios",
            redirect_uris=["myapp://oauth/callback"],
            expires_in_days=365
        )
    """
    # Generate credentials
    client_id = generate_client_id()
    client_secret = generate_client_secret()

    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

    # Create client record (encode secret to bytes for LargeBinary field)
    client = DynamicClient(
        client_id=client_id,
        client_secret=client_secret.encode('utf-8'),
        platform=platform,
        redirect_uris=redirect_uris,
        expires_at=expires_at,
    )

    db.add(client)
    await db.commit()
    await db.refresh(client)

    # Return both client and plain text secret (for API response and testing)
    return client, client_secret


async def get_client(db: AsyncSession, client_id: str) -> Optional[DynamicClient]:
    """
    Get client by ID.

    Args:
        db: Database session
        client_id: Client ID

    Returns:
        DynamicClient if found, None otherwise
    """
    stmt = select(DynamicClient).where(DynamicClient.client_id == client_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def validate_client(
    db: AsyncSession, client_id: str, client_secret: str
) -> bool:
    """
    Validate client credentials.

    Args:
        db: Database session
        client_id: Client ID
        client_secret: Client secret

    Returns:
        True if credentials valid and not expired, False otherwise
    """
    client = await get_client(db, client_id)

    if not client:
        return False

    # Check secret match (decode stored bytes secret for comparison)
    if client.client_secret.decode('utf-8') != client_secret:
        return False

    # Check expiration (handle both timezone-aware and naive datetimes)
    now = datetime.now(timezone.utc)
    expires_at = client.expires_at
    if expires_at.tzinfo is None:
        # Database stored naive datetime, assume UTC
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        return False

    # Update last used timestamp
    client.last_used = now
    await db.commit()

    return True


async def validate_redirect_uri(
    db: AsyncSession, client_id: str, redirect_uri: str
) -> bool:
    """
    Validate redirect URI for client.

    Args:
        db: Database session
        client_id: Client ID
        redirect_uri: Redirect URI to validate

    Returns:
        True if redirect URI is registered for client, False otherwise
    """
    client = await get_client(db, client_id)

    if not client:
        return False

    return redirect_uri in client.redirect_uris


async def revoke_client(db: AsyncSession, client_id: str) -> bool:
    """
    Revoke client registration.

    Args:
        db: Database session
        client_id: Client ID to revoke

    Returns:
        True if client was revoked, False if not found
    """
    stmt = delete(DynamicClient).where(DynamicClient.client_id == client_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def cleanup_expired_clients(db: AsyncSession) -> int:
    """
    Delete expired client registrations.

    Should be run periodically (e.g., daily cron job).

    Args:
        db: Database session

    Returns:
        Number of clients deleted
    """
    # SQLite stores naive datetimes, so we need to use naive datetime for comparison
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stmt = delete(DynamicClient).where(DynamicClient.expires_at <= now)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount


async def list_clients(
    db: AsyncSession, platform: Optional[str] = None
) -> list[DynamicClient]:
    """
    List registered clients.

    Args:
        db: Database session
        platform: Optional platform filter

    Returns:
        List of registered clients
    """
    stmt = select(DynamicClient)

    if platform:
        stmt = stmt.where(DynamicClient.platform == platform)

    stmt = stmt.order_by(DynamicClient.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())
