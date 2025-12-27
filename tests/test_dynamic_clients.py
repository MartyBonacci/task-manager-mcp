"""
Integration tests for dynamic client registration (RFC 7591).

Tests client registration, validation, and OAuth flow with
dynamically registered clients.
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.client_service import (
    cleanup_expired_clients,
    generate_client_id,
    generate_client_secret,
    get_client,
    register_client,
    validate_client,
    validate_redirect_uri,
)


class TestClientRegistration:
    """Test RFC 7591 client registration."""

    @pytest.mark.asyncio
    async def test_register_client_via_api(self):
        """Test registering client through API endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/register",
                json={
                    "platform": "ios",
                    "redirect_uris": ["myapp://oauth/callback"],
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify response structure
            assert "client_id" in data
            assert "client_secret" in data
            assert data["platform"] == "ios"
            assert data["redirect_uris"] == ["myapp://oauth/callback"]
            assert "expires_at" in data

            # Client ID should have prefix
            assert data["client_id"].startswith("client_")

    @pytest.mark.asyncio
    async def test_register_invalid_platform(self):
        """Test registration fails with invalid platform."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/register",
                json={
                    "platform": "invalid_platform",
                    "redirect_uris": ["myapp://callback"],
                },
            )

            # Pydantic validation errors return 422 (Unprocessable Entity)
            assert response.status_code == 422
            # Check validation error details
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_register_empty_redirect_uris(self):
        """Test registration fails without redirect URIs."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/register",
                json={
                    "platform": "android",
                    "redirect_uris": [],
                },
            )

            assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_register_invalid_redirect_uri_format(self):
        """Test registration fails with invalid URI format."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/clients/register",
                json={
                    "platform": "cli",
                    "redirect_uris": ["invalid-uri"],
                },
            )

            assert response.status_code == 400
            assert "Invalid redirect URI format" in response.json()["detail"]


class TestClientValidation:
    """Test client credential validation."""

    @pytest.mark.asyncio
    async def test_validate_client_credentials(self, db_session: AsyncSession):
        """Test validating client credentials."""
        # Register client (captures plain text secret for validation)
        client, secret = await register_client(
            db_session,
            platform="macos",
            redirect_uris=["myapp://callback"],
        )

        # Validate with correct credentials (using plain text secret)
        is_valid = await validate_client(
            db_session,
            client_id=client.client_id,
            client_secret=secret,
        )

        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_wrong_secret(self, db_session: AsyncSession):
        """Test validation fails with wrong secret."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="windows",
            redirect_uris=["http://localhost:8080/callback"],
        )

        # Validate with wrong secret
        is_valid = await validate_client(
            db_session,
            client_id=client.client_id,
            client_secret="wrong_secret",
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_nonexistent_client(self, db_session: AsyncSession):
        """Test validation fails for nonexistent client."""
        is_valid = await validate_client(
            db_session,
            client_id="nonexistent_client_id",
            client_secret="any_secret",
        )

        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_expired_client(self, db_session: AsyncSession):
        """Test validation fails for expired client."""
        # Register client that expired 1 day ago
        client, _secret = await register_client(
            db_session,
            platform="linux",
            redirect_uris=["http://localhost/callback"],
            expires_in_days=-1,  # Expired yesterday
        )

        # Should fail validation
        is_valid = await validate_client(
            db_session,
            client_id=client.client_id,
            client_secret=client.client_secret,
        )

        assert is_valid is False


class TestRedirectURIValidation:
    """Test redirect URI validation."""

    @pytest.mark.asyncio
    async def test_validate_registered_redirect_uri(self, db_session: AsyncSession):
        """Test validating registered redirect URI."""
        # Register client with multiple URIs
        client, _secret = await register_client(
            db_session,
            platform="ios",
            redirect_uris=[
                "myapp://oauth/callback",
                "myapp://oauth/alternate",
            ],
        )

        # Validate first URI
        is_valid1 = await validate_redirect_uri(
            db_session,
            client_id=client.client_id,
            redirect_uri="myapp://oauth/callback",
        )

        # Validate second URI
        is_valid2 = await validate_redirect_uri(
            db_session,
            client_id=client.client_id,
            redirect_uri="myapp://oauth/alternate",
        )

        assert is_valid1 is True
        assert is_valid2 is True

    @pytest.mark.asyncio
    async def test_validate_unregistered_redirect_uri(self, db_session: AsyncSession):
        """Test validation fails for unregistered URI."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="android",
            redirect_uris=["myapp://callback"],
        )

        # Try to validate unregistered URI
        is_valid = await validate_redirect_uri(
            db_session,
            client_id=client.client_id,
            redirect_uri="myapp://evil/callback",
        )

        assert is_valid is False


class TestClientManagement:
    """Test client management endpoints."""

    @pytest.mark.asyncio
    async def test_get_client_info(self, db_session: AsyncSession):
        """Test getting client information."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="cli",
            redirect_uris=["http://localhost:8000/callback"],
        )

        # Get info via API
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            response = await http_client.get(f"/clients/{client.client_id}")

            assert response.status_code == 200
            data = response.json()

            # Verify secret is NOT included
            assert "client_secret" not in data
            assert data["client_id"] == client.client_id
            assert data["platform"] == "cli"

    @pytest.mark.asyncio
    async def test_get_nonexistent_client(self):
        """Test getting nonexistent client returns 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/nonexistent_client_id")

            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_client(self, db_session: AsyncSession):
        """Test revoking client registration."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="ios",
            redirect_uris=["myapp://callback"],
        )

        # Revoke via API
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            response = await http_client.delete(f"/clients/{client.client_id}")

            assert response.status_code == 200
            assert "revoked" in response.json()["message"].lower()

        # Verify client is gone
        retrieved = await get_client(db_session, client.client_id)
        assert retrieved is None

    @pytest.mark.asyncio
    async def test_list_clients(self, db_session: AsyncSession):
        """Test listing registered clients."""
        # Register multiple clients
        await register_client(
            db_session,
            platform="ios",
            redirect_uris=["ios://callback"],
        )

        await register_client(
            db_session,
            platform="android",
            redirect_uris=["android://callback"],
        )

        # List all clients
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/")

            assert response.status_code == 200
            data = response.json()
            assert "clients" in data
            assert len(data["clients"]) >= 2

    @pytest.mark.asyncio
    async def test_list_clients_by_platform(self, db_session: AsyncSession):
        """Test listing clients filtered by platform."""
        # Register clients
        await register_client(
            db_session,
            platform="macos",
            redirect_uris=["macos://callback"],
        )

        await register_client(
            db_session,
            platform="windows",
            redirect_uris=["windows://callback"],
        )

        # List macOS clients
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/clients/?platform=macos")

            assert response.status_code == 200
            data = response.json()
            clients = data["clients"]

            # All should be macOS
            assert all(c["platform"] == "macos" for c in clients)


