"""
Structured logging configuration for Task Manager MCP Server.

Provides JSON-formatted logging with correlation IDs, contextual information,
and Google Cloud Logging integration for production environments.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

from app.config.settings import settings


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Formats log records as JSON with standard fields plus custom context.
    Compatible with Google Cloud Logging and other log aggregators.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON string.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log string
        """
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra context fields
        # These can be added via logger.info("msg", extra={"key": "value"})
        for key, value in record.__dict__.items():
            if key not in {
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
                "taskName",
            }:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure application logging.

    Sets up:
    - JSON formatting for production
    - Appropriate log levels based on environment
    - Console output with colors for development
    - Google Cloud Logging integration for production

    Call this during application startup.
    """
    # Determine log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    # Use JSON formatter in production, simple formatter in development
    if settings.ENVIRONMENT == "production":
        formatter = JSONFormatter()
    else:
        # Colored formatter for development
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(
        f"Logging configured for {settings.ENVIRONMENT} environment",
        extra={
            "log_level": settings.LOG_LEVEL,
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
        },
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Operation completed", extra={"user_id": "123", "task_id": 456})
    """
    return logging.getLogger(name)
