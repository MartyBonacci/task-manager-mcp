"""
Authentication and user context management.

Phase 1: Mock authentication with hardcoded user_id
Phase 2+: OAuth 2.1 integration with Google/GitHub
"""

from typing import Any

from app.config.settings import settings


class AuthService:
    """
    Authentication service for user context management.

    Phase 1 Implementation:
        - Returns hardcoded user_id from settings
        - No actual authentication performed
        - Prepares interface for Phase 2 OAuth integration

    Phase 2+ Implementation:
        - OAuth 2.1 token validation
        - User session management
        - JWT token handling
    """

    @staticmethod
    def get_current_user_id() -> str:
        """
        Get the current authenticated user's ID.

        In Phase 1, this always returns the mock user ID from settings.
        In Phase 2+, this will validate OAuth tokens and return the actual user ID.

        Returns:
            str: The current user's ID (mock in Phase 1)

        Example:
            user_id = AuthService.get_current_user_id()
            tasks = await task_service.list_tasks(user_id)
        """
        return settings.MOCK_USER_ID

    @staticmethod
    def validate_user_access(user_id: str, resource_user_id: str) -> bool:
        """
        Validate that a user has access to a specific resource.

        Ensures user isolation by checking that the requesting user
        matches the resource owner.

        Args:
            user_id: The requesting user's ID
            resource_user_id: The user ID associated with the resource

        Returns:
            bool: True if access is allowed, False otherwise

        Raises:
            PermissionError: If user_id doesn't match resource_user_id

        Example:
            if not AuthService.validate_user_access(user_id, task.user_id):
                raise PermissionError("Access denied")
        """
        if user_id != resource_user_id:
            return False
        return True

    @staticmethod
    async def get_user_preferences(user_id: str) -> dict[str, Any] | None:
        """
        Get user preferences (placeholder for Phase 2+).

        Args:
            user_id: The user's ID

        Returns:
            Optional[dict]: User preferences (None in Phase 1)

        Note:
            This is a placeholder for Phase 2 implementation.
            In Phase 2, this will fetch actual user preferences from the database.
        """
        # Phase 1: No user preferences
        return None


# Convenience function for dependency injection
def get_current_user_id() -> str:
    """
    FastAPI dependency for getting current user ID.

    Usage:
        @app.get("/tasks")
        async def get_tasks(user_id: str = Depends(get_current_user_id)):
            # user_id is automatically injected
            pass

    Returns:
        str: Current user's ID
    """
    return AuthService.get_current_user_id()
