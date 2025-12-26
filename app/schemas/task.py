"""
Pydantic schemas for Task model validation.

These schemas define the structure and validation rules for task data
in API requests and responses, ensuring type safety and data integrity.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskBase(BaseModel):
    """
    Base schema for Task with common fields.

    This is the parent schema that contains fields shared across
    create, update, and response schemas.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Task title")
    project: str | None = Field(None, max_length=100, description="Project/category name")
    priority: int = Field(
        default=3, ge=1, le=5, description="Priority level (1=Someday, 2=Low, 3=Medium, 4=High, 5=Critical)"
    )
    energy: Literal["light", "medium", "deep"] = Field(
        default="medium", description="Energy level required"
    )
    time_estimate: str = Field(
        default="1hr", max_length=50, description='Estimated time (e.g., "1hr", "30min")'
    )
    notes: str | None = Field(None, description="Additional task notes/description")
    due_date: str | None = Field(None, description="Due date in ISO 8601 format")

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Ensure priority is within valid range (1-5)."""
        if v < 1 or v > 5:
            raise ValueError("Priority must be between 1 and 5")
        return v

    @field_validator("energy")
    @classmethod
    def validate_energy(cls, v: str) -> str:
        """Ensure energy level is valid."""
        if v not in ("light", "medium", "deep"):
            raise ValueError("Energy must be 'light', 'medium', or 'deep'")
        return v


class TaskCreate(TaskBase):
    """
    Schema for creating a new task.

    All fields from TaskBase are available. The user_id is automatically
    set from the authenticated user context.

    Example:
        {
            "title": "Research MCP specification",
            "project": "Deep Dive Coding",
            "priority": 4,
            "energy": "deep",
            "time_estimate": "2hr",
            "notes": "Focus on tool registration"
        }
    """



class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.

    All fields are optional, allowing partial updates.
    Only provided fields will be updated.

    Example:
        {
            "priority": 5,
            "notes": "Updated notes"
        }
    """

    title: str | None = Field(None, min_length=1, max_length=500)
    project: str | None = Field(None, max_length=100)
    priority: int | None = Field(None, ge=1, le=5)
    energy: Literal["light", "medium", "deep"] | None = None
    time_estimate: str | None = Field(None, max_length=50)
    notes: str | None = None
    due_date: str | None = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int | None) -> int | None:
        """Ensure priority is within valid range if provided."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Priority must be between 1 and 5")
        return v

    @field_validator("energy")
    @classmethod
    def validate_energy(cls, v: str | None) -> str | None:
        """Ensure energy level is valid if provided."""
        if v is not None and v not in ("light", "medium", "deep"):
            raise ValueError("Energy must be 'light', 'medium', or 'deep'")
        return v


class TaskResponse(TaskBase):
    """
    Schema for task responses.

    Includes all TaskBase fields plus system-generated fields
    (id, user_id, completed status, timestamps).

    This schema is used for all task retrieval operations.

    Example:
        {
            "id": 1,
            "user_id": "dev-user",
            "title": "Research MCP specification",
            "project": "Deep Dive Coding",
            "priority": 4,
            "energy": "deep",
            "time_estimate": "2hr",
            "notes": "Focus on tool registration",
            "due_date": null,
            "completed": false,
            "completed_at": null,
            "created_at": "2025-12-25T10:00:00Z",
            "updated_at": "2025-12-25T10:00:00Z"
        }
    """

    id: int
    user_id: str
    completed: bool
    completed_at: str | None
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class TaskStats(BaseModel):
    """
    Schema for task statistics.

    Provides summary statistics for task management metrics.

    Example:
        {
            "total_tasks": 25,
            "completed_tasks": 10,
            "incomplete_tasks": 15,
            "completion_rate": 40.0,
            "by_project": {
                "Deep Dive Coding": 5,
                "Personal": 3
            },
            "by_priority": {
                "5": 2,
                "4": 5,
                "3": 8
            }
        }
    """

    total_tasks: int = Field(description="Total number of tasks")
    completed_tasks: int = Field(description="Number of completed tasks")
    incomplete_tasks: int = Field(description="Number of incomplete tasks")
    completion_rate: float = Field(description="Completion rate percentage")
    by_project: dict[str, int] = Field(description="Task count by project")
    by_priority: dict[str, int] = Field(description="Task count by priority level")
