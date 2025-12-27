"""
Google OAuth 2.1 configuration.

This module provides configuration for the OAuth authorization code flow
with PKCE for authenticating users via Google.
"""

from google_auth_oauthlib.flow import Flow

from app.config.settings import settings

# OAuth scopes requested from Google
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def create_oauth_flow() -> Flow:
    """
    Create Google OAuth flow instance.

    Returns:
        Flow: Configured OAuth flow for authorization code grant.
    """
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.OAUTH_REDIRECT_URI,
    )
