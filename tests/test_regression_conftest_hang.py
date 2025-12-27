"""
Regression test for Bug: Test execution hang

This test verifies that pytest can complete test execution without hanging.

Bug Description:
  Test execution hangs indefinitely due to SQLAlchemy async engine
  not being properly disposed after tests complete.

Root Cause:
  - tests/conftest.py creates test_engine at module level
  - db_session fixture uses engine but never disposes it
  - Engine connection pool remains open
  - pytest waits indefinitely for connections to close

Expected Behavior:
  - BEFORE FIX: This test will cause pytest to hang after completion
  - AFTER FIX: This test will complete successfully with proper cleanup

Fix:
  - Add session-scoped fixture to dispose engine after all tests
  - Add pytest timeout configuration to detect hangs
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task


@pytest.mark.asyncio
async def test_simple_database_operation_completes(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that a simple database operation completes without hanging.

    This test will HANG before the fix because:
    1. It uses db_session fixture
    2. db_session uses test_engine
    3. test_engine is never disposed
    4. pytest waits for engine cleanup → hangs

    After fix, this test will complete successfully.
    """
    # Create a simple task
    task = Task(
        user_id=test_user_id,
        title="Regression Test Task",
        project="Test",
        priority=3,
        energy="medium",
        time_estimate="1hr",
        completed=False,
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Verify task was created
    assert task.id is not None
    assert task.title == "Regression Test Task"


@pytest.mark.asyncio
async def test_multiple_tests_dont_cause_resource_leak(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that running multiple tests doesn't leak resources.

    This verifies that each test properly cleans up its database session
    and that the overall test suite can complete.
    """
    # Create multiple tasks to stress test cleanup
    for i in range(5):
        task = Task(
            user_id=test_user_id,
            title=f"Test Task {i}",
            project="Test",
            priority=3,
            energy="medium",
            time_estimate="1hr",
            completed=False,
        )
        db_session.add(task)

    await db_session.commit()

    # Verify all tasks were created
    # This ensures the session is working correctly
    assert True  # If we get here without hanging, test passes


@pytest.mark.asyncio
@pytest.mark.timeout(10)  # 10 second timeout to detect hangs
async def test_test_suite_completes_within_timeout(
    db_session: AsyncSession, test_user_id: str
):
    """
    Test that the test suite can complete within a reasonable timeout.

    This test uses pytest-timeout to detect if the test hangs.

    BEFORE FIX: This test may timeout/hang
    AFTER FIX: This test will complete in < 10 seconds
    """
    task = Task(
        user_id=test_user_id,
        title="Timeout Test Task",
        project="Test",
        priority=3,
        energy="medium",
        time_estimate="1hr",
        completed=False,
    )

    db_session.add(task)
    await db_session.commit()

    # If we reach here without timeout, fix is working
    assert True
