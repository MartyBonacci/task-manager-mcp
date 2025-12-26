"""
Tests for TaskService business logic.

These tests verify CRUD operations, filtering, search,
and statistics functionality.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


class TestTaskService:
    """Test suite for TaskService operations."""

    @pytest.mark.asyncio
    async def test_create_task(self, db_session: AsyncSession, test_user_id: str) -> None:
        """Test creating a new task."""
        task_data = TaskCreate(
            title="New Task",
            project="Test Project",
            priority=4,
            energy="deep",
            time_estimate="2hr",
            notes="Test notes",
        )

        task = await TaskService.create_task(db_session, test_user_id, task_data)

        assert task.id is not None
        assert task.title == "New Task"
        assert task.project == "Test Project"
        assert task.priority == 4
        assert task.energy == "deep"
        assert task.completed is False
        assert task.user_id == test_user_id

    @pytest.mark.asyncio
    async def test_list_tasks(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test listing tasks with filters."""
        # List all incomplete tasks
        tasks = await TaskService.list_tasks(db_session, test_user_id)
        assert len(tasks) == 2  # Only incomplete tasks

        # List all tasks including completed
        all_tasks = await TaskService.list_tasks(db_session, test_user_id, show_completed=True)
        assert len(all_tasks) == 3

        # Filter by project
        work_tasks = await TaskService.list_tasks(db_session, test_user_id, project="Work")
        assert len(work_tasks) == 1
        assert work_tasks[0].project == "Work"

        # Filter by priority
        high_priority = await TaskService.list_tasks(db_session, test_user_id, priority=5)
        assert len(high_priority) == 1
        assert high_priority[0].priority == 5

    @pytest.mark.asyncio
    async def test_get_task(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test getting a specific task by ID."""
        task = await TaskService.get_task(db_session, test_user_id, sample_task.id)

        assert task is not None
        assert task.id == sample_task.id
        assert task.title == sample_task.title

    @pytest.mark.asyncio
    async def test_get_task_not_found(
        self, db_session: AsyncSession, test_user_id: str
    ) -> None:
        """Test getting a non-existent task."""
        task = await TaskService.get_task(db_session, test_user_id, 99999)
        assert task is None

    @pytest.mark.asyncio
    async def test_update_task(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test updating a task."""
        update_data = TaskUpdate(priority=5, notes="Updated notes")

        updated_task = await TaskService.update_task(
            db_session, test_user_id, sample_task.id, update_data
        )

        assert updated_task is not None
        assert updated_task.priority == 5
        assert updated_task.notes == "Updated notes"
        assert updated_task.title == sample_task.title  # Unchanged field

    @pytest.mark.asyncio
    async def test_complete_task(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test marking a task as complete."""
        completed_task = await TaskService.complete_task(
            db_session, test_user_id, sample_task.id
        )

        assert completed_task is not None
        assert completed_task.completed is True
        assert completed_task.completed_at is not None

    @pytest.mark.asyncio
    async def test_delete_task(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test deleting a task."""
        success = await TaskService.delete_task(db_session, test_user_id, sample_task.id)
        assert success is True

        # Verify task is deleted
        deleted_task = await TaskService.get_task(db_session, test_user_id, sample_task.id)
        assert deleted_task is None

    @pytest.mark.asyncio
    async def test_search_tasks(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test searching tasks by keywords."""
        # Search in title
        results = await TaskService.search_tasks(db_session, test_user_id, "High Priority")
        assert len(results) == 1
        assert "High Priority" in results[0].title

        # Search with no matches
        no_results = await TaskService.search_tasks(db_session, test_user_id, "NonExistent")
        assert len(no_results) == 0

    @pytest.mark.asyncio
    async def test_get_task_stats(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test getting task statistics."""
        stats = await TaskService.get_task_stats(db_session, test_user_id)

        assert stats.total_tasks == 3
        assert stats.completed_tasks == 1
        assert stats.incomplete_tasks == 2
        assert stats.completion_rate == pytest.approx(33.33, rel=0.01)
        assert "Work" in stats.by_project or "Personal" in stats.by_project
        assert "5" in stats.by_priority or "3" in stats.by_priority

    @pytest.mark.asyncio
    async def test_user_isolation(
        self, db_session: AsyncSession, sample_task: Task
    ) -> None:
        """Test that users can only access their own tasks."""
        different_user = "different-user"

        # Try to get another user's task
        task = await TaskService.get_task(db_session, different_user, sample_task.id)
        assert task is None

        # Try to update another user's task
        update_data = TaskUpdate(priority=5)
        updated = await TaskService.update_task(
            db_session, different_user, sample_task.id, update_data
        )
        assert updated is None

        # Try to delete another user's task
        success = await TaskService.delete_task(db_session, different_user, sample_task.id)
        assert success is False
