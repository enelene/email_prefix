"""
Comprehensive test suite for Smart Habit Tracker API.
Tests CRUD operations, composite pattern, streaks, and error handling.
"""

import uuid
from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from core.domain.entities import Habit
from core.domain.enums import Category, HabitType

from runner.main import app, repo

client = TestClient(app)


# --- FIXTURE ---
@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    """Clear database before each test."""
    repo._storage.clear()
    yield


# ==========================================
# 1. BASIC CRUD TESTS
# ==========================================


def test_create_and_get_habit() -> None:
    """Test creating and retrieving a habit."""
    payload = {
        "name": "Drink Water",
        "description": "2 liters",
        "category": "health",
        "habit_type": "numeric",
        "target": 2.0,
    }
    response = client.post("/habits", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Drink Water"
    assert data["type"] == "habit"
    habit_id = data["id"]

    get_response = client.get(f"/habits/{habit_id}")
    assert get_response.status_code == 200
    habit_data = get_response.json()
    assert habit_data["name"] == "Drink Water"
    assert habit_data["target"] == 2.0


def test_list_habits() -> None:
    """Test listing all habits."""
    client.post(
        "/habits",
        json={"name": "Habit 1", "description": "desc1", "category": "health"},
    )
    client.post(
        "/habits",
        json={"name": "Habit 2", "description": "desc2", "category": "learning"},
    )

    response = client.get("/habits")
    assert response.status_code == 200
    habits = response.json()
    assert len(habits) == 2
    assert habits[0]["type"] == "habit"


def test_update_habit() -> None:
    """Test updating a habit's details."""
    res = client.post(
        "/habits",
        json={
            "name": "Run",
            "description": "5km",
            "category": "health",
            "habit_type": "numeric",
            "target": 5.0,
        },
    )
    habit_id = res.json()["id"]

    update_payload = {"name": "Walk", "target": 3.0}
    res = client.put(f"/habits/{habit_id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["name"] == "Walk"

    # Verify the update persisted
    get_res = client.get(f"/habits/{habit_id}")
    assert get_res.json()["name"] == "Walk"
    assert get_res.json()["target"] == 3.0


def test_delete_habit() -> None:
    """Test deleting a habit."""
    res = client.post(
        "/habits",
        json={"name": "To Delete", "description": "desc", "category": "health"},
    )
    habit_id = res.json()["id"]

    del_res = client.delete(f"/habits/{habit_id}")
    assert del_res.status_code == 204

    # Verify it's gone
    get_res = client.get(f"/habits/{habit_id}")
    assert get_res.status_code == 404


# ==========================================
# 2. TRACKING & ACCUMULATION TESTS
# ==========================================


def test_log_progress_accumulation() -> None:
    """Test that progress accumulates correctly throughout the day."""
    res = client.post(
        "/habits",
        json={
            "name": "Water",
            "description": "Hydrate",
            "category": "health",
            "habit_type": "numeric",
            "target": 2.0,
        },
    )
    habit_id = res.json()["id"]

    # Log 1.0 (Morning)
    log1 = client.post(f"/habits/{habit_id}/logs", json={"value": 1.0})
    assert log1.json()["value"] == 1.0
    assert log1.json()["is_completed"] is False

    # Log 0.5 (Afternoon) - total 1.5
    log2 = client.post(f"/habits/{habit_id}/logs", json={"value": 0.5})
    assert log2.json()["value"] == 1.5
    assert log2.json()["is_completed"] is False

    # Log 0.5 (Evening) - total 2.0 (target reached)
    log3 = client.post(f"/habits/{habit_id}/logs", json={"value": 0.5})
    assert log3.json()["value"] == 2.0
    assert log3.json()["is_completed"] is True

    # Check logs history
    logs_res = client.get(f"/habits/{habit_id}/logs")
    assert len(logs_res.json()) == 1  # One entry for today
    assert logs_res.json()[0]["value"] == 2.0


def test_boolean_habit_logging() -> None:
    """Test that boolean habits replace values instead of accumulating."""
    res = client.post(
        "/habits",
        json={
            "name": "Meditate",
            "description": "10 minutes",
            "category": "health",
            "habit_type": "boolean",
            "target": 1.0,
        },
    )
    habit_id = res.json()["id"]

    # Log 1.0 (done) - first time
    log1 = client.post(f"/habits/{habit_id}/logs", json={"value": 1.0})
    assert log1.status_code == 200
    assert log1.json()["value"] == 1.0
    assert log1.json()["is_completed"] is True

    # Log 1.0 again (updating the same day) - should stay 1.0, not become 2.0
    log2 = client.post(f"/habits/{habit_id}/logs", json={"value": 1.0})
    assert log2.status_code == 200
    assert log2.json()["value"] == 1.0  # Still 1.0, not 2.0!
    assert log2.json()["is_completed"] is True

    # Log 0.0 (mark as not done) - should replace
    log3 = client.post(f"/habits/{habit_id}/logs", json={"value": 0.0})
    assert log3.status_code == 200
    assert log3.json()["value"] == 0.0
    assert log3.json()["is_completed"] is False


# ==========================================
# 3. COMPOSITE PATTERN TESTS
# ==========================================


def test_create_routine_and_subhabits() -> None:
    """Test creating a routine with sub-habits."""
    routine_res = client.post(
        "/habits",
        json={"name": "Morning Routine", "description": "Start day", "is_group": True},
    )
    assert routine_res.json()["type"] == "routine"
    routine_id = routine_res.json()["id"]

    # Add sub-habits
    client.post(
        f"/habits/{routine_id}/subhabits",
        json={
            "name": "Stretch",
            "description": "10m",
            "category": "health",
            "habit_type": "boolean",
            "target": 1.0,
        },
    )
    client.post(
        f"/habits/{routine_id}/subhabits",
        json={
            "name": "Meditate",
            "description": "10m",
            "category": "health",
            "habit_type": "boolean",
            "target": 1.0,
        },
    )

    # Verify structure
    routine_data = client.get(f"/habits/{routine_id}").json()
    assert routine_data["sub_habit_count"] == 2
    assert len(routine_data["sub_habits"]) == 2


def test_routine_progress_calculation() -> None:
    """Test that routine progress is calculated correctly."""
    r_res = client.post(
        "/habits", json={"name": "Routine", "description": "desc", "is_group": True}
    )
    r_id = r_res.json()["id"]

    # Add two children
    c1 = client.post(
        f"/habits/{r_id}/subhabits",
        json={"name": "Task A", "description": "d", "target": 1.0},
    )
    c2 = client.post(
        f"/habits/{r_id}/subhabits",
        json={"name": "Task B", "description": "d", "target": 1.0},
    )

    child1_id = c1.json()["child_id"]
    child2_id = c2.json()["child_id"]

    # Complete only first child (50% progress)
    client.post(f"/habits/{child1_id}/logs", json={"value": 1.0})

    stats = client.get(f"/habits/{r_id}/stats").json()
    assert stats["data"]["progress_today"] == 50.0
    assert stats["data"]["is_completed_today"] is False

    # Complete second child (100% progress)
    client.post(f"/habits/{child2_id}/logs", json={"value": 1.0})

    stats = client.get(f"/habits/{r_id}/stats").json()
    assert stats["data"]["progress_today"] == 100.0
    assert stats["data"]["is_completed_today"] is True


# ==========================================
# 4. STREAK CALCULATION TESTS
# ==========================================


def test_streak_calculation_consecutive_days() -> None:
    """Test streak calculation with consecutive days."""
    habit_id = str(uuid.uuid4())
    habit = Habit(
        id=habit_id,
        name="Reading",
        description="Read daily",
        category=Category.LEARNING,
        habit_type=HabitType.BOOLEAN,
        target=1.0,
    )

    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)

    # Log 3 consecutive days
    habit.add_log(today, 1.0)
    habit.add_log(yesterday, 1.0)
    habit.add_log(day_before, 1.0)

    repo.save(habit)

    # Verify streak
    stats = client.get(f"/habits/{habit_id}/stats").json()
    assert stats["data"]["current_streak"] == 3
    assert stats["data"]["completions"] == 3


def test_streak_broken_by_gap() -> None:
    """Test that streak is broken by a gap in days."""
    habit_id = str(uuid.uuid4())
    habit = Habit(
        id=habit_id,
        name="Exercise",
        description="Daily exercise",
        category=Category.HEALTH,
        habit_type=HabitType.BOOLEAN,
        target=1.0,
    )

    today = date.today()
    yesterday = today - timedelta(days=1)
    three_days_ago = today - timedelta(days=3)  # Gap!

    habit.add_log(today, 1.0)
    habit.add_log(yesterday, 1.0)
    habit.add_log(three_days_ago, 1.0)  # This doesn't count in streak

    repo.save(habit)

    stats = client.get(f"/habits/{habit_id}/stats").json()
    assert stats["data"]["current_streak"] == 2  # Only today and yesterday


def test_streak_with_incomplete_days() -> None:
    """Test that incomplete days break the streak."""
    habit_id = str(uuid.uuid4())
    habit = Habit(
        id=habit_id,
        name="Water",
        description="2L water",
        category=Category.HEALTH,
        habit_type=HabitType.NUMERIC,
        target=2.0,
    )

    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)

    habit.add_log(today, 2.0)  # Complete
    habit.add_log(yesterday, 1.0)  # Incomplete (< 2.0)
    habit.add_log(day_before, 2.0)  # Complete (but doesn't count due to gap)

    repo.save(habit)

    stats = client.get(f"/habits/{habit_id}/stats").json()
    assert stats["data"]["current_streak"] == 1  # Only today


