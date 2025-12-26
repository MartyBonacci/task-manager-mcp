"""
Task Service - Business Logic Layer

This module implements all business logic for task management operations,
including CRUD operations, search, and statistics.

All methods enforce user isolation by filtering queries with user_id.
"""

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskStats, TaskUpdate


class TaskService:
    """
    Service class for task management operations.

    All methods are async and require a database session.
    User isolation is enforced in all queries.
    """

    @staticmethod
    async def create_task(
        db: AsyncSession, user_id: str, task_data: TaskCreate
    ) -> TaskResponse:
        """
        Create a new task.

        Args:
            db: Database session
            user_id: ID of the user creating the task
            task_data: Task creation data

        Returns:
            TaskResponse: Created task with generated ID and timestamps

        Example:
            task = await TaskService.create_task(
                db,
                "dev-user",
                TaskCreate(title="New task", priority=4)
            )
        """
        # Create new task instance
        task = Task(
            user_id=user_id,
            title=task_data.title,
            project=task_data.project,
            priority=task_data.priority,
            energy=task_data.energy,
            time_estimate=task_data.time_estimate,
            notes=task_data.notes,
            due_date=task_data.due_date,
            completed=False,
        )

        # Add to session and commit
        db.add(task)
        await db.commit()
        await db.refresh(task)

        return TaskResponse.model_validate(task)

    @staticmethod
    async def list_tasks(
        db: AsyncSession,
        user_id: str,
        project: str | None = None,
        priority: int | None = None,
        show_completed: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[TaskResponse]:
        """
        List tasks with optional filters.

        Args:
            db: Database session
            user_id: ID of the user requesting tasks
            project: Optional project filter
            priority: Optional priority filter
            show_completed: Include completed tasks (default: False)
            limit: Maximum number of tasks to return (default: 100, max: 1000)
            offset: Number of tasks to skip (default: 0)

        Returns:
            list[TaskResponse]: List of matching tasks

        Example:
            tasks = await TaskService.list_tasks(
                db,
                "dev-user",
                project="Deep Dive Coding",
                priority=4,
                limit=50
            )
        """
        # Build query with user isolation
        query = select(Task).filter(Task.user_id == user_id)

        # Apply filters
        if project:
            query = query.filter(Task.project == project)

        if priority:
            query = query.filter(Task.priority == priority)

        if not show_completed:
            query = query.filter(Task.completed == False)  # noqa: E712

        # Apply sorting (priority DESC, created_at ASC)
        query = query.order_by(Task.priority.desc(), Task.created_at)

        # Apply pagination
        query = query.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()

        return [TaskResponse.model_validate(task) for task in tasks]

    @staticmethod
    async def get_task(db: AsyncSession, user_id: str, task_id: int) -> TaskResponse | None:
        """
        Get a specific task by ID.

        Args:
            db: Database session
            user_id: ID of the user requesting the task
            task_id: ID of the task to retrieve

        Returns:
            Optional[TaskResponse]: Task if found and owned by user, None otherwise

        Raises:
            ValueError: If task not found or not owned by user

        Example:
            task = await TaskService.get_task(db, "dev-user", 1)
            if not task:
                raise ValueError("Task not found")
        """
        query = select(Task).filter(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        return TaskResponse.model_validate(task)

    @staticmethod
    async def update_task(
        db: AsyncSession, user_id: str, task_id: int, task_data: TaskUpdate
    ) -> TaskResponse | None:
        """
        Update an existing task.

        Only provided fields will be updated. User ownership is verified.

        Args:
            db: Database session
            user_id: ID of the user updating the task
            task_id: ID of the task to update
            task_data: Task update data (partial)

        Returns:
            Optional[TaskResponse]: Updated task if found, None otherwise

        Example:
            updated_task = await TaskService.update_task(
                db,
                "dev-user",
                1,
                TaskUpdate(priority=5, notes="Updated")
            )
        """
        # Get task with user verification
        query = select(Task).filter(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        # Update provided fields
        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        # Update timestamp
        task.updated_at = datetime.now(UTC).isoformat()

        await db.commit()
        await db.refresh(task)

        return TaskResponse.model_validate(task)

    @staticmethod
    async def complete_task(
        db: AsyncSession, user_id: str, task_id: int
    ) -> TaskResponse | None:
        """
        Mark a task as complete.

        Sets completed=True and completed_at to current timestamp.

        Args:
            db: Database session
            user_id: ID of the user completing the task
            task_id: ID of the task to complete

        Returns:
            Optional[TaskResponse]: Completed task if found, None otherwise

        Example:
            completed_task = await TaskService.complete_task(db, "dev-user", 1)
        """
        # Get task with user verification
        query = select(Task).filter(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return None

        # Mark as complete
        task.completed = True
        task.completed_at = datetime.now(UTC).isoformat()
        task.updated_at = datetime.now(UTC).isoformat()

        await db.commit()
        await db.refresh(task)

        return TaskResponse.model_validate(task)

    @staticmethod
    async def delete_task(db: AsyncSession, user_id: str, task_id: int) -> bool:
        """
        Delete a task permanently.

        Args:
            db: Database session
            user_id: ID of the user deleting the task
            task_id: ID of the task to delete

        Returns:
            bool: True if task was deleted, False if not found

        Example:
            success = await TaskService.delete_task(db, "dev-user", 1)
            if not success:
                raise ValueError("Task not found")
        """
        # Get task with user verification
        query = select(Task).filter(Task.id == task_id, Task.user_id == user_id)
        result = await db.execute(query)
        task = result.scalar_one_or_none()

        if not task:
            return False

        await db.delete(task)
        await db.commit()

        return True

    @staticmethod
    async def search_tasks(
        db: AsyncSession, user_id: str, query: str, limit: int = 100
    ) -> list[TaskResponse]:
        """
        Search tasks by keywords in title or notes.

        Args:
            db: Database session
            user_id: ID of the user searching
            query: Search query string
            limit: Maximum number of results (default: 100)

        Returns:
            list[TaskResponse]: List of matching tasks

        Example:
            tasks = await TaskService.search_tasks(db, "dev-user", "MCP specification")
        """
        # Build search query with user isolation
        search_pattern = f"%{query}%"
        search_query = (
            select(Task)
            .filter(
                Task.user_id == user_id,
                or_(Task.title.ilike(search_pattern), Task.notes.ilike(search_pattern)),
            )
            .order_by(Task.priority.desc(), Task.created_at)
            .limit(limit)
        )

        # Execute query
        result = await db.execute(search_query)
        tasks = result.scalars().all()

        return [TaskResponse.model_validate(task) for task in tasks]

    @staticmethod
    async def get_task_stats(
        db: AsyncSession, user_id: str, project: str | None = None
    ) -> TaskStats:
        """
        Get task statistics and summary.

        Args:
            db: Database session
            user_id: ID of the user requesting stats
            project: Optional project filter

        Returns:
            TaskStats: Task statistics including counts and completion rate

        Example:
            stats = await TaskService.get_task_stats(db, "dev-user")
            print(f"Completion rate: {stats.completion_rate}%")
        """
        # Base query with user isolation
        base_query = select(Task).filter(Task.user_id == user_id)

        if project:
            base_query = base_query.filter(Task.project == project)

        # Total task count
        total_result = await db.execute(select(func.count()).select_from(base_query.subquery()))
        total_tasks = total_result.scalar() or 0

        # Completed task count
        completed_query = base_query.filter(Task.completed == True)  # noqa: E712
        completed_result = await db.execute(
            select(func.count()).select_from(completed_query.subquery())
        )
        completed_tasks = completed_result.scalar() or 0

        # Calculate stats
        incomplete_tasks = total_tasks - completed_tasks
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

        # Count by project
        by_project_query = (
            select(Task.project, func.count(Task.id))
            .filter(Task.user_id == user_id, Task.completed == False)  # noqa: E712
            .group_by(Task.project)
        )
        by_project_result = await db.execute(by_project_query)
        by_project = {
            project or "None": count for project, count in by_project_result.all()
        }

        # Count by priority
        by_priority_query = (
            select(Task.priority, func.count(Task.id))
            .filter(Task.user_id == user_id, Task.completed == False)  # noqa: E712
            .group_by(Task.priority)
        )
        by_priority_result = await db.execute(by_priority_query)
        by_priority = {str(priority): count for priority, count in by_priority_result.all()}

        return TaskStats(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            incomplete_tasks=incomplete_tasks,
            completion_rate=round(completion_rate, 2),
            by_project=by_project,
            by_priority=by_priority,
        )