class TestClientCleanup:
    """Test client expiration and cleanup."""

    @pytest.mark.asyncio
    async def test_cleanup_expired_clients(self, db_session: AsyncSession):
        """Test cleanup removes expired clients."""
        # Register expired client
        expired = await register_client(
            db_session,
            platform="cli",
            redirect_uris=["http://localhost/callback"],
            expires_in_days=-1,  # Expired
        )

        # Register valid client
        valid = await register_client(
            db_session,
            platform="cli",
            redirect_uris=["http://localhost/callback"],
            expires_in_days=365,
        )

        # Run cleanup
        deleted_count = await cleanup_expired_clients(db_session)

        # Should delete at least the expired client
        assert deleted_count >= 1

        # Verify expired is gone, valid remains
        expired_check = await get_client(db_session, expired.client_id)
        valid_check = await get_client(db_session, valid.client_id)

        assert expired_check is None
        assert valid_check is not None


class TestDynamicClientOAuthFlow:
    """Test OAuth flow with dynamically registered clients."""

    @pytest.mark.asyncio
    async def test_authorize_with_dynamic_client(self, db_session: AsyncSession):
        """Test OAuth authorize with dynamic client."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="ios",
            redirect_uris=["myapp://oauth/callback"],
        )

        # Call authorize with client params
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            response = await http_client.get(
                "/oauth/authorize",
                params={
                    "client_id": client.client_id,
                    "redirect_uri": "myapp://oauth/callback",
                },
                follow_redirects=False,
            )

            # Should redirect to Google OAuth
            assert response.status_code == 307
            assert "accounts.google.com" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_authorize_with_invalid_redirect_uri(self, db_session: AsyncSession):
        """Test authorize rejects unregistered redirect URI."""
        # Register client
        client, _secret = await register_client(
            db_session,
            platform="android",
            redirect_uris=["myapp://callback"],
        )

        # Try authorize with different URI
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as http_client:
            response = await http_client.get(
                "/oauth/authorize",
                params={
                    "client_id": client.client_id,
                    "redirect_uri": "evil://callback",
                },
            )

            assert response.status_code == 400
            assert "not registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_authorize_missing_client_id(self):
        """Test authorize requires both client_id and redirect_uri."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Provide redirect_uri but no client_id
            response = await client.get(
                "/oauth/authorize",
                params={"redirect_uri": "myapp://callback"},
            )

            assert response.status_code == 400
            assert "Both client_id and redirect_uri" in response.json()["detail"]


class TestClientCredentialGeneration:
    """Test client credential generation utilities."""

    def test_generate_client_id_format(self):
        """Test client ID generation format."""
        client_id = generate_client_id()

        assert client_id.startswith("client_")
        assert len(client_id) > 20  # Should be substantial length

    def test_generate_client_id_uniqueness(self):
        """Test client IDs are unique."""
        id1 = generate_client_id()
        id2 = generate_client_id()

        assert id1 != id2

    def test_generate_client_secret_format(self):
        """Test client secret generation."""
        secret = generate_client_secret()

        assert len(secret) > 30  # Should be long
        assert isinstance(secret, str)

    def test_generate_client_secret_uniqueness(self):
        """Test client secrets are unique."""
        secret1 = generate_client_secret()
        secret2 = generate_client_secret()

        assert secret1 != secret2
