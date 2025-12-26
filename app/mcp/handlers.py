"""
MCP Tool Handlers

This module implements handlers for all MCP tools, following the
MCP specification 2025-06-18 response format.

All handlers return MCPToolResponse with JSON-encoded content.
"""

import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.mcp import (
    MCPContent,
    MCPToolResponse,
    TaskCompleteInput,
    TaskCreateInput,
    TaskDeleteInput,
    TaskGetInput,
    TaskListInput,
    TaskSearchInput,
    TaskStatsInput,
    TaskUpdateInput,
)
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task_service import TaskService


class MCPToolHandlers:
    """
    MCP tool handler implementations.

    All methods are async and return MCPToolResponse with JSON content.
    """

    @staticmethod
    async def task_create(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_create tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Created task as JSON content

        Example Input:
            {
                "title": "Research MCP spec",
                "priority": 4,
                "energy": "deep"
            }

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"id\": 1, \"title\": \"Research MCP spec\", ...}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskCreateInput(**params)

            # Create task
            task_data = TaskCreate(**input_data.model_dump())
            task = await TaskService.create_task(db, user_id, task_data)

            # Return MCP response
            return MCPToolResponse(
                content=[MCPContent(type="text", text=task.model_dump_json())]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_CREATE_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_list(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_list tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Array of tasks as JSON content

        Example Input:
            {
                "project": "Deep Dive Coding",
                "priority": 4,
                "limit": 50
            }

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "[{\"id\": 1, ...}, {\"id\": 2, ...}]"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskListInput(**params)

            # List tasks
            tasks = await TaskService.list_tasks(
                db,
                user_id,
                project=input_data.project,
                priority=input_data.priority,
                show_completed=input_data.show_completed,
                limit=input_data.limit,
                offset=input_data.offset,
            )

            # Convert to JSON array
            tasks_json = json.dumps([task.model_dump() for task in tasks])

            # Return MCP response
            return MCPToolResponse(content=[MCPContent(type="text", text=tasks_json)])
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_LIST_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_get(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_get tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Task details as JSON content or error

        Example Input:
            {"task_id": 1}

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"id\": 1, \"title\": \"Task\", ...}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskGetInput(**params)

            # Get task
            task = await TaskService.get_task(db, user_id, input_data.task_id)

            if not task:
                error_data = {"error": "Task not found", "code": "NOT_FOUND"}
                return MCPToolResponse(
                    content=[MCPContent(type="text", text=json.dumps(error_data))]
                )

            # Return MCP response
            return MCPToolResponse(
                content=[MCPContent(type="text", text=task.model_dump_json())]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_GET_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_update(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_update tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Updated task as JSON content or error

        Example Input:
            {
                "task_id": 1,
                "priority": 5,
                "notes": "Updated notes"
            }

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"id\": 1, \"priority\": 5, ...}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskUpdateInput(**params)

            # Extract task_id
            task_id = input_data.task_id

            # Create update data (exclude task_id)
            update_dict = input_data.model_dump(exclude={"task_id"}, exclude_unset=True)
            task_data = TaskUpdate(**update_dict)

            # Update task
            task = await TaskService.update_task(db, user_id, task_id, task_data)

            if not task:
                error_data = {"error": "Task not found", "code": "NOT_FOUND"}
                return MCPToolResponse(
                    content=[MCPContent(type="text", text=json.dumps(error_data))]
                )

            # Return MCP response
            return MCPToolResponse(
                content=[MCPContent(type="text", text=task.model_dump_json())]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_UPDATE_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_complete(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_complete tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Completed task as JSON content or error

        Example Input:
            {"task_id": 1}

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"id\": 1, \"completed\": true, \"completed_at\": \"2025-12-25T...\", ...}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskCompleteInput(**params)

            # Complete task
            task = await TaskService.complete_task(db, user_id, input_data.task_id)

            if not task:
                error_data = {"error": "Task not found", "code": "NOT_FOUND"}
                return MCPToolResponse(
                    content=[MCPContent(type="text", text=json.dumps(error_data))]
                )

            # Return MCP response
            return MCPToolResponse(
                content=[MCPContent(type="text", text=task.model_dump_json())]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_COMPLETE_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_delete(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_delete tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Success confirmation or error

        Example Input:
            {"task_id": 1}

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"success\": true, \"message\": \"Task deleted successfully\"}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskDeleteInput(**params)

            # Delete task
            success = await TaskService.delete_task(db, user_id, input_data.task_id)

            if not success:
                error_data = {"error": "Task not found", "code": "NOT_FOUND"}
                return MCPToolResponse(
                    content=[MCPContent(type="text", text=json.dumps(error_data))]
                )

            # Return success response
            success_data = {"success": True, "message": "Task deleted successfully"}
            return MCPToolResponse(
                content=[MCPContent(type="text", text=json.dumps(success_data))]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_DELETE_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_search(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_search tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Array of matching tasks as JSON content

        Example Input:
            {
                "query": "MCP specification",
                "limit": 50
            }

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "[{\"id\": 1, \"title\": \"Research MCP specification\", ...}]"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskSearchInput(**params)

            # Search tasks
            tasks = await TaskService.search_tasks(
                db, user_id, input_data.query, limit=input_data.limit
            )

            # Convert to JSON array
            tasks_json = json.dumps([task.model_dump() for task in tasks])

            # Return MCP response
            return MCPToolResponse(content=[MCPContent(type="text", text=tasks_json)])
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_SEARCH_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])

    @staticmethod
    async def task_stats(
        db: AsyncSession, user_id: str, params: dict[str, Any]
    ) -> MCPToolResponse:
        """
        Handle task_stats tool call.

        Args:
            db: Database session
            user_id: Authenticated user ID
            params: Tool input parameters

        Returns:
            MCPToolResponse: Task statistics as JSON content

        Example Input:
            {"project": "Deep Dive Coding"}

        Example Output:
            {
                "content": [{
                    "type": "text",
                    "text": "{\"total_tasks\": 25, \"completed_tasks\": 10, ...}"
                }]
            }
        """
        try:
            # Validate input
            input_data = TaskStatsInput(**params)

            # Get statistics
            stats = await TaskService.get_task_stats(db, user_id, project=input_data.project)

            # Return MCP response
            return MCPToolResponse(
                content=[MCPContent(type="text", text=stats.model_dump_json())]
            )
        except Exception as e:
            # Return error response
            error_data = {"error": str(e), "code": "TASK_STATS_FAILED"}
            return MCPToolResponse(content=[MCPContent(type="text", text=json.dumps(error_data))])


# Tool name to handler mapping
TOOL_HANDLERS = {
    "task_create": MCPToolHandlers.task_create,
    "task_list": MCPToolHandlers.task_list,
    "task_get": MCPToolHandlers.task_get,
    "task_update": MCPToolHandlers.task_update,
    "task_complete": MCPToolHandlers.task_complete,
    "task_delete": MCPToolHandlers.task_delete,
    "task_search": MCPToolHandlers.task_search,
    "task_stats": MCPToolHandlers.task_stats,
}
