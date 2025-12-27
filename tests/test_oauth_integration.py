"""
Integration tests for OAuth 2.1 authentication flow.

Tests the complete OAuth workflow including authorization, callback,
token refresh, and session management.
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.session_service import create_session, validate_session
from app.services.user_service import create_user


class TestOAuthFlow:
    """Test OAuth 2.1 authorization flow."""

    @pytest.mark.asyncio
    async def test_oauth_authorize_redirect(self):
        """Test /oauth/authorize redirects to Google."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/oauth/authorize", follow_redirects=False)

            # Should redirect to Google OAuth
            assert response.status_code == 307
            assert "accounts.google.com" in response.headers["location"]
            assert "state=" in response.headers["location"]
            assert "scope=" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_oauth_callback_invalid_state(self):
        """Test callback rejects invalid state parameter."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/oauth/callback",
                params={
                    "code": "fake_auth_code",
                    "state": "invalid_state_token",
                },
            )

            # Should reject invalid state
            assert response.status_code == 400
            assert "Invalid state parameter" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_oauth_callback_missing_code(self):
        """Test callback requires authorization code."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First get valid state
            auth_response = await client.get("/oauth/authorize", follow_redirects=False)
            location = auth_response.headers["location"]
            state = location.split("state=")[1].split("&")[0]

            # Try callback without code
            response = await client.get(
                "/oauth/callback",
                params={"state": state},
            )

            # Should return 422 (validation error) for missing required param
            assert response.status_code == 422


class TestSessionManagement:
    """Test session creation and validation."""

    @pytest.mark.asyncio
    async def test_create_and_validate_session(self, db_session: AsyncSession):
        """Test creating and validating a session."""
        # Create test user
        user = await create_user(
            db_session,
            user_id="test_user_123",
            email="test@example.com",
            name="Test User",
        )

        # Create session
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="test_access_token",
            refresh_token="test_refresh_token",
            expires_at=expires_at,
        )

        assert session.session_id is not None
        assert session.user_id == user.user_id

        # Validate session
        is_valid = await validate_session(db_session, session.session_id)
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_expired_session(self, db_session: AsyncSession):
        """Test that expired sessions are invalid."""
        # Create test user
        user = await create_user(
            db_session,
            user_id="test_user_456",
            email="test2@example.com",
            name="Test User 2",
        )

        # Create session with past expiration
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="expired_token",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        # Validate session (should be invalid due to expiration)
        is_valid = await validate_session(db_session, session.session_id)
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_nonexistent_session(self, db_session: AsyncSession):
        """Test that nonexistent sessions are invalid."""
        is_valid = await validate_session(db_session, "nonexistent_session_id")
        assert is_valid is False


class TestTokenRefresh:
    """Test token refresh functionality."""

    @pytest.mark.asyncio
    async def test_refresh_missing_session(self):
        """Test refresh fails with nonexistent session."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/oauth/refresh",
                json={
                    "session_id": "nonexistent_session",
                    "refresh_token": "fake_token",
                },
            )

            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, db_session: AsyncSession):
        """Test refresh fails with wrong refresh token."""
        # Create test user and session
        user = await create_user(
            db_session,
            user_id="test_user_789",
            email="test3@example.com",
            name="Test User 3",
        )

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="test_access",
            refresh_token="correct_refresh_token",
            expires_at=expires_at,
        )

        # Try refresh with wrong token
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/oauth/refresh",
                json={
                    "session_id": session.session_id,
                    "refresh_token": "wrong_refresh_token",
                },
            )

            assert response.status_code == 401
            assert "Invalid refresh token" in response.json()["detail"]