# ==========================================
# 5. ERROR HANDLING
# ==========================================


def test_get_non_existent_habit() -> None:
    """Test getting a habit that doesn't exist."""
    res = client.get("/habits/non-existent-id")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_update_non_existent_habit() -> None:
    """Test updating a habit that doesn't exist."""
    res = client.put("/habits/fake-id", json={"name": "New Name"})
    assert res.status_code == 404


def test_delete_non_existent_habit() -> None:
    """Test deleting a habit that doesn't exist."""
    res = client.delete("/habits/fake-id")
    assert res.status_code == 404


def test_log_to_routine_fails() -> None:
    """Test that logging to a routine returns an error."""
    r_res = client.post(
        "/habits", json={"name": "Routine", "description": "d", "is_group": True}
    )
    r_id = r_res.json()["id"]

    res = client.post(f"/habits/{r_id}/logs", json={"value": 1.0})
    assert res.status_code == 400
    assert "routine" in res.json()["detail"].lower()


def test_add_subhabit_to_non_group_fails() -> None:
    """Test that adding a sub-habit to a non-routine fails."""
    h_res = client.post(
        "/habits", json={"name": "Regular Habit", "description": "d", "is_group": False}
    )
    h_id = h_res.json()["id"]

    res = client.post(
        f"/habits/{h_id}/subhabits", json={"name": "Sub", "description": "d"}
    )
    assert res.status_code == 400
    assert "not a routine" in res.json()["detail"].lower()


def test_add_subhabit_to_non_existent_routine() -> None:
    """Test adding a sub-habit to a non-existent routine."""
    res = client.post(
        "/habits/fake-routine-id/subhabits", json={"name": "Sub", "description": "d"}
    )
    assert res.status_code == 400


# ==========================================
# 6. HEALTH CHECK
# ==========================================


def test_health_check() -> None:
    """Test the health check endpoint."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
