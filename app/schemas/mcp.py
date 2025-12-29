"""
Pydantic schemas for MCP protocol tool inputs and outputs.

These schemas define the structure and validation for MCP tool calls,
ensuring compliance with the MCP specification 2025-06-18.
"""

from typing import Literal

from pydantic import BaseModel, Field


class MCPToolInput(BaseModel):
    """Base schema for MCP tool inputs."""



class TaskCreateInput(MCPToolInput):
    """
    Input schema for task_create tool.

    MCP Tool: task_create
    Description: Create a new task with specified details

    Example:
        {
            "title": "Research MCP specification",
            "project": "Deep Dive Coding",
            "priority": 4,
            "energy": "deep",
            "time_estimate": "2hr"
        }
    """

    title: str = Field(..., description="Task title (required)")
    project: str | None = Field(None, description="Project/category name")
    priority: int = Field(default=3, ge=1, le=5, description="Priority (1-5)")
    energy: Literal["light", "medium", "deep"] = Field(
        default="medium", description="Energy level"
    )
    time_estimate: str = Field(default="1hr", description="Time estimate")
    notes: str | None = Field(None, description="Additional notes")
    due_date: str | None = Field(None, description="Due date (ISO 8601)")


class TaskListInput(MCPToolInput):
    """
    Input schema for task_list tool.

    MCP Tool: task_list
    Description: List tasks with optional filters

    Example:
        {
            "project": "Deep Dive Coding",
            "priority": 4,
            "show_completed": false,
            "limit": 50
        }
    """

    project: str | None = Field(None, description="Filter by project")
    priority: int | None = Field(None, ge=1, le=5, description="Filter by priority")
    show_completed: bool = Field(default=False, description="Include completed tasks")
    limit: int = Field(default=100, ge=1, le=1000, description="Max tasks to return")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class TaskGetInput(MCPToolInput):
    """
    Input schema for task_get tool.

    MCP Tool: task_get
    Description: Get a specific task by ID

    Example:
        {
            "task_id": 1
        }
    """

    task_id: int = Field(..., description="Task ID to retrieve")


class TaskUpdateInput(MCPToolInput):
    """
    Input schema for task_update tool.

    MCP Tool: task_update
    Description: Update an existing task

    Example:
        {
            "task_id": 1,
            "priority": 5,
            "notes": "Updated notes"
        }
    """

    task_id: int = Field(..., description="Task ID to update")
    title: str | None = Field(None, description="New task title")
    project: str | None = Field(None, description="New project")
    priority: int | None = Field(None, ge=1, le=5, description="New priority")
    energy: Literal["light", "medium", "deep"] | None = Field(None, description="New energy")
    time_estimate: str | None = Field(None, description="New time estimate")
    notes: str | None = Field(None, description="New notes")
    due_date: str | None = Field(None, description="New due date")


class TaskCompleteInput(MCPToolInput):
    """
    Input schema for task_complete tool.

    MCP Tool: task_complete
    Description: Mark a task as complete

    Example:
        {
            "task_id": 1
        }
    """

    task_id: int = Field(..., description="Task ID to mark complete")


class TaskDeleteInput(MCPToolInput):
    """
    Input schema for task_delete tool.

    MCP Tool: task_delete
    Description: Delete a task permanently

    Example:
        {
            "task_id": 1
        }
    """

    task_id: int = Field(..., description="Task ID to delete")


class TaskSearchInput(MCPToolInput):
    """
    Input schema for task_search tool.

    MCP Tool: task_search
    Description: Search tasks by keywords in title or notes

    Example:
        {
            "query": "MCP specification",
            "limit": 50
        }
    """

    query: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(default=100, ge=1, le=1000, description="Max results")


class TaskStatsInput(MCPToolInput):
    """
    Input schema for task_stats tool.

    MCP Tool: task_stats
    Description: Get task statistics and summary

    Example:
        {
            "project": "Deep Dive Coding"
        }
    """

    project: str | None = Field(None, description="Filter stats by project")


class TaskScheduleInput(MCPToolInput):
    """
    Input schema for task_schedule tool.

    MCP Tool: task_schedule
    Description: Schedule a task to Google Calendar

    Example:
        {
            "task_id": 1,
            "start_time": "2025-12-30T14:00:00-08:00",
            "duration_minutes": 60
        }
    """

    task_id: int = Field(..., description="ID of task to schedule")
    start_time: str = Field(..., description="Event start time (ISO 8601 with timezone)")
    duration_minutes: int = Field(
        default=60, ge=5, le=480, description="Duration in minutes (5-480)"
    )


class MCPContent(BaseModel):
    """
    MCP content block schema.

    According to MCP spec 2025-06-18, tool responses must return
    content blocks in this format.
    """

    type: Literal["text"] = "text"
    text: str = Field(..., description="JSON-encoded response data")


class MCPToolResponse(BaseModel):
    """
    MCP tool call response schema.

    All MCP tool handlers must return responses in this format
    per MCP specification 2025-06-18.

    Example:
        {
            "content": [
                {
                    "type": "text",
                    "text": "{\"id\": 1, \"title\": \"Task\", ...}"
                }
            ]
        }
    """

    content: list[MCPContent] = Field(..., description="Response content blocks")


class MCPErrorResponse(BaseModel):
    """
    MCP error response schema.

    Used when tool execution fails or validation errors occur.

    Example:
        {
            "content": [
                {
                    "type": "text",
                    "text": "{\"error\": \"Task not found\", \"code\": \"NOT_FOUND\"}"
                }
            ]
        }
    """

    content: list[MCPContent]
