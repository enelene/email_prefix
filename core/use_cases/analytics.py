from datetime import date
from typing import Dict, Any, Optional
from core.domain.entities import Habit, HabitGroup
from core.interfaces.repository import IHabitRepository


class AnalyticsService:
    """
    Handles the calculation of statistics (Streaks, Completion rates).
    Visitor-like pattern: behaves differently for Leaves vs Groups.
    """

    def __init__(self, repo: IHabitRepository):
        self.repo = repo

    def get_report(self, habit_id: str) -> Optional[Dict[str, Any]]:
        habit = self.repo.get_by_id(habit_id)
        if not habit:
            return None

        if isinstance(habit, Habit):
            return self._analyze_leaf(habit)
        elif isinstance(habit, HabitGroup):
            return self._analyze_group(habit)
        return None

    def _analyze_leaf(self, habit: Habit) -> Dict[str, Any]:
        # Calculate completion count
        completions = sum(1 for log in habit.logs if log.value >= habit.target)

        return {
            "type": "habit",
            "name": habit.name,
            "completions": completions,
            "target": habit.target,
            "is_completed_today": habit.is_completed(date.today()),
        }

    def _analyze_group(self, group: HabitGroup) -> Dict[str, Any]:
        return {
            "type": "routine",
            "name": group.name,
            "sub_habits_count": len(group.habits),
            "progress_today": group.get_progress(date.today()),
        }
