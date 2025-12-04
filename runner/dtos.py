"""
Data Transfer Objects for API requests and responses.
Provides consistent, standardized API responses.
"""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from core.domain.enums import Category, HabitType

# ============================================
# REQUEST MODELS
# ============================================


class CreateHabitRequest(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the habit"
    )
    description: str = Field(..., max_length=500, description="Short description")
    category: Category = Field(
        default=Category.HEALTH, description="Category of the habit"
    )
    habit_type: HabitType = Field(
        default=HabitType.BOOLEAN, description="Type of tracking"
    )
    target: float = Field(
        default=1.0, gt=0, description="Target value (e.g., 1.0 for Yes/No, 5.0 for km)"
    )
    is_group: bool = Field(
        default=False, description="Set to True if this is a Routine/Group"
    )


class UpdateHabitRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)
    target: float | None = Field(None, gt=0)


class LogRequest(BaseModel):
    value: float = Field(
        ..., ge=0, description="Amount to log (e.g., 1.0 for done, 5.0 for 5km)"
    )
    accumulate: bool = Field(
        default=True,
        description="If True, add to today's existing value. If False, replace it.",
    )


# ============================================
# RESPONSE MODELS (Standardized)
# ============================================


class LogResponse(BaseModel):
    """Represents a single log entry."""

    date: date
    value: float


class HabitResponse(BaseModel):
    """Standard response for a single habit."""

    id: str
    name: str
    description: str
    category: str
    habit_type: str
    target: float
    created_at: date
    logs: list[LogResponse]


class HabitGroupResponse(BaseModel):
    """Standard response for a habit group/routine."""

    id: str
    name: str
    description: str
    created_at: date
    sub_habits: list[str]  # List of sub-habit IDs
    sub_habit_count: int


class HabitListItemResponse(BaseModel):
    """Simplified response for habit lists."""

    id: str
    name: str
    description: str
    type: str  # "habit" or "routine"
    created_at: date


class CreateHabitResponse(BaseModel):
    """Response after creating a habit."""

    status: str = "created"
    id: str
    name: str
    type: str  # "habit" or "routine"


class UpdateHabitResponse(BaseModel):
    """Response after updating a habit."""

    status: str = "updated"
    id: str
    name: str


class DeleteHabitResponse(BaseModel):
    """Response after deleting a habit."""

    status: str = "deleted"
    id: str


class LogProgressResponse(BaseModel):
    """Response after logging progress."""

    status: str = "logged"
    habit_id: str
    date: date
    value: float
    is_completed: bool


class AddSubHabitResponse(BaseModel):
    """Response after adding a sub-habit to a routine."""

    status: str = "added"
    parent_id: str
    child_id: str
    child_name: str


class StatsResponse(BaseModel):
    """Response for habit statistics."""

    type: str
    name: str
    data: dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: str | None = None
    status_code: int


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.1.0"
