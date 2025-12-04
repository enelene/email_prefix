"""
FastAPI application with standardized responses and proper error handling.
Follows RESTful principles with consistent response formats.
"""

from datetime import date
from typing import Any

from fastapi import FastAPI, HTTPException, status

from core.domain.entities import Habit, HabitGroup
from core.use_cases.analytics import AnalyticsService
from core.use_cases.management import HabitManager
from core.use_cases.tracking import ProgressTracker

from runner.database import InMemoryHabitRepository
from runner.dtos import (
    AddSubHabitResponse,
    CreateHabitRequest,
    CreateHabitResponse,
    HabitListItemResponse,
    HealthCheckResponse,
    LogProgressResponse,
    LogRequest,
    LogResponse,
    StatsResponse,
    UpdateHabitRequest,
    UpdateHabitResponse,
)

app = FastAPI(
    title="Smart Habit Tracker API",
    description="RESTful API for tracking habits and routines",
    version="0.1.0",
)

# --- DEPENDENCY INJECTION ---
repo = InMemoryHabitRepository()
manager = HabitManager(repo)
tracker = ProgressTracker(repo)
analytics = AnalyticsService(repo)


# --- HEALTH CHECK ---
@app.get("/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    return HealthCheckResponse()


# --- HABIT MANAGEMENT ENDPOINTS ---


@app.post(
    "/habits", status_code=status.HTTP_201_CREATED, response_model=CreateHabitResponse
)
def create_habit(req: CreateHabitRequest) -> CreateHabitResponse:
    """Create a new habit or routine."""
    if req.is_group:
        group = manager.create_routine(req.name, req.description)
        return CreateHabitResponse(id=group.id, name=group.name, type="routine")

    habit = manager.create_habit(
        req.name, req.description, req.category, req.habit_type, req.target
    )
    return CreateHabitResponse(id=habit.id, name=habit.name, type="habit")


@app.get("/habits", response_model=list[HabitListItemResponse])
def list_habits() -> list[HabitListItemResponse]:
    """List all habits and routines."""
    habits = manager.get_all()
    return [
        HabitListItemResponse(
            id=h.id,
            name=h.name,
            description=h.description,
            type="routine" if isinstance(h, HabitGroup) else "habit",
            created_at=h.created_at if hasattr(h, "created_at") else date.today(),
        )
        for h in habits
    ]


@app.get("/habits/{habit_id}")
def get_habit(habit_id: str) -> dict[str, Any]:
    """Get a single habit or routine with full details."""
    habit = manager.get_habit(habit_id)
    if not habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id '{habit_id}' not found",
        )

    if isinstance(habit, HabitGroup):
        return {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "type": "routine",
            "created_at": habit.created_at.isoformat(),
            "sub_habits": [{"id": h.id, "name": h.name} for h in habit.habits],
            "sub_habit_count": len(habit.habits),
        }

    # It's a regular Habit - cast for type checking
    if isinstance(habit, Habit):
        return {
            "id": habit.id,
            "name": habit.name,
            "description": habit.description,
            "type": "habit",
            "category": habit.category.value,
            "habit_type": habit.habit_type.value,
            "target": habit.target,
            "created_at": habit.created_at.isoformat(),
            "total_logs": len(habit.logs),
            "current_streak": habit.calculate_streak(),
        }

    # Fallback (should never reach here)
    return {"error": "Unknown habit type"}


@app.put("/habits/{habit_id}", response_model=UpdateHabitResponse)
def update_habit(habit_id: str, req: UpdateHabitRequest) -> UpdateHabitResponse:
    """Update a habit's details (partial update)."""
    updates = req.model_dump(exclude_unset=True)
    updated_habit = manager.update_habit(habit_id, updates)

    if not updated_habit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id '{habit_id}' not found",
        )

    return UpdateHabitResponse(id=updated_habit.id, name=updated_habit.name)


@app.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: str) -> None:
    """Delete a habit or routine."""
    success = manager.delete_habit(habit_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id '{habit_id}' not found",
        )


# --- SUB-HABIT MANAGEMENT ---


@app.post(
    "/habits/{habit_id}/subhabits",
    status_code=status.HTTP_201_CREATED,
    response_model=AddSubHabitResponse,
)
def add_sub_habit(habit_id: str, req: CreateHabitRequest) -> AddSubHabitResponse:
    """Add a sub-habit to a routine."""
    # Create the child habit
    child = manager.create_habit(
        req.name, req.description, req.category, req.habit_type, req.target
    )

    # Add to parent routine
    success = manager.add_to_routine(habit_id, child)
    if not success:
        # Clean up the created habit
        manager.delete_habit(child.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parent with id '{habit_id}' not found or is not a routine",
        )

    return AddSubHabitResponse(
        parent_id=habit_id, child_id=child.id, child_name=child.name
    )


# --- PROGRESS TRACKING ---


@app.post("/habits/{habit_id}/logs", response_model=LogProgressResponse)
def log_progress(habit_id: str, req: LogRequest) -> LogProgressResponse:
    """Record progress for a habit."""
    result = tracker.log_progress(habit_id, req.value)

    if result is None:
        habit = manager.get_habit(habit_id)
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Habit with id '{habit_id}' not found",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot log progress for routines, only individual habits",
        )

    # Get updated habit to check completion status
    habit = manager.get_habit(habit_id)
    is_completed = False
    if isinstance(habit, Habit):
        is_completed = habit.is_completed(date.today())

    return LogProgressResponse(
        habit_id=habit_id, date=date.today(), value=result, is_completed=is_completed
    )


@app.get("/habits/{habit_id}/logs", response_model=list[LogResponse])
def get_logs(habit_id: str) -> list[LogResponse]:
    """Retrieve the history of logs for a habit."""
    logs = tracker.get_history(habit_id)

    if logs is None:
        habit = manager.get_habit(habit_id)
        if not habit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Habit with id '{habit_id}' not found",
            )
        # It's a routine, return empty list
        return []

    return [LogResponse(date=log.date, value=log.value) for log in logs]


# --- ANALYTICS ---


@app.get("/habits/{habit_id}/stats", response_model=StatsResponse)
def get_stats(habit_id: str) -> StatsResponse:
    """Get statistics for a habit or routine."""
    stats = analytics.get_report(habit_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Habit with id '{habit_id}' not found",
        )

    habit_type = stats.pop("type")
    habit_name = stats.pop("name")

    return StatsResponse(type=habit_type, name=habit_name, data=stats)


@app.get("/stats/summary")
def get_summary() -> dict[str, Any]:
    """Get overall summary of all habits."""
    return analytics.get_summary()


# --- RUNNER ---
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("runner.main:app", host="127.0.0.1", port=8000, reload=True)
