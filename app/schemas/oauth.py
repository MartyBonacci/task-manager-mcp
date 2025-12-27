"""
Pydantic schemas for OAuth 2.1 authentication entities.

These schemas handle request/response validation for OAuth flows,
user authentication, session management, and dynamic client registration.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# User Schemas


class UserBase(BaseModel):
    """Base User schema with common fields."""

    email: EmailStr
    name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user (from OAuth callback)."""

    user_id: str = Field(..., description="Google user ID (sub claim)")


class UserResponse(UserBase):
    """Schema for user response."""

    user_id: str
    created_at: datetime
    last_login: datetime

    model_config = ConfigDict(from_attributes=True)


# Session Schemas


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    user_id: str
    access_token: str = Field(..., description="OAuth access token (will be encrypted)")
    refresh_token: str = Field(..., description="OAuth refresh token (will be encrypted)")
    expires_at: datetime = Field(..., description="Access token expiration timestamp")
    user_agent: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for session response (excludes encrypted tokens)."""

    session_id: str
    user_id: str
    expires_at: datetime
    created_at: datetime
    last_activity: datetime

    model_config = ConfigDict(from_attributes=True)


# Dynamic Client Schemas


class DynamicClientRegister(BaseModel):
    """Schema for RFC 7591 Dynamic Client Registration request."""

    platform: str = Field(..., pattern="^(ios|android|macos|windows|linux|cli)$")
    redirect_uris: list[str] = Field(..., min_length=1, max_length=5)


class DynamicClientResponse(BaseModel):
    """Schema for Dynamic Client Registration response."""

    client_id: str
    client_secret: str = Field(..., description="Return once, cannot be retrieved later")
    platform: str
    redirect_uris: list[str]
    expires_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DynamicClientInfo(BaseModel):
    """Schema for Dynamic Client information (excludes secret)."""

    client_id: str
    platform: str
    redirect_uris: list[str]
    created_at: datetime
    expires_at: datetime
    last_used: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# OAuth Flow Schemas


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback query parameters."""

    code: str = Field(..., description="Authorization code from Google")
    state: str = Field(..., description="CSRF protection state")
    scope: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response to client."""

    session_id: str
    access_token: str
    refresh_token: str
    expires_in: int = Field(..., description="Seconds until access token expires")
    token_type: str = "Bearer"


class OAuthRefreshRequest(BaseModel):
    """Schema for token refresh request."""

    session_id: str
    refresh_token: str


# Session Validation Schemas


class SessionValidationRequest(BaseModel):
    """Schema for session validation request."""

    session_id: str


class SessionValidationResponse(BaseModel):
    """Schema for session validation response."""

    valid: bool
    user_id: Optional[str] = None
    expires_at: Optional[datetime] = None
