from abc import ABC, abstractmethod

from core.domain.base import HabitComponent


class IHabitRepository(ABC):
    """
    Abstract Interface for data access.
    The Core layer uses this interface without knowing HOW data is stored.
    """

    @abstractmethod
    def save(self, habit: HabitComponent) -> HabitComponent:
        pass

    @abstractmethod
    def get_by_id(self, habit_id: str) -> HabitComponent | None:
        pass

    @abstractmethod
    def list_all(self) -> list[HabitComponent]:
        pass

    @abstractmethod
    def delete(self, habit_id: str) -> bool:
        pass
