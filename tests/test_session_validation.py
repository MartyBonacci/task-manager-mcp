"""
Integration tests for session validation.

Tests session lifecycle including creation, validation, expiration,
and cleanup.
"""

import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.session_service import (
    cleanup_expired_sessions,
    create_session,
    delete_session,
    get_decrypted_access_token,
    get_decrypted_refresh_token,
    get_session,
    refresh_session,
    validate_session,
)
from app.services.user_service import create_user


class TestSessionCreation:
    """Test session creation and token encryption."""

    @pytest.mark.asyncio
    async def test_create_session_encrypts_tokens(self, db_session: AsyncSession):
        """Test that tokens are encrypted when stored."""
        # Create test user
        user = await create_user(
            db_session,
            user_id="encrypt_test_user",
            email="encrypt@example.com",
        )

        # Create session with plaintext tokens
        plaintext_access = "plaintext_access_token_12345"
        plaintext_refresh = "plaintext_refresh_token_67890"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token=plaintext_access,
            refresh_token=plaintext_refresh,
            expires_at=expires_at,
        )

        # Verify tokens are encrypted in database (not plaintext)
        assert session.access_token != plaintext_access.encode()
        assert session.refresh_token != plaintext_refresh.encode()
        assert isinstance(session.access_token, bytes)
        assert isinstance(session.refresh_token, bytes)

        # Verify decryption works
        decrypted_access = await get_decrypted_access_token(
            db_session, session.session_id
        )
        decrypted_refresh = await get_decrypted_refresh_token(
            db_session, session.session_id
        )

        assert decrypted_access == plaintext_access
        assert decrypted_refresh == plaintext_refresh

    @pytest.mark.asyncio
    async def test_session_id_unique(self, db_session: AsyncSession):
        """Test that session IDs are unique."""
        user = await create_user(
            db_session,
            user_id="unique_test_user",
            email="unique@example.com",
        )

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        # Create multiple sessions
        session1 = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="token1",
            refresh_token="refresh1",
            expires_at=expires_at,
        )

        session2 = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="token2",
            refresh_token="refresh2",
            expires_at=expires_at,
        )

        # Session IDs should be different
        assert session1.session_id != session2.session_id


class TestSessionValidation:
    """Test session validation logic."""

    @pytest.mark.asyncio
    async def test_valid_session_updates_last_activity(self, db_session: AsyncSession):
        """Test that validation updates last_activity timestamp."""
        user = await create_user(
            db_session,
            user_id="activity_test_user",
            email="activity@example.com",
        )

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        original_activity = session.last_activity

        # Wait a moment and validate
        import asyncio
        await asyncio.sleep(0.1)

        is_valid = await validate_session(db_session, session.session_id)
        assert is_valid is True

        # Check that last_activity was updated
        updated_session = await get_session(db_session, session.session_id)
        assert updated_session.last_activity > original_activity

    @pytest.mark.asyncio
    async def test_expired_session_invalid(self, db_session: AsyncSession):
        """Test that expired sessions fail validation."""
        user = await create_user(
            db_session,
            user_id="expired_test_user",
            email="expired@example.com",
        )

        # Create session that expired 1 hour ago
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="expired_token",
            refresh_token="expired_refresh",
            expires_at=expires_at,
        )

        # Should be invalid
        is_valid = await validate_session(db_session, session.session_id)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_nonexistent_session_invalid(self, db_session: AsyncSession):
        """Test that nonexistent sessions fail validation."""
        is_valid = await validate_session(db_session, "fake_session_id_xyz")
        assert is_valid is False


class TestSessionRefresh:
    """Test session token refresh."""

    @pytest.mark.asyncio
    async def test_refresh_updates_access_token(self, db_session: AsyncSession):
        """Test that refresh updates access token and expiry."""
        user = await create_user(
            db_session,
            user_id="refresh_test_user",
            email="refresh@example.com",
        )

        # Create session
        original_access = "original_access_token"
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token=original_access,
            refresh_token="refresh_token",
            expires_at=expires_at,
        )

        # Refresh with new token
        new_access = "new_access_token"
        new_expires = datetime.now(timezone.utc) + timedelta(hours=2)

        updated = await refresh_session(
            db_session,
            session_id=session.session_id,
            new_access_token=new_access,
            new_expires_at=new_expires,
        )

        # Verify update
        assert updated is not None
        decrypted = await get_decrypted_access_token(db_session, session.session_id)
        assert decrypted == new_access
        assert updated.expires_at == new_expires

    @pytest.mark.asyncio
    async def test_refresh_nonexistent_session(self, db_session: AsyncSession):
        """Test refresh fails for nonexistent session."""
        new_expires = datetime.now(timezone.utc) + timedelta(hours=1)

        result = await refresh_session(
            db_session,
            session_id="nonexistent",
            new_access_token="new_token",
            new_expires_at=new_expires,
        )

        assert result is None


class TestSessionCleanup:
    """Test session cleanup and deletion."""

    @pytest.mark.asyncio
    async def test_delete_session(self, db_session: AsyncSession):
        """Test session deletion."""
        user = await create_user(
            db_session,
            user_id="delete_test_user",
            email="delete@example.com",
        )

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="test_token",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        # Delete session
        deleted = await delete_session(db_session, session.session_id)
        assert deleted is True

        # Verify session is gone
        retrieved = await get_session(db_session, session.session_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, db_session: AsyncSession):
        """Test deleting nonexistent session returns False."""
        deleted = await delete_session(db_session, "nonexistent_id")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, db_session: AsyncSession):
        """Test cleanup removes only expired sessions."""
        user = await create_user(
            db_session,
            user_id="cleanup_test_user",
            email="cleanup@example.com",
        )

        # Create expired session
        expired_session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="expired",
            refresh_token="expired",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )

        # Create valid session
        valid_session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="valid",
            refresh_token="valid",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )

        # Run cleanup
        deleted_count = await cleanup_expired_sessions(db_session)

        # Should delete at least the expired session
        assert deleted_count >= 1

        # Verify expired is gone, valid remains
        expired_check = await get_session(db_session, expired_session.session_id)
        valid_check = await get_session(db_session, valid_session.session_id)

        assert expired_check is None
        assert valid_check is not None
