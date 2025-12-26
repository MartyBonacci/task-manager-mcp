"""
SQLAlchemy database models for the Task Manager MCP Server.

This module defines the database schema using SQLAlchemy 2.0 async ORM.
All models follow the data model specification in data-model.md.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""



class Task(Base):
    """
    Task model representing a single actionable item.

    Attributes:
        id: Unique task identifier (auto-generated)
        user_id: Owner of the task (FK to users.user_id)
        title: Task title (1-500 characters)
        project: Optional project/category for organization
        priority: Priority level (1=Someday, 2=Low, 3=Medium, 4=High, 5=Critical)
        energy: Energy level required (light | medium | deep)
        time_estimate: Estimated time to complete (e.g., "1hr", "30min")
        notes: Optional additional task notes/description
        due_date: Optional due date (ISO 8601 format)
        completed: Task completion status
        completed_at: Timestamp when task was completed
        created_at: Creation timestamp (auto-generated)
        updated_at: Last update timestamp (auto-updated)
    """

    __tablename__ = "tasks"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, index=True)

    # User Ownership (for multi-user support in Phase 2+)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)

    # Core Task Fields
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    project: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)

    # Priority & Energy
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=3, index=True)
    energy: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    time_estimate: Mapped[str] = mapped_column(String(50), nullable=False, default="1hr")

    # Details
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)

    # Status
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    completed_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[str] = mapped_column(
        String(50), nullable=False, default=lambda: datetime.now(UTC).isoformat()
    )
    updated_at: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default=lambda: datetime.now(UTC).isoformat(),
        onupdate=lambda: datetime.now(UTC).isoformat(),
    )

    def __repr__(self) -> str:
        """String representation of Task model."""
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"priority={self.priority}, completed={self.completed})>"
        )


class User(Base):
    """
    User model for authentication and preferences.

    Note: Phase 1 uses a hardcoded "dev-user". This model is prepared
    for Phase 2 OAuth 2.1 integration.

    Attributes:
        user_id: Unique user identifier (from OAuth in Phase 2)
        email: User's email address
        preferences: JSON blob for user preferences
        created_at: Account creation timestamp
    """

    __tablename__ = "users"

    # Primary Key
    user_id: Mapped[str] = mapped_column(String, primary_key=True)

    # User Info
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)

    # Preferences (JSON blob stored as string)
    preferences: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[str] = mapped_column(
        String(50), nullable=False, default=lambda: datetime.now(UTC).isoformat()
    )

    def __repr__(self) -> str:
        """String representation of User model."""
        return f"<User(user_id='{self.user_id}', email='{self.email}')>"
