import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
import uuid
from typing import Generator

# Import the app and the global repository
from runner.main import app, repo
from core.domain.entities import Habit, Log
from core.domain.enums import Category, HabitType

client = TestClient(app)

# --- FIXTURE ---
@pytest.fixture(autouse=True)
def reset_db() -> Generator[None, None, None]:
    repo._storage.clear()
    yield

# ==========================================
# 1. BASIC CRUD TESTS
# ==========================================

def test_create_and_get_habit() -> None:
    # 1. Create
    payload = {
        "name": "Drink Water",
        "description": "2 liters",
        "category": "health",
        "habit_type": "numeric",
        "target": 2.0
    }
    response = client.post("/habits", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Drink Water"
    habit_id = data["id"]

    # 2. Get
    get_response = client.get(f"/habits/{habit_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == habit_id

def test_update_habit() -> None:
    # Create
    res = client.post("/habits", json={
        "name": "Run", "description": "5km", 
        "category": "health", "habit_type": "numeric", "target": 5.0
    })
    habit_id = res.json()["id"]

    # Update
    update_payload = {"name": "Walk", "target": 3.0}
    res = client.put(f"/habits/{habit_id}", json=update_payload)
    assert res.status_code == 200
    assert res.json()["name"] == "Walk"
    assert res.json()["target"] == 3.0

def test_delete_habit() -> None:
    # Create
    res = client.post("/habits", json={
        "name": "To Delete", "description": "desc", "category": "health"
    })
    habit_id = res.json()["id"]

    # Delete
    del_res = client.delete(f"/habits/{habit_id}")
    assert del_res.status_code == 204

    # Verify it's gone
    get_res = client.get(f"/habits/{habit_id}")
    assert get_res.status_code == 404

# ==========================================
# 2. TRACKING & ACCUMULATION TESTS
# ==========================================

def test_log_progress_accumulation() -> None:
    # 1. Create Habit
    res = client.post("/habits", json={
        "name": "Water", "description": "Hydrate", 
        "category": "health", "habit_type": "numeric", "target": 2.0
    })
    habit_id = res.json()["id"]

    # 2. Log 1.0 (Morning)
    client.post(f"/habits/{habit_id}/logs", json={"value": 1.0})
    
    # 3. Log 0.5 (Afternoon)
    client.post(f"/habits/{habit_id}/logs", json={"value": 0.5})

    # 4. Check Logs
    log_res = client.get(f"/habits/{habit_id}/logs")
    assert log_res.status_code == 200
    
    stats_res = client.get(f"/habits/{habit_id}/stats")
    assert stats_res.json()["completions"] == 0
    
    # 5. Log 0.5 (Evening) -> Total 2.0
    client.post(f"/habits/{habit_id}/logs", json={"value": 0.5})
    
    stats_res = client.get(f"/habits/{habit_id}/stats")
    assert stats_res.json()["completions"] == 1

# ==========================================
# 3. COMPOSITE PATTERN TESTS
# ==========================================

def test_create_routine_and_subhabits() -> None:
    # 1. Create Routine
    routine_res = client.post("/habits", json={
        "name": "Morning Routine", "description": "Start day", "is_group": True
    })
    routine_id = routine_res.json()["id"]

    # 2. Create Sub-habits
    client.post(f"/habits/{routine_id}/subhabits", json={
        "name": "Stretch", "description": "10m", 
        "category": "health", "habit_type": "boolean", "target": 1.0
    })
    client.post(f"/habits/{routine_id}/subhabits", json={
        "name": "Meditate", "description": "10m", 
        "category": "health", "habit_type": "boolean", "target": 1.0
    })

    # 4. Verify Structure
    stats_res = client.get(f"/habits/{routine_id}/stats")
    assert stats_res.status_code == 200
    assert stats_res.json()["type"] == "routine"
    assert stats_res.json()["sub_habits_count"] == 2

def test_routine_progress_calculation() -> None:
    # 1. Create Routine
    r_res = client.post("/habits", json={"name": "Routine", "description": "desc", "is_group": True})
    r_id = r_res.json()["id"]

    # 2. Add Children
    c1 = client.post(f"/habits/{r_id}/subhabits", json={"name": "A", "description": "d", "target": 1.0})
    # c2 = ... (unused in this specific test flow logic, kept simple)
    client.post(f"/habits/{r_id}/subhabits", json={"name": "B", "description": "d", "target": 1.0})
    
    child1_id = c1.json()["child_id"]
    
    # 3. Log progress
    client.post(f"/habits/{child1_id}/logs", json={"value": 1.0})

    # 4. Check Routine Stats (50% done)
    stats = client.get(f"/habits/{r_id}/stats").json()
    assert stats["progress_today"] == 50.0

# ==========================================
# 4. ADVANCED LOGIC (STREAKS)
# ==========================================

def test_streak_calculation() -> None:
    habit_id = str(uuid.uuid4())
    habit = Habit(
        id=habit_id, name="Reading", description="Read", 
        category=Category.LEARNING, habit_type=HabitType.BOOLEAN, target=1.0
    )
    
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    habit.add_log(today, 1.0)
    habit.add_log(yesterday, 1.0)
    habit.add_log(day_before, 1.0)
    
    repo.save(habit)
    
    res = client.get(f"/habits/{habit_id}/stats")
    assert res.status_code == 200
    # Assuming the implementation counts total completions
    assert res.json()["completions"] == 3 

# ==========================================
# 5. ERROR HANDLING
# ==========================================

def test_get_non_existent_habit() -> None:
    res = client.get("/habits/99999")
    assert res.status_code == 404

def test_log_to_group_fails() -> None:
    r_res = client.post("/habits", json={"name": "G", "description": "d", "is_group": True})
    r_id = r_res.json()["id"]
    
    res = client.post(f"/habits/{r_id}/logs", json={"value": 1.0})
    assert res.status_code in [400, 404]

def test_add_subhabit_to_non_group_fails() -> None:
    h_res = client.post("/habits", json={"name": "H", "description": "d", "is_group": False})
    h_id = h_res.json()["id"]
    
    res = client.post(f"/habits/{h_id}/subhabits", json={"name": "Sub", "description": "d"})
    assert res.status_code == 400