"""
Custom exception classes for Task Manager MCP Server.

Provides structured error handling for OAuth, MCP, and API operations.
"""

from typing import Any, Optional


# Base exception classes


class TaskManagerException(Exception):
    """Base exception for all Task Manager errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)


# OAuth 2.1 exceptions


class OAuthException(TaskManagerException):
    """Base exception for OAuth-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        detail: Optional[dict[str, Any]] = None,
    ):
        self.error_code = error_code
        super().__init__(message, status_code, detail)


class InvalidStateException(OAuthException):
    """OAuth state parameter validation failed (CSRF protection)."""

    def __init__(self, message: str = "Invalid state parameter"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="invalid_state",
        )


class InvalidAuthorizationCodeException(OAuthException):
    """Authorization code is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired authorization code"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="invalid_grant",
        )


class InvalidTokenException(OAuthException):
    """Access token or refresh token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="invalid_token",
        )


class TokenExpiredException(OAuthException):
    """Access token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="token_expired",
        )


class InsufficientScopeException(OAuthException):
    """Token lacks required scopes."""

    def __init__(self, required_scope: str, message: Optional[str] = None):
        msg = message or f"Insufficient scope. Required: {required_scope}"
        super().__init__(
            message=msg,
            status_code=403,
            error_code="insufficient_scope",
            detail={"required_scope": required_scope},
        )


# Dynamic Client Registration (RFC 7591) exceptions


class DynamicClientException(TaskManagerException):
    """Base exception for dynamic client registration errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        detail: Optional[dict[str, Any]] = None,
    ):
        self.error_code = error_code
        super().__init__(message, status_code, detail)


class InvalidClientException(DynamicClientException):
    """Client credentials are invalid."""

    def __init__(self, message: str = "Invalid client credentials"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="invalid_client",
        )


class InvalidRedirectUriException(DynamicClientException):
    """Redirect URI is not registered for this client."""

    def __init__(self, redirect_uri: str, message: Optional[str] = None):
        msg = message or f"Redirect URI not registered for client: {redirect_uri}"
        super().__init__(
            message=msg,
            status_code=400,
            error_code="invalid_redirect_uri",
            detail={"redirect_uri": redirect_uri},
        )


class ClientExpiredException(DynamicClientException):
    """Client registration has expired."""

    def __init__(self, message: str = "Client registration has expired"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="client_expired",
        )


class InvalidPlatformException(DynamicClientException):
    """Platform is not supported."""

    def __init__(self, platform: str, valid_platforms: list[str]):
        super().__init__(
            message=f"Invalid platform: {platform}",
            status_code=400,
            error_code="invalid_platform",
            detail={
                "platform": platform,
                "valid_platforms": valid_platforms,
            },
        )


# Session management exceptions


class SessionException(TaskManagerException):
    """Base exception for session-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 401,
        detail: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, detail)


class SessionNotFoundException(SessionException):
    """Session not found in database."""

    def __init__(self, session_id: str):
        super().__init__(
            message="Session not found",
            status_code=404,
            detail={"session_id": session_id},
        )


class SessionExpiredException(SessionException):
    """Session has expired."""

    def __init__(self, message: str = "Session has expired"):
        super().__init__(message=message, status_code=401)


class InvalidRefreshTokenException(SessionException):
    """Refresh token does not match stored token."""

    def __init__(self, message: str = "Invalid refresh token"):
        super().__init__(message=message, status_code=401)


# MCP protocol exceptions


class MCPException(TaskManagerException):
    """Base exception for MCP protocol errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        mcp_error_code: int = -32603,
        detail: Optional[dict[str, Any]] = None,
    ):
        self.mcp_error_code = mcp_error_code
        super().__init__(message, status_code, detail)


class MCPInvalidRequestException(MCPException):
    """Invalid MCP request format."""

    def __init__(self, message: str = "Invalid request"):
        super().__init__(
            message=message,
            status_code=400,
            mcp_error_code=-32600,
        )


class MCPMethodNotFoundException(MCPException):
    """MCP method or tool not found."""

    def __init__(self, method_name: str):
        super().__init__(
            message=f"Method not found: {method_name}",
            status_code=404,
            mcp_error_code=-32601,
            detail={"method": method_name},
        )


class MCPInvalidParamsException(MCPException):
    """Invalid parameters for MCP method."""

    def __init__(self, message: str, param_name: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            mcp_error_code=-32602,
            detail={"param": param_name} if param_name else {},
        )


class MCPInternalErrorException(MCPException):
    """Internal error during MCP method execution."""

    def __init__(self, message: str = "Internal error"):
        super().__init__(
            message=message,
            status_code=500,
            mcp_error_code=-32603,
        )


class MCPAuthenticationRequiredException(MCPException):
    """MCP method requires authentication."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            mcp_error_code=-32000,  # Custom MCP error code
        )


# Task management exceptions


class TaskException(TaskManagerException):
    """Base exception for task-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, detail)


class TaskNotFoundException(TaskException):
    """Task not found for this user."""

    def __init__(self, task_id: str):
        super().__init__(
            message="Task not found",
            status_code=404,
            detail={"task_id": task_id},
        )


class TaskValidationException(TaskException):
    """Task data validation failed."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=400,
            detail={"field": field} if field else {},
        )


class TaskPermissionException(TaskException):
    """User does not have permission to access this task."""

    def __init__(self, task_id: str):
        super().__init__(
            message="You do not have permission to access this task",
            status_code=403,
            detail={"task_id": task_id},
        )


# User management exceptions


class UserException(TaskManagerException):
    """Base exception for user-related errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 400,
        detail: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, detail)


class UserNotFoundException(UserException):
    """User not found in database."""

    def __init__(self, user_id: str):
        super().__init__(
            message="User not found",
            status_code=404,
            detail={"user_id": user_id},
        )


class UserAlreadyExistsException(UserException):
    """User with this email already exists."""

    def __init__(self, email: str):
        super().__init__(
            message="User with this email already exists",
            status_code=409,
            detail={"email": email},
        )


# Database exceptions


class DatabaseException(TaskManagerException):
    """Base exception for database errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, detail)


class DatabaseConnectionException(DatabaseException):
    """Database connection failed."""

    def __init__(self, message: str = "Database connection failed"):
        super().__init__(message=message, status_code=503)


class DatabaseOperationException(DatabaseException):
    """Database operation failed."""

    def __init__(self, operation: str, message: Optional[str] = None):
        msg = message or f"Database operation failed: {operation}"
        super().__init__(
            message=msg,
            status_code=500,
            detail={"operation": operation},
        )


# Configuration exceptions


class ConfigurationException(TaskManagerException):
    """Base exception for configuration errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        detail: Optional[dict[str, Any]] = None,
    ):
        super().__init__(message, status_code, detail)


class MissingConfigException(ConfigurationException):
    """Required configuration value is missing."""

    def __init__(self, config_key: str):
        super().__init__(
            message=f"Missing required configuration: {config_key}",
            status_code=500,
            detail={"config_key": config_key},
        )


class InvalidConfigException(ConfigurationException):
    """Configuration value is invalid."""

    def __init__(self, config_key: str, reason: str):
        super().__init__(
            message=f"Invalid configuration: {config_key} - {reason}",
            status_code=500,
            detail={"config_key": config_key, "reason": reason},
        )
