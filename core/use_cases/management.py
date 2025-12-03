import uuid
from typing import List, Optional, Dict, Any
from core.domain.entities import Habit, HabitGroup
from core.domain.base import HabitComponent
from core.domain.enums import Category, HabitType
from core.interfaces.repository import IHabitRepository


class HabitManager:
    """
    Handles the creation, modification, and organization of habits.
    """

    def __init__(self, repo: IHabitRepository):
        self.repo = repo

    def create_habit(
        self, name: str, desc: str, cat: Category, h_type: HabitType, target: float
    ) -> Habit:
        new_id = str(uuid.uuid4())
        habit = Habit(
            id=new_id,
            name=name,
            description=desc,
            category=cat,
            habit_type=h_type,
            target=target,
        )
        self.repo.save(habit)
        return habit

    def create_routine(self, name: str, desc: str) -> HabitGroup:
        new_id = str(uuid.uuid4())
        group = HabitGroup(id=new_id, name=name, description=desc)
        self.repo.save(group)
        return group

    def update_habit(
        self, habit_id: str, updates: Dict[str, Any]
    ) -> Optional[HabitComponent]:
        habit = self.repo.get_by_id(habit_id)
        if not habit:
            return None

        # Apply updates if the key exists in the dictionary and is not None
        if "name" in updates and updates["name"] is not None:
            habit.name = updates["name"]
        if "description" in updates and updates["description"] is not None:
            habit.description = updates["description"]

        # Target only applies to Leafs (Habit), not Groups
        if (
            isinstance(habit, Habit)
            and "target" in updates
            and updates["target"] is not None
        ):
            habit.target = updates["target"]

        self.repo.save(habit)
        return habit

    def delete_habit(self, habit_id: str) -> bool:
        return self.repo.delete(habit_id)

    def add_to_routine(self, routine_id: str, habit: HabitComponent) -> bool:
        routine = self.repo.get_by_id(routine_id)
        if isinstance(routine, HabitGroup):
            routine.add(habit)
            self.repo.save(routine)
            return True
        return False

    def get_habit(self, habit_id: str) -> Optional[HabitComponent]:
        return self.repo.get_by_id(habit_id)

    def get_all(self) -> List[HabitComponent]:
        return self.repo.list_all()
