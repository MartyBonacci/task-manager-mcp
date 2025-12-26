"""
Tests for MCP tool handlers.

These tests verify that all MCP tools return properly formatted
responses according to the MCP specification 2025-06-18.
"""

import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task
from app.mcp.handlers import MCPToolHandlers


class TestMCPHandlers:
    """Test suite for MCP tool handlers."""

    @pytest.mark.asyncio
    async def test_task_create_handler(
        self, db_session: AsyncSession, test_user_id: str
    ) -> None:
        """Test task_create MCP tool handler."""
        params = {
            "title": "Test Task",
            "project": "Test Project",
            "priority": 4,
            "energy": "deep",
        }

        response = await MCPToolHandlers.task_create(db_session, test_user_id, params)

        # Verify response structure
        assert len(response.content) == 1
        assert response.content[0].type == "text"

        # Parse response data
        data = json.loads(response.content[0].text)
        assert "id" in data
        assert data["title"] == "Test Task"
        assert data["priority"] == 4

    @pytest.mark.asyncio
    async def test_task_list_handler(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test task_list MCP tool handler."""
        params = {}

        response = await MCPToolHandlers.task_list(db_session, test_user_id, params)

        # Verify response structure
        assert len(response.content) == 1
        assert response.content[0].type == "text"

        # Parse response data
        data = json.loads(response.content[0].text)
        assert isinstance(data, list)
        assert len(data) == 2  # Only incomplete tasks by default

    @pytest.mark.asyncio
    async def test_task_get_handler(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test task_get MCP tool handler."""
        params = {"task_id": sample_task.id}

        response = await MCPToolHandlers.task_get(db_session, test_user_id, params)

        # Verify response structure
        assert len(response.content) == 1

        # Parse response data
        data = json.loads(response.content[0].text)
        assert data["id"] == sample_task.id
        assert data["title"] == sample_task.title

    @pytest.mark.asyncio
    async def test_task_get_not_found(
        self, db_session: AsyncSession, test_user_id: str
    ) -> None:
        """Test task_get with non-existent task."""
        params = {"task_id": 99999}

        response = await MCPToolHandlers.task_get(db_session, test_user_id, params)

        # Parse error response
        data = json.loads(response.content[0].text)
        assert "error" in data
        assert data["code"] == "NOT_FOUND"

    @pytest.mark.asyncio
    async def test_task_update_handler(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test task_update MCP tool handler."""
        params = {"task_id": sample_task.id, "priority": 5, "notes": "Updated"}

        response = await MCPToolHandlers.task_update(db_session, test_user_id, params)

        # Parse response data
        data = json.loads(response.content[0].text)
        assert data["priority"] == 5
        assert data["notes"] == "Updated"

    @pytest.mark.asyncio
    async def test_task_complete_handler(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test task_complete MCP tool handler."""
        params = {"task_id": sample_task.id}

        response = await MCPToolHandlers.task_complete(db_session, test_user_id, params)

        # Parse response data
        data = json.loads(response.content[0].text)
        assert data["completed"] is True
        assert data["completed_at"] is not None

    @pytest.mark.asyncio
    async def test_task_delete_handler(
        self, db_session: AsyncSession, test_user_id: str, sample_task: Task
    ) -> None:
        """Test task_delete MCP tool handler."""
        params = {"task_id": sample_task.id}

        response = await MCPToolHandlers.task_delete(db_session, test_user_id, params)

        # Parse response data
        data = json.loads(response.content[0].text)
        assert data["success"] is True
        assert "deleted successfully" in data["message"]

    @pytest.mark.asyncio
    async def test_task_search_handler(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test task_search MCP tool handler."""
        params = {"query": "Priority", "limit": 10}

        response = await MCPToolHandlers.task_search(db_session, test_user_id, params)

        # Parse response data
        data = json.loads(response.content[0].text)
        assert isinstance(data, list)
        assert len(data) > 0

    @pytest.mark.asyncio
    async def test_task_stats_handler(
        self, db_session: AsyncSession, test_user_id: str, multiple_tasks: list[Task]
    ) -> None:
        """Test task_stats MCP tool handler."""
        params = {}

        response = await MCPToolHandlers.task_stats(db_session, test_user_id, params)

        # Parse response data
        data = json.loads(response.content[0].text)
        assert "total_tasks" in data
        assert "completed_tasks" in data
        assert "completion_rate" in data
        assert data["total_tasks"] == 3
        assert data["completed_tasks"] == 1

    @pytest.mark.asyncio
    async def test_invalid_params(
        self, db_session: AsyncSession, test_user_id: str
    ) -> None:
        """Test handler with invalid parameters."""
        params = {"title": ""}  # Invalid: title too short

        response = await MCPToolHandlers.task_create(db_session, test_user_id, params)

        # Parse error response
        data = json.loads(response.content[0].text)
        assert "error" in data
