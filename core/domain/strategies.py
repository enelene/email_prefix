"""
Strategy Pattern for different habit type behaviors.
This makes the system Open/Closed - new habit types
can be added without modifying existing code.
"""

from abc import ABC, abstractmethod
from datetime import date, timedelta


class HabitStrategy(ABC):
    """Abstract strategy for habit-specific behavior."""

    @abstractmethod
    def is_completed(self, value: float, target: float) -> bool:
        """Determine if the habit is completed based on logged value."""
        pass

    @abstractmethod
    def validate_value(self, value: float) -> bool:
        """Validate that the logged value is appropriate for this habit type."""
        pass

    @abstractmethod
    def calculate_streak(self, logs: list[tuple[date, float]], target: float) -> int:
        """Calculate the current streak for this habit type."""
        pass


class BooleanHabitStrategy(HabitStrategy):
    """Strategy for yes/no habits (done or not done)."""

    def is_completed(self, value: float, target: float) -> bool:
        return value >= target

    def validate_value(self, value: float) -> bool:
        # Boolean habits should be 0.0 or 1.0
        return value in (0.0, 1.0)

    def calculate_streak(self, logs: list[tuple[date, float]], target: float) -> int:
        if not logs:
            return 0

        # Sort logs by date descending (most recent first)
        sorted_logs = sorted(logs, key=lambda x: x[0], reverse=True)

        streak = 0
        expected_date = date.today()

        for log_date, value in sorted_logs:
            if log_date == expected_date and value >= target:
                streak += 1
                expected_date -= timedelta(days=1)
            elif log_date < expected_date:
                # Gap in dates, streak broken
                break

        return streak


class NumericHabitStrategy(HabitStrategy):
    """Strategy for measurable quantity habits (km, pages, minutes, etc)."""

    def is_completed(self, value: float, target: float) -> bool:
        return value >= target

    def validate_value(self, value: float) -> bool:
        # Numeric habits should be non-negative
        return value >= 0.0

    def calculate_streak(self, logs: list[tuple[date, float]], target: float) -> int:
        if not logs:
            return 0

        sorted_logs = sorted(logs, key=lambda x: x[0], reverse=True)

        streak = 0
        expected_date = date.today()

        for log_date, value in sorted_logs:
            if log_date == expected_date and value >= target:
                streak += 1
                expected_date -= timedelta(days=1)
            elif log_date < expected_date:
                break

        return streak


# Future habit types can be added here without modifying existing code
class TimeBasedHabitStrategy(HabitStrategy):
    """Strategy for time-duration habits (minutes, hours)."""

    def is_completed(self, value: float, target: float) -> bool:
        return value >= target

    def validate_value(self, value: float) -> bool:
        # Time should be positive and reasonable (less than 24 hours = 1440 minutes)
        return 0.0 <= value <= 1440.0

    def calculate_streak(self, logs: list[tuple[date, float]], target: float) -> int:
        # Similar to numeric, but could have different logic if needed
        if not logs:
            return 0

        sorted_logs = sorted(logs, key=lambda x: x[0], reverse=True)
        streak = 0
        expected_date = date.today()

        for log_date, value in sorted_logs:
            if log_date == expected_date and value >= target:
                streak += 1
                expected_date -= timedelta(days=1)
            elif log_date < expected_date:
                break

        return streak


class HabitStrategyFactory:
    """Factory for creating habit strategies based on habit type."""

    _strategies: dict[str, type[HabitStrategy]] = {
        "boolean": BooleanHabitStrategy,
        "numeric": NumericHabitStrategy,
        "time": TimeBasedHabitStrategy,
    }

    @classmethod
    def create(cls, habit_type: str) -> HabitStrategy:
        """Create and return the appropriate strategy for the given habit type."""
        strategy_class = cls._strategies.get(habit_type.lower())
        if not strategy_class:
            raise ValueError(f"Unknown habit type: {habit_type}")
        return strategy_class()  # Instantiate the concrete class

    @classmethod
    def register_strategy(
        cls, habit_type: str, strategy_class: type[HabitStrategy]
    ) -> None:
        """Register a new habit strategy (for extensibility)."""
        cls._strategies[habit_type.lower()] = strategy_class
