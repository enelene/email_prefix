from abc import ABC, abstractmethod
from datetime import date


class HabitComponent(ABC):
    """Component interface for the Composite Pattern."""

    # We explicitly type-hint these fields so Mypy knows
    # that any HabitComponent (Leaf or Group) has them.
    id: str
    name: str
    description: str
    created_at: date

    @abstractmethod
    def get_progress(self, target_date: date) -> float:
        pass

    @abstractmethod
    def is_completed(self, target_date: date) -> bool:
        pass
