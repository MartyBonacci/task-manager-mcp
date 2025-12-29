"""
OAuth 2.1 authentication endpoints.

Implements Google OAuth authorization code flow with PKCE.
"""

import secrets
from datetime import datetime, timezone
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google.auth.transport import requests as google_requests
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.oauth import create_oauth_flow
from app.config.settings import settings
from app.db.database import get_db
from app.schemas.oauth import (
    OAuthCallbackRequest,
    OAuthRefreshRequest,
    OAuthTokenResponse,
)
from app.services.client_service import validate_client, validate_redirect_uri
from app.services.session_service import (
    create_session,
    get_decrypted_refresh_token,
    refresh_session,
)
from app.services.user_service import upsert_user

router = APIRouter(prefix="/oauth", tags=["oauth"])

# Temporary in-memory state storage
# TODO: Replace with Redis in production for distributed deployments
oauth_states: Dict[str, bool] = {}


@router.get("/authorize")
async def oauth_authorize(
    request: Request,
    client_id: str = None,
    redirect_uri: str = None,
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Initiate OAuth 2.1 authorization flow.

    Supports both web and dynamic client flows:
    - Web: No parameters (uses default Google OAuth client)
    - Dynamic: Requires client_id and redirect_uri

    Args:
        request: FastAPI request
        client_id: Optional dynamic client ID
        redirect_uri: Optional redirect URI for dynamic client
        db: Database session (injected)

    Returns:
        RedirectResponse to Google OAuth authorization URL

    Raises:
        HTTPException: If dynamic client validation fails
    """
    # Validate dynamic client if provided
    if client_id or redirect_uri:
        # Both must be provided together
        if not (client_id and redirect_uri):
            raise HTTPException(
                status_code=400,
                detail="Both client_id and redirect_uri are required for dynamic clients",
            )

        # Validate redirect URI for client
        is_valid = await validate_redirect_uri(db, client_id, redirect_uri)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail="Invalid client_id or redirect_uri not registered for client",
            )

    # Create OAuth flow (uses Google OAuth credentials)
    flow = create_oauth_flow()

    # Override redirect URI for dynamic clients
    if redirect_uri:
        flow.redirect_uri = redirect_uri

    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    oauth_states[state] = True

    # Generate authorization URL
    authorization_url, _ = flow.authorization_url(
        access_type="offline",  # Request refresh token
        include_granted_scopes="true",  # Incremental authorization
        state=state,
        prompt="consent",  # Force consent screen to always get refresh token
    )

    return RedirectResponse(url=authorization_url)


@router.get("/callback")
async def oauth_callback(
    code: str,
    state: str,
    scope: str = None,
    db: AsyncSession = Depends(get_db),
) -> OAuthTokenResponse:
    """
    Handle OAuth 2.1 callback from Google.

    Validates state parameter, exchanges authorization code for tokens,
    creates or updates user, and creates session.

    Args:
        code: Authorization code from Google
        state: CSRF protection state parameter
        scope: Granted scopes (optional)
        db: Database session (injected)

    Returns:
        OAuthTokenResponse with session_id and tokens

    Raises:
        HTTPException: If state is invalid or token exchange fails
    """
    # Validate state parameter (CSRF protection)
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    # Remove used state
    del oauth_states[state]

    # Create OAuth flow
    flow = create_oauth_flow()

    # Exchange authorization code for tokens
    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to exchange authorization code: {str(e)}"
        )

    # Get credentials
    credentials = flow.credentials

    # Get user info from ID token
    id_token_jwt = credentials.id_token
    if not id_token_jwt:
        raise HTTPException(status_code=400, detail="No ID token in response")

    # Verify and decode the ID token
    try:
        id_info = id_token.verify_oauth2_token(
            id_token_jwt, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid ID token: {str(e)}"
        )

    user_id = id_info.get("sub")
    email = id_info.get("email")
    name = id_info.get("name")

    if not user_id or not email:
        raise HTTPException(
            status_code=400, detail="Missing required user info in ID token"
        )

    # Create or update user
    user = await upsert_user(db, user_id=user_id, email=email, name=name)

    # Create session with encrypted tokens
    session = await create_session(
        db,
        user_id=user.user_id,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_at=credentials.expiry,
        user_agent=None,  # TODO: Extract from request headers
    )

    # Calculate expires_in (seconds until expiration)
    now = datetime.now(timezone.utc)
    # Ensure credentials.expiry is timezone-aware
    expiry = credentials.expiry
    if expiry.tzinfo is None:
        # If naive, assume UTC
        expiry = expiry.replace(tzinfo=timezone.utc)
    expires_in = int((expiry - now).total_seconds())

    # Return session info and tokens
    return OAuthTokenResponse(
        session_id=session.session_id,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_in=expires_in,
        token_type="Bearer",
    )


@router.post("/refresh")
async def oauth_refresh(
    request: OAuthRefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> OAuthTokenResponse:
    """
    Refresh OAuth access token using refresh token.

    Args:
        request: Refresh request with session_id and refresh_token
        db: Database session (injected)

    Returns:
        OAuthTokenResponse with new access token

    Raises:
        HTTPException: If session not found or refresh fails
    """
    # Get refresh token from session
    stored_refresh_token = await get_decrypted_refresh_token(db, request.session_id)

    if not stored_refresh_token:
        raise HTTPException(status_code=404, detail="Session not found")

    # Validate provided refresh token matches stored token
    if stored_refresh_token != request.refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Create OAuth flow to get client config
    flow = create_oauth_flow()

    # Use refresh token to get new access token
    try:
        # Create credentials object with refresh token
        credentials = Credentials(
            token=None,
            refresh_token=stored_refresh_token,
            token_uri=flow.client_config["token_uri"],
            client_id=flow.client_config["client_id"],
            client_secret=flow.client_config["client_secret"],
        )
        # Refresh to get new access token
        credentials.refresh(google_requests.Request())
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to refresh token: {str(e)}"
        )

    # Update session with new access token
    updated_session = await refresh_session(
        db,
        session_id=request.session_id,
        new_access_token=credentials.token,
        new_expires_at=credentials.expiry,
    )

    if not updated_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Calculate expires_in
    now = datetime.now(timezone.utc)
    # Ensure credentials.expiry is timezone-aware
    expiry = credentials.expiry
    if expiry.tzinfo is None:
        # If naive, assume UTC
        expiry = expiry.replace(tzinfo=timezone.utc)
    expires_in = int((expiry - now).total_seconds())

    # Return new tokens
    return OAuthTokenResponse(
        session_id=updated_session.session_id,
        access_token=credentials.token,
        refresh_token=stored_refresh_token,  # Refresh token doesn't change
        expires_in=expires_in,
        token_type="Bearer",
    )
