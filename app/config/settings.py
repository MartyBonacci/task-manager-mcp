"""
Application settings and configuration management.

This module provides centralized configuration using Pydantic Settings,
loading values from environment variables with sensible defaults.
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.

    All settings can be overridden via environment variables.
    See .env.example for available configuration options.
    """

    # Application Info
    APP_NAME: str = "Task Manager MCP Server"
    VERSION: str = "0.1.0"
    DEBUG: bool = False

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./tasks.db"

    # MCP Configuration
    MCP_PROTOCOL_VERSION: str = "2025-06-18"

    # Authentication (Phase 1: Mock user)
    MOCK_USER_ID: str = "dev-user"

    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    # OAuth 2.1 Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    OAUTH_REDIRECT_URI: str
    ENCRYPTION_KEY: str
    DEVELOPMENT_MODE: bool = False

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
settings = Settings()
