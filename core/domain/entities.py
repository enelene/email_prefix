from dataclasses import dataclass, field
from datetime import date

from core.domain.base import HabitComponent
from core.domain.enums import Category, HabitType
from core.domain.strategies import HabitStrategy, HabitStrategyFactory


@dataclass
class Log:
    date: date
    value: float


@dataclass
class Habit(HabitComponent):
    id: str
    name: str
    description: str
    category: Category
    habit_type: HabitType
    target: float = 1.0
    created_at: date = field(default_factory=date.today)
    logs: list[Log] = field(default_factory=list)
    _strategy: HabitStrategy = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize the strategy based on habit type."""
        self._strategy = HabitStrategyFactory.create(self.habit_type.value)

    def add_log(self, log_date: date, value: float) -> None:
        """Add or update a log entry for a specific date."""
        # Validate the value using the strategy
        if not self._strategy.validate_value(value):
            raise ValueError(
                f"Invalid value {value} for habit type {self.habit_type}. "
                f"Expected: {self._get_validation_hint()}"
            )

        # Update existing log or create new one
        for log in self.logs:
            if log.date == log_date:
                log.value = value
                return
        self.logs.append(Log(date=log_date, value=value))

    def _get_validation_hint(self) -> str:
        """Get a helpful hint about valid values for this habit type."""
        if self.habit_type.value == "boolean":
            return "0.0 or 1.0 only"
        if self.habit_type.value == "numeric":
            return "any non-negative number"
        if self.habit_type.value == "time":
            return "0.0 to 1440.0 (minutes)"
        return "check habit type documentation"

    def get_progress(self, target_date: date) -> float:
        """Get the logged value for a specific date."""
        for log in self.logs:
            if log.date == target_date:
                return log.value
        return 0.0

    def is_completed(self, target_date: date) -> bool:
        """Check if habit was completed on a specific date using the strategy."""
        value = self.get_progress(target_date)
        return self._strategy.is_completed(value, self.target)

    def calculate_streak(self) -> int:
        """Calculate current streak using the strategy."""
        log_tuples = [(log.date, log.value) for log in self.logs]
        return self._strategy.calculate_streak(log_tuples, self.target)


@dataclass
class HabitGroup(HabitComponent):
    id: str
    name: str
    description: str
    created_at: date = field(default_factory=date.today)
    habits: list[HabitComponent] = field(default_factory=list)

    def add(self, component: HabitComponent) -> None:
        """Add a habit or sub-group to this group."""
        self.habits.append(component)

    def remove(self, component_id: str) -> bool:
        """Remove a habit from this group."""
        for i, habit in enumerate(self.habits):
            if habit.id == component_id:
                self.habits.pop(i)
                return True
        return False

    def get_progress(self, target_date: date) -> float:
        """
        Calculate progress as percentage of completed sub-habits.
        Returns 0-100.
        """
        if not self.habits:
            return 0.0
        completed = sum(1 for h in self.habits if h.is_completed(target_date))
        return (completed / len(self.habits)) * 100.0

    def is_completed(self, target_date: date) -> bool:
        """Group is completed when ALL sub-habits are completed."""
        if not self.habits:
            return False
        return all(h.is_completed(target_date) for h in self.habits)
