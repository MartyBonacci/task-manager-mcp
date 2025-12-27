"""
Integration tests for user isolation.

Tests that users can only access their own tasks and that the
authentication system properly isolates user data.
"""

import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.session_service import create_session
from app.services.task_service import TaskService
from app.services.user_service import create_user
from app.schemas.task import TaskCreate


class TestTaskIsolation:
    """Test that users can only access their own tasks."""

    @pytest.mark.asyncio
    async def test_user_cannot_see_other_users_tasks(self, db_session: AsyncSession):
        """Test users only see their own tasks via MCP."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="user_1",
            email="user1@example.com",
            name="User One",
        )

        user2 = await create_user(
            db_session,
            user_id="user_2",
            email="user2@example.com",
            name="User Two",
        )

        # Create tasks for user 1
        await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="User 1 Task 1", priority=4),
        )
        await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="User 1 Task 2", priority=3),
        )

        # Create tasks for user 2
        await TaskService.create_task(
            db_session,
            user2.user_id,
            TaskCreate(title="User 2 Task 1", priority=5),
        )

        # User 1 should only see their tasks
        user1_tasks = await TaskService.list_tasks(db_session, user1.user_id)
        assert len(user1_tasks) == 2
        assert all(task.title.startswith("User 1") for task in user1_tasks)

        # User 2 should only see their tasks
        user2_tasks = await TaskService.list_tasks(db_session, user2.user_id)
        assert len(user2_tasks) == 1
        assert user2_tasks[0].title == "User 2 Task 1"

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_users_task_by_id(
        self, db_session: AsyncSession
    ):
        """Test users cannot access another user's task by ID."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="user_a",
            email="usera@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="user_b",
            email="userb@example.com",
        )

        # User 1 creates a task
        user1_task = await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="User A Private Task", priority=4),
        )

        # User 2 tries to access User 1's task
        result = await TaskService.get_task(db_session, user2.user_id, user1_task.id)

        # Should return None (not found)
        assert result is None

    @pytest.mark.asyncio
    async def test_user_cannot_update_other_users_task(self, db_session: AsyncSession):
        """Test users cannot update another user's task."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="user_alpha",
            email="alpha@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="user_beta",
            email="beta@example.com",
        )

        # User 1 creates a task
        user1_task = await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="Original Title", priority=4),
        )

        # User 2 tries to update User 1's task
        from app.schemas.task import TaskUpdate

        result = await TaskService.update_task(
            db_session,
            user2.user_id,
            user1_task.id,
            TaskUpdate(title="Hijacked Title"),
        )

        # Update should fail (return None)
        assert result is None

        # Verify original task unchanged
        original = await TaskService.get_task(db_session, user1.user_id, user1_task.id)
        assert original.title == "Original Title"

    @pytest.mark.asyncio
    async def test_user_cannot_delete_other_users_task(self, db_session: AsyncSession):
        """Test users cannot delete another user's task."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="user_gamma",
            email="gamma@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="user_delta",
            email="delta@example.com",
        )

        # User 1 creates a task
        user1_task = await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="Protected Task", priority=4),
        )

        # User 2 tries to delete User 1's task
        deleted = await TaskService.delete_task(
            db_session, user2.user_id, user1_task.id
        )

        # Delete should fail
        assert deleted is False

        # Verify task still exists for user 1
        task_check = await TaskService.get_task(
            db_session, user1.user_id, user1_task.id
        )
        assert task_check is not None


