from typing import List, Optional, Dict
from core.interfaces.repository import IHabitRepository
from core.domain.base import HabitComponent


class InMemoryHabitRepository(IHabitRepository):
    """
    Concrete implementation of the repository using a Python dictionary.
    This belongs in the 'Outer Layer' (runner) because it deals with
    infrastructure (storage), not business rules.
    """

    def __init__(self) -> None:
        self._storage: Dict[str, HabitComponent] = {}

    def save(self, habit: HabitComponent) -> HabitComponent:
        """Saves or updates a habit/group."""
        self._storage[habit.id] = habit
        return habit

    def get_by_id(self, habit_id: str) -> Optional[HabitComponent]:
        """Retrieves a single item by ID."""
        return self._storage.get(habit_id)

    def list_all(self) -> List[HabitComponent]:
        """Returns all items in storage."""
        return list(self._storage.values())

    def delete(self, habit_id: str) -> bool:
        """Deletes an item. Returns True if found and deleted."""
        if habit_id in self._storage:
            del self._storage[habit_id]
            return True
        return False
