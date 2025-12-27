"""
Pytest configuration and shared fixtures.

This module provides common test fixtures for database sessions,
test data, and utilities used across all test files.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import settings
from app.db.models import Base, Task

# Test database URL (in-memory SQLite)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Create test session factory
TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_engine():
    """
    Clean up test engine after all tests complete.

    This fixture runs automatically at session scope and ensures
    the async engine is properly disposed, allowing pytest to exit cleanly.
    """
    yield  # Run all tests first

    # After all tests complete, dispose the engine
    await test_engine.dispose()


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for test session with proper cleanup."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Tables are created before the test and dropped after,
    ensuring test isolation.

    Yields:
        AsyncSession: Test database session
    """
    # Import here to avoid circular imports
    from unittest.mock import patch
    import app.db.session as db_session_module
    from app.db.session import get_db
    from app.main import app

    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestAsyncSessionLocal() as session:
        # Override get_db function for both FastAPI dependency injection and direct calls
        async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
            try:
                yield session
            finally:
                # Don't close - let the fixture handle cleanup
                pass

        # Override FastAPI dependency injection
        app.dependency_overrides[get_db] = override_get_db

        # Monkeypatch get_db in the middleware module where it's used
        # (middleware calls get_db() directly, not via Depends)
        import app.api.middleware as middleware_module
        with patch.object(middleware_module, 'get_db', override_get_db):
            yield session

        # Clear dependency overrides
        app.dependency_overrides.clear()

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_user_id() -> str:
    """
    Get test user ID.

    Returns:
        str: Mock user ID for testing
    """
    return settings.MOCK_USER_ID


@pytest_asyncio.fixture
async def sample_task(db_session: AsyncSession, test_user_id: str) -> Task:
    """
    Create a sample task for testing.

    Args:
        db_session: Test database session
        test_user_id: Test user ID

    Returns:
        Task: Created task instance
    """
    task = Task(
        user_id=test_user_id,
        title="Sample Test Task",
        project="Test Project",
        priority=3,
        energy="medium",
        time_estimate="1hr",
        notes="Test notes",
        completed=False,
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    return task


@pytest_asyncio.fixture
async def multiple_tasks(db_session: AsyncSession, test_user_id: str) -> list[Task]:
    """
    Create multiple sample tasks for testing.

    Args:
        db_session: Test database session
        test_user_id: Test user ID

    Returns:
        list[Task]: List of created tasks
    """
    tasks = [
        Task(
            user_id=test_user_id,
            title="High Priority Task",
            project="Work",
            priority=5,
            energy="deep",
            time_estimate="2hr",
            completed=False,
        ),
        Task(
            user_id=test_user_id,
            title="Medium Priority Task",
            project="Personal",
            priority=3,
            energy="medium",
            time_estimate="1hr",
            completed=False,
        ),
        Task(
            user_id=test_user_id,
            title="Completed Task",
            project="Work",
            priority=4,
            energy="medium",
            time_estimate="1hr",
            completed=True,
        ),
    ]

    for task in tasks:
        db_session.add(task)

    await db_session.commit()

    for task in tasks:
        await db_session.refresh(task)

    return tasks
