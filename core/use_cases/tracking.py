from datetime import date

from core.domain.entities import Habit, Log
from core.interfaces.repository import IHabitRepository


class ProgressTracker:
    """
    Handles the recording and retrieval of progress logs.
    """

    def __init__(self, repo: IHabitRepository):
        self.repo = repo

    def log_progress(self, habit_id: str, value: float) -> float | None:
        habit = self.repo.get_by_id(habit_id)

        if isinstance(habit, Habit):
            current_val = habit.get_progress(date.today())
            new_val = current_val + value

            habit.add_log(date.today(), new_val)
            self.repo.save(habit)
            return new_val

        return None

    def get_history(self, habit_id: str) -> list[Log] | None:
        habit = self.repo.get_by_id(habit_id)

        if isinstance(habit, Habit):
            return habit.logs

        return None
