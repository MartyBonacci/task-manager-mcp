"""
Integration tests for MCP authentication.

Tests that MCP tool calls require valid OAuth sessions and properly
authenticate users.
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.session_service import create_session
from app.services.user_service import create_user


class TestMCPAuthenticationRequired:
    """Test that MCP tools require authentication."""

    @pytest.mark.asyncio
    async def test_mcp_initialize_no_auth(self):
        """Test /mcp/initialize works without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/mcp/initialize")

            # Initialize should work without auth
            assert response.status_code == 200
            assert response.json()["protocolVersion"] == "2025-06-18"

    @pytest.mark.asyncio
    async def test_mcp_tools_list_no_auth(self):
        """Test /mcp/tools/list works without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/mcp/tools/list")

            # Tools list should work without auth
            assert response.status_code == 200
            assert "tools" in response.json()
            assert len(response.json()["tools"]) > 0

    @pytest.mark.asyncio
    async def test_mcp_tools_call_requires_auth(self):
        """Test /mcp/tools/call requires authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={
                    "name": "task_list",
                    "params": {},
                },
            )

            # Should fail without authentication
            assert response.status_code == 401
            assert "Authentication required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_mcp_tools_call_invalid_session(self):
        """Test tool call with invalid session ID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={
                    "name": "task_list",
                    "params": {},
                },
                headers={"Authorization": "Bearer invalid_session_id"},
            )

            # Should fail with invalid session
            assert response.status_code == 401
            assert "Invalid or expired session" in response.json()["detail"]


class TestMCPAuthenticatedAccess:
    """Test MCP tools with valid authentication."""

    @pytest.mark.asyncio
    async def test_mcp_tools_call_with_valid_session(self, db_session: AsyncSession):
        """Test tool call with valid session."""
        # Create test user
        user = await create_user(
            db_session,
            user_id="mcp_test_user",
            email="mcp@example.com",
            name="MCP Test User",
        )

        # Create valid session
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="mcp_access_token",
            refresh_token="mcp_refresh_token",
            expires_at=expires_at,
        )

        # Call MCP tool with valid session
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={
                    "name": "task_list",
                    "params": {},
                },
                headers={"Authorization": f"Bearer {session.session_id}"},
            )

            # Should succeed with valid session
            assert response.status_code == 200
            assert "content" in response.json()

    @pytest.mark.asyncio
    async def test_mcp_create_task_authenticated(self, db_session: AsyncSession):
        """Test creating task through MCP with authentication."""
        # Create test user
        user = await create_user(
            db_session,
            user_id="task_creator",
            email="creator@example.com",
            name="Task Creator",
        )

        # Create valid session
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        session = await create_session(
            db_session,
            user_id=user.user_id,
            access_token="creator_access",
            refresh_token="creator_refresh",
            expires_at=expires_at,
        )

        # Create task via MCP
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={
                    "name": "task_create",
                    "params": {
                        "title": "Authenticated task",
                        "priority": 4,
                    },
                },
                headers={"Authorization": f"Bearer {session.session_id}"},
            )

            # Should succeed
            assert response.status_code == 200
            result = response.json()
            assert "content" in result


class TestAuthorizationHeader:
    """Test Authorization header parsing."""

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        """Test request without Authorization header."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={"name": "task_list", "params": {}},
            )

            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_authorization_format(self):
        """Test Authorization header with wrong format."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={"name": "task_list", "params": {}},
                headers={"Authorization": "InvalidFormat session_id"},
            )

            assert response.status_code == 401
            assert "Invalid authorization header format" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_bearer_without_token(self):
        """Test Bearer token without session ID."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={"name": "task_list", "params": {}},
                headers={"Authorization": "Bearer "},
            )

            assert response.status_code == 401
            assert "Missing session ID" in response.json()["detail"]
