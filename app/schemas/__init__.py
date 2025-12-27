"""Pydantic schemas package for request/response validation."""

from app.schemas.oauth import (
    DynamicClientInfo,
    DynamicClientRegister,
    DynamicClientResponse,
    OAuthCallbackRequest,
    OAuthRefreshRequest,
    OAuthTokenResponse,
    SessionCreate,
    SessionResponse,
    SessionValidationRequest,
    SessionValidationResponse,
    UserCreate,
    UserResponse,
)

__all__ = [
    # User schemas
    "UserCreate",
    "UserResponse",
    # Session schemas
    "SessionCreate",
    "SessionResponse",
    "SessionValidationRequest",
    "SessionValidationResponse",
    # Dynamic Client schemas
    "DynamicClientRegister",
    "DynamicClientResponse",
    "DynamicClientInfo",
    # OAuth Flow schemas
    "OAuthCallbackRequest",
    "OAuthTokenResponse",
    "OAuthRefreshRequest",
]
