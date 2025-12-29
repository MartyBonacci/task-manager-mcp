"""
Database session management and connection handling.

This module provides async database session management using SQLAlchemy 2.0.
Sessions are created per-request using dependency injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings

# Create async engine with production-ready connection pool settings
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
    pool_pre_ping=True,  # Check connection health before using
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_size=5,  # Maximum number of connections in the pool
    max_overflow=10,  # Maximum overflow connections
    connect_args={
        "server_settings": {"jit": "off"},  # Disable JIT for Neon compatibility
        "command_timeout": 60,  # 60 second command timeout
        "timeout": 10,  # 10 second connection timeout
    },
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection for database sessions.

    Yields an async database session that is automatically closed
    after the request completes.

    Usage:
        @app.get("/tasks")
        async def get_tasks(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        AsyncSession: Database session for the current request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database tables.

    Creates all tables defined in Base.metadata if they don't exist.
    This should be called once during application startup.

    Note: In production, use Alembic migrations instead of this function.
    """
    from app.db.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