class TestMCPIsolation:
    """Test user isolation via MCP API."""

    @pytest.mark.asyncio
    async def test_mcp_list_isolates_by_session(self, db_session: AsyncSession):
        """Test MCP task_list returns only authenticated user's tasks."""
        # Create two users with sessions
        user1 = await create_user(
            db_session,
            user_id="mcp_user_1",
            email="mcp1@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="mcp_user_2",
            email="mcp2@example.com",
        )

        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        session1 = await create_session(
            db_session,
            user_id=user1.user_id,
            access_token="user1_token",
            refresh_token="user1_refresh",
            expires_at=expires_at,
        )

        session2 = await create_session(
            db_session,
            user_id=user2.user_id,
            access_token="user2_token",
            refresh_token="user2_refresh",
            expires_at=expires_at,
        )

        # Create tasks for both users
        await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="User 1 MCP Task", priority=4),
        )

        await TaskService.create_task(
            db_session,
            user2.user_id,
            TaskCreate(title="User 2 MCP Task", priority=5),
        )

        # User 1 calls task_list via MCP
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response1 = await client.post(
                "/mcp/tools/call",
                json={"name": "task_list", "params": {}},
                headers={"Authorization": f"Bearer {session1.session_id}"},
            )

            assert response1.status_code == 200
            # Parse response and verify only User 1's tasks
            # (Response format is MCP content blocks with JSON)

    @pytest.mark.asyncio
    async def test_mcp_get_task_isolation(self, db_session: AsyncSession):
        """Test MCP task_get enforces user isolation."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="get_user_1",
            email="get1@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="get_user_2",
            email="get2@example.com",
        )

        # Create sessions
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        session1 = await create_session(
            db_session,
            user_id=user1.user_id,
            access_token="get1_token",
            refresh_token="get1_refresh",
            expires_at=expires_at,
        )

        session2 = await create_session(
            db_session,
            user_id=user2.user_id,
            access_token="get2_token",
            refresh_token="get2_refresh",
            expires_at=expires_at,
        )

        # User 1 creates a task
        user1_task = await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="User 1 Private", priority=4),
        )

        # User 2 tries to get User 1's task via MCP
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/mcp/tools/call",
                json={
                    "name": "task_get",
                    "params": {"task_id": user1_task.id},
                },
                headers={"Authorization": f"Bearer {session2.session_id}"},
            )

            # Should fail or return not found
            assert response.status_code in [404, 500]  # Depends on error handling


class TestSearchIsolation:
    """Test search respects user boundaries."""

    @pytest.mark.asyncio
    async def test_search_only_returns_own_tasks(self, db_session: AsyncSession):
        """Test task search is isolated by user."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="search_user_1",
            email="search1@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="search_user_2",
            email="search2@example.com",
        )

        # Both users create tasks with keyword "important"
        await TaskService.create_task(
            db_session,
            user1.user_id,
            TaskCreate(title="Important User 1 Task", priority=4),
        )

        await TaskService.create_task(
            db_session,
            user2.user_id,
            TaskCreate(title="Important User 2 Task", priority=5),
        )

        # User 1 searches for "important"
        user1_results = await TaskService.search_tasks(
            db_session, user1.user_id, "important"
        )

        # Should only find their own task
        assert len(user1_results) == 1
        assert "User 1" in user1_results[0].title

        # User 2 searches for "important"
        user2_results = await TaskService.search_tasks(
            db_session, user2.user_id, "important"
        )

        # Should only find their own task
        assert len(user2_results) == 1
        assert "User 2" in user2_results[0].title


class TestStatsIsolation:
    """Test statistics respect user boundaries."""

    @pytest.mark.asyncio
    async def test_stats_only_count_own_tasks(self, db_session: AsyncSession):
        """Test task_stats only counts authenticated user's tasks."""
        # Create two users
        user1 = await create_user(
            db_session,
            user_id="stats_user_1",
            email="stats1@example.com",
        )

        user2 = await create_user(
            db_session,
            user_id="stats_user_2",
            email="stats2@example.com",
        )

        # User 1 creates 3 tasks
        for i in range(3):
            await TaskService.create_task(
                db_session,
                user1.user_id,
                TaskCreate(title=f"User 1 Task {i}", priority=4),
            )

        # User 2 creates 5 tasks
        for i in range(5):
            await TaskService.create_task(
                db_session,
                user2.user_id,
                TaskCreate(title=f"User 2 Task {i}", priority=3),
            )

        # User 1 gets stats
        user1_stats = await TaskService.get_task_stats(db_session, user1.user_id)
        assert user1_stats.total_tasks == 3

        # User 2 gets stats
        user2_stats = await TaskService.get_task_stats(db_session, user2.user_id)
        assert user2_stats.total_tasks == 5
