from datetime import date

from core.domain.entities import Habit, Log
from core.interfaces.repository import IHabitRepository


class ProgressTracker:
    """
    Handles the recording and retrieval of progress logs.
    """

    def __init__(self, repo: IHabitRepository):
        self.repo = repo

    def log_progress(
        self, habit_id: str, value: float, accumulate: bool = True
    ) -> float | None:
        """
        Log progress for a habit.

        Args:
            habit_id: ID of the habit to log progress for
            value: Value to log
            accumulate: If True, add to existing value for today.
                       If False, replace existing value for today.

        Returns:
            The new total value for today, or None if habit not found/not a Habit
        """
        habit = self.repo.get_by_id(habit_id)

        if isinstance(habit, Habit):
            # For boolean habits, always replace (don't accumulate)
            # For numeric habits, allow accumulation
            if habit.habit_type.value == "boolean":
                # Boolean habits should replace, not accumulate
                habit.add_log(date.today(), value)
                self.repo.save(habit)
                return value
            # Numeric habits can accumulate throughout the day
            if accumulate:
                current_val = habit.get_progress(date.today())
                new_val = current_val + value
            else:
                new_val = value

            habit.add_log(date.today(), new_val)
            self.repo.save(habit)
            return new_val

        return None

    def get_history(self, habit_id: str) -> list[Log] | None:
        habit = self.repo.get_by_id(habit_id)

        if isinstance(habit, Habit):
            return habit.logs

        return None
