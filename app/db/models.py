"""
SQLAlchemy database models for the Task Manager MCP Server.

This module defines the database schema using SQLAlchemy 2.0 async ORM.
All models follow the data model specification in data-model.md.
"""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, JSON, LargeBinary, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False, index=True
    )

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

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="tasks")

    def __repr__(self) -> str:
        """String representation of Task model."""
        return (
            f"<Task(id={self.id}, title='{self.title}', "
            f"priority={self.priority}, completed={self.completed})>"
        )


class User(Base):
    """
    User model for OAuth 2.1 authentication.

    Stores authenticated user information from Google OAuth.

    Attributes:
        user_id: Google user ID (sub claim from ID token)
        email: Google account email address
        name: Display name from Google profile (optional)
        created_at: First authentication timestamp
        last_login: Most recent authentication timestamp
    """

    __tablename__ = "users"

    # Primary Key
    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)

    # User Info
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_login: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="user")

    def __repr__(self) -> str:
        """String representation of User model."""
        return f"<User(user_id='{self.user_id}', email='{self.email}', name='{self.name}')>"


class Session(Base):
    """
    Session model for OAuth 2.1 session state.

    Stores OAuth session state with encrypted tokens.

    Attributes:
        session_id: Cryptographically random session identifier
        user_id: Reference to User.user_id
        access_token: Encrypted Google OAuth access token (AES-256)
        refresh_token: Encrypted Google OAuth refresh token (AES-256)
        expires_at: Access token expiration timestamp
        created_at: Session creation timestamp
        last_activity: Most recent request using this session
        user_agent: Client User-Agent header for audit trail
    """

    __tablename__ = "sessions"

    # Primary Key
    session_id: Mapped[str] = mapped_column(String(43), primary_key=True)

    # Foreign Key
    user_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False
    )

    # Encrypted Tokens
    access_token: Mapped[bytes] = mapped_column(LargeBinary(512), nullable=False)
    refresh_token: Mapped[bytes] = mapped_column(LargeBinary(512), nullable=False)

    # Timestamps
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Audit
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index("idx_session_user_id", "user_id"),
        Index("idx_session_expires_at", "expires_at"),
        Index("idx_session_last_activity", "last_activity"),
    )

    def __repr__(self) -> str:
        """String representation of Session model."""
        return (
            f"<Session(session_id='{self.session_id}', user_id='{self.user_id}', "
            f"expires_at='{self.expires_at}')>"
        )


class DynamicClient(Base):
    """
    DynamicClient model for RFC 7591 Dynamic Client Registration.

    Stores registered OAuth clients for mobile/desktop applications.

    Attributes:
        client_id: Generated client identifier (UUID)
        client_secret: Encrypted client secret (AES-256)
        platform: Client platform (ios, android, macos, windows, linux, cli)
        redirect_uris: Allowed OAuth callback URIs (JSON array)
        created_at: Registration timestamp
        expires_at: Credential expiration (30 days)
        last_used: Most recent usage timestamp
    """

    __tablename__ = "dynamic_clients"

    # Primary Key
    client_id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Encrypted Secret
    client_secret: Mapped[bytes] = mapped_column(LargeBinary(512), nullable=False)

    # Client Info
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    redirect_uris: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Indexes
    __table_args__ = (
        Index("idx_dynamic_client_expires_at", "expires_at"),
        Index("idx_dynamic_client_platform", "platform"),
    )

    def __repr__(self) -> str:
        """String representation of DynamicClient model."""
        return (
            f"<DynamicClient(client_id='{self.client_id}', platform='{self.platform}', "
            f"expires_at='{self.expires_at}')>"
        )
