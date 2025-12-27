"""
User service for managing OAuth 2.1 user operations.

This service handles user creation, retrieval, and updates during the OAuth flow.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Get user by Google user ID.

    Args:
        db: Database session
        user_id: Google user ID (sub claim)

    Returns:
        User if found, None otherwise
    """
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email address.

    Args:
        db: Database session
        email: User's email address

    Returns:
        User if found, None otherwise
    """
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession, user_id: str, email: str, name: Optional[str] = None
) -> User:
    """
    Create new user from OAuth callback data.

    Args:
        db: Database session
        user_id: Google user ID (sub claim)
        email: User's email address
        name: User's display name (optional)

    Returns:
        Created User instance
    """
    now = datetime.now(timezone.utc)
    user = User(
        user_id=user_id,
        email=email,
        name=name,
        last_login=now,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_last_login(db: AsyncSession, user_id: str) -> None:
    """
    Update user's last login timestamp.

    Args:
        db: Database session
        user_id: Google user ID (sub claim)
    """
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        user.last_login = datetime.now(timezone.utc)
        await db.commit()


async def upsert_user(
    db: AsyncSession, user_id: str, email: str, name: Optional[str] = None
) -> User:
    """
    Create or update user with last_login timestamp.

    This is the primary function used during OAuth callback to ensure
    the user exists and update their last login time.

    Args:
        db: Database session
        user_id: Google user ID (sub claim)
        email: User's email address
        name: User's display name (optional)

    Returns:
        User instance (created or updated)
    """
    # Check if user exists
    user = await get_user_by_id(db, user_id)

    if user:
        # Update existing user
        user.email = email
        if name:
            user.name = name
        user.last_login = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
        return user
    else:
        # Create new user
        return await create_user(db, user_id, email, name)
