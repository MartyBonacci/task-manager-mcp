"""
MCP Tool Definitions

This module defines all MCP tools available in the Task Manager MCP Server,
following the MCP specification 2025-06-18.

Each tool includes:
- name: Unique tool identifier
- description: Human-readable description
- inputSchema: JSON Schema for tool input validation
"""

from typing import Any

# MCP Tool Definitions (MCP Spec 2025-06-18 compliant)
TOOLS: list[dict[str, Any]] = [
    {
        "name": "task_create",
        "description": "Create a new task with specified details. Returns the created task with generated ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title (required, 1-500 characters)",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "project": {
                    "type": "string",
                    "description": "Project or category name (optional, max 100 characters)",
                    "maxLength": 100,
                },
                "priority": {
                    "type": "integer",
                    "description": "Priority level: 1=Someday, 2=Low, 3=Medium (default), 4=High, 5=Critical",
                    "minimum": 1,
                    "maximum": 5,
                    "default": 3,
                },
                "energy": {
                    "type": "string",
                    "description": "Energy level required: light, medium (default), or deep",
                    "enum": ["light", "medium", "deep"],
                    "default": "medium",
                },
                "time_estimate": {
                    "type": "string",
                    "description": "Estimated time to complete (e.g., '1hr', '30min', '2hr')",
                    "default": "1hr",
                },
                "notes": {
                    "type": "string",
                    "description": "Additional notes or description (optional)",
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in ISO 8601 format (optional)",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "task_list",
        "description": "List tasks with optional filters. Returns an array of tasks sorted by priority (descending) and creation date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Filter tasks by project name (optional)",
                },
                "priority": {
                    "type": "integer",
                    "description": "Filter tasks by priority level (1-5, optional)",
                    "minimum": 1,
                    "maximum": 5,
                },
                "show_completed": {
                    "type": "boolean",
                    "description": "Include completed tasks in results (default: false)",
                    "default": False,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of tasks to return (default: 100, max: 1000)",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100,
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of tasks to skip for pagination (default: 0)",
                    "minimum": 0,
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "task_get",
        "description": "Get a specific task by ID. Returns the complete task details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to retrieve (required)",
                }
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_update",
        "description": "Update an existing task. Only provided fields will be updated. Returns the updated task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to update (required)",
                },
                "title": {
                    "type": "string",
                    "description": "New task title (optional)",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "project": {"type": "string", "description": "New project name (optional)"},
                "priority": {
                    "type": "integer",
                    "description": "New priority level (1-5, optional)",
                    "minimum": 1,
                    "maximum": 5,
                },
                "energy": {
                    "type": "string",
                    "description": "New energy level (optional)",
                    "enum": ["light", "medium", "deep"],
                },
                "time_estimate": {
                    "type": "string",
                    "description": "New time estimate (optional)",
                },
                "notes": {"type": "string", "description": "New notes (optional)"},
                "due_date": {"type": "string", "description": "New due date in ISO 8601 (optional)"},
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_complete",
        "description": "Mark a task as complete. Sets completed=true and records completion timestamp. Returns the updated task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to mark complete (required)",
                }
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_delete",
        "description": "Permanently delete a task. This action cannot be undone. Returns success confirmation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to delete (required)",
                }
            },
            "required": ["task_id"],
        },
    },
    {
        "name": "task_search",
        "description": "Search tasks by keywords in title or notes. Returns matching tasks sorted by priority and creation date.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string (required, minimum 1 character)",
                    "minLength": 1,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 100, max: 1000)",
                    "minimum": 1,
                    "maximum": 1000,
                    "default": 100,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "task_stats",
        "description": "Get task statistics including total, completed, incomplete counts, completion rate, and breakdowns by project and priority.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {
                    "type": "string",
                    "description": "Filter statistics to a specific project (optional)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "task_schedule",
        "description": "Schedule a task to Google Calendar. Creates a calendar event linked to the task with specified start time and duration. Requires Google Calendar OAuth scope.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "integer",
                    "description": "ID of the task to schedule (required)",
                },
                "start_time": {
                    "type": "string",
                    "description": "Event start time in ISO 8601 format with timezone (e.g., '2025-12-30T14:00:00-08:00')",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Event duration in minutes (5-480, default: 60)",
                    "minimum": 5,
                    "maximum": 480,
                    "default": 60,
                },
            },
            "required": ["task_id", "start_time", "duration_minutes"],
        },
    },
]


def get_tool_by_name(name: str) -> dict[str, Any] | None:
    """
    Get a tool definition by name.

    Args:
        name: Tool name to look up

    Returns:
        Tool definition dict if found, None otherwise

    Example:
        tool = get_tool_by_name("task_create")
        if tool:
            print(tool["description"])
    """
    for tool in TOOLS:
        if tool["name"] == name:
            return tool
    return None


def list_tool_names() -> list[str]:
    """
    Get list of all available tool names.

    Returns:
        List of tool names

    Example:
        tools = list_tool_names()
        # ['task_create', 'task_list', ...]
    """
    return [tool["name"] for tool in TOOLS]
