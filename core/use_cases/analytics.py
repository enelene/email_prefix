"""
Analytics service using proper Visitor pattern for calculating statistics.
This respects Open/Closed principle - new habit types don't require changes here.
"""

from abc import ABC, abstractmethod
from datetime import date

# Import at the end to avoid circular import issues
from typing import TYPE_CHECKING, Any

from core.domain.base import HabitComponent
from core.interfaces.repository import IHabitRepository

if TYPE_CHECKING:
    from core.domain.entities import Habit, HabitGroup


class HabitVisitor(ABC):
    """Abstract visitor for processing different habit component types."""

    @abstractmethod
    def visit_habit(self, habit: "Habit") -> dict[str, Any]:
        """Visit a single habit."""
        pass

    @abstractmethod
    def visit_habit_group(self, group: "HabitGroup") -> dict[str, Any]:
        """Visit a habit group/routine."""
        pass


class StatisticsVisitor(HabitVisitor):
    """Concrete visitor that generates statistical reports."""

    def visit_habit(self, habit: "Habit") -> dict[str, Any]:
        """Generate statistics for a single habit."""
        # Calculate completion count
        completions = sum(1 for log in habit.logs if log.value >= habit.target)

        # Calculate current streak using the strategy pattern
        current_streak = habit.calculate_streak()

        # Calculate average value (for numeric habits)
        avg_value = 0.0
        if habit.logs:
            avg_value = sum(log.value for log in habit.logs) / len(habit.logs)

        return {
            "type": "habit",
            "name": habit.name,
            "habit_type": habit.habit_type.value,
            "category": habit.category.value,
            "completions": completions,
            "current_streak": current_streak,
            "target": habit.target,
            "average_value": round(avg_value, 2),
            "total_logs": len(habit.logs),
            "is_completed_today": habit.is_completed(date.today()),
        }

    def visit_habit_group(self, group: "HabitGroup") -> dict[str, Any]:
        """Generate statistics for a habit group/routine."""
        return {
            "type": "routine",
            "name": group.name,
            "sub_habits_count": len(group.habits),
            "progress_today": round(group.get_progress(date.today()), 2),
            "is_completed_today": group.is_completed(date.today()),
            "sub_habits": [h.name for h in group.habits],
        }


# Making HabitComponent visitable
def accept_visitor(component: HabitComponent, visitor: HabitVisitor) -> dict[str, Any]:
    """
    Helper function to apply visitor pattern to habit components.
    This is a workaround since we can't modify the ABC directly
    without breaking existing code.
    """
    # Import here to avoid circular import
    from core.domain.entities import Habit, HabitGroup

    if isinstance(component, Habit):
        return visitor.visit_habit(component)
    if isinstance(component, HabitGroup):
        return visitor.visit_habit_group(component)
    raise TypeError(f"Unknown component type: {type(component)}")


class AnalyticsService:
    """
    Service for generating habit analytics and statistics.
    Uses Visitor pattern for extensibility.
    """

    def __init__(self, repo: IHabitRepository):
        self.repo = repo
        self._visitor = StatisticsVisitor()

    def get_report(self, habit_id: str) -> dict[str, Any] | None:
        """Generate a statistical report for a habit or routine."""
        habit = self.repo.get_by_id(habit_id)
        if not habit:
            return None

        return accept_visitor(habit, self._visitor)

    def get_all_reports(self) -> list[dict[str, Any]]:
        """Generate reports for all habits."""
        habits = self.repo.list_all()
        return [accept_visitor(h, self._visitor) for h in habits]

    def get_summary(self) -> dict[str, Any]:
        """Generate an overall summary of all habits."""
        from core.domain.entities import Habit, HabitGroup

        habits = self.repo.list_all()

        total_habits = 0
        total_routines = 0
        completed_today = 0

        for habit in habits:
            if isinstance(habit, Habit):
                total_habits += 1
                if habit.is_completed(date.today()):
                    completed_today += 1
            elif isinstance(habit, HabitGroup):
                total_routines += 1
                if habit.is_completed(date.today()):
                    completed_today += 1

        return {
            "total_habits": total_habits,
            "total_routines": total_routines,
            "completed_today": completed_today,
            "completion_rate_today": (
                round((completed_today / len(habits)) * 100, 2) if habits else 0.0
            ),
        }
