from fastapi import FastAPI, HTTPException, Depends
from typing import List, Dict, Any, Union

from core.use_cases.management import HabitManager
from core.use_cases.tracking import ProgressTracker
from core.use_cases.analytics import AnalyticsService
from core.domain.base import HabitComponent
from core.domain.entities import Habit, HabitGroup
from runner.database import InMemoryHabitRepository
from runner.dtos import CreateHabitRequest, LogRequest, UpdateHabitRequest

app = FastAPI(title="Smart Habit Tracker")

# --- DEPENDENCY INJECTION ---
repo = InMemoryHabitRepository()
manager = HabitManager(repo)
tracker = ProgressTracker(repo)
analytics = AnalyticsService(repo)

# --- EXISTING ENDPOINTS ---

@app.post("/habits", status_code=201)
def create_habit(req: CreateHabitRequest) -> Union[Habit, HabitGroup]:
    if req.is_group:
        return manager.create_routine(req.name, req.description)
    return manager.create_habit(req.name, req.description, req.category, req.habit_type, req.target)

@app.get("/habits")
def list_habits() -> List[HabitComponent]:
    return manager.get_all()

@app.get("/habits/{habit_id}")
def get_habit(habit_id: str) -> HabitComponent:
    habit = manager.get_habit(habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit

# --- NEW ENDPOINTS ---

@app.put("/habits/{habit_id}")
def update_habit(habit_id: str, req: UpdateHabitRequest) -> HabitComponent:
    """Updates a habit's details."""
    updates = req.dict(exclude_unset=True)
    updated_habit = manager.update_habit(habit_id, updates)
    
    if not updated_habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return updated_habit

@app.delete("/habits/{habit_id}", status_code=204)
def delete_habit(habit_id: str) -> None:
    """Deletes a habit or routine."""
    success = manager.delete_habit(habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")
    return

@app.get("/habits/{habit_id}/logs")
def get_logs(habit_id: str) -> List[Any]:
    """Retrieves the history of logs for a habit."""
    logs = tracker.get_history(habit_id)
    if logs is None:
        if not manager.get_habit(habit_id):
            raise HTTPException(status_code=404, detail="Habit not found")
        else:
            return [] 
    return logs

# --- EXISTING LOGIC CONTINUED ---

@app.post("/habits/{habit_id}/subhabits", status_code=201)
def add_sub_habit(habit_id: str, req: CreateHabitRequest) -> Dict[str, str]:
    child = manager.create_habit(req.name, req.description, req.category, req.habit_type, req.target)
    success = manager.add_to_routine(habit_id, child)
    if not success:
        raise HTTPException(status_code=400, detail="Parent not found or not a Group")
    return {"status": "added", "parent_id": habit_id, "child_id": child.id}

@app.post("/habits/{habit_id}/logs")
def log_progress(habit_id: str, req: LogRequest) -> Dict[str, Any]:
    result = tracker.log_progress(habit_id, req.value)
    if result is None:
        raise HTTPException(status_code=404, detail="Habit not found or is a Group")
    return {"status": "logged", "value": result}

@app.get("/habits/{habit_id}/stats")
def get_stats(habit_id: str) -> Dict[str, Any]:
    stats = analytics.get_report(habit_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Habit not found")
    return stats

# --- RUNNER ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("runner.main:app", host="127.0.0.1", port=8000, reload=True)