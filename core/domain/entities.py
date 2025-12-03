from dataclasses import dataclass, field
from datetime import date
from typing import List
from core.domain.base import HabitComponent
from core.domain.enums import Category, HabitType


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
    logs: List[Log] = field(default_factory=list)

    def add_log(self, log_date: date, value: float) -> None:
        for log in self.logs:
            if log.date == log_date:
                log.value = value
                return
        self.logs.append(Log(date=log_date, value=value))

    def get_progress(self, target_date: date) -> float:
        for log in self.logs:
            if log.date == target_date:
                return log.value
        return 0.0

    def is_completed(self, target_date: date) -> bool:
        return self.get_progress(target_date) >= self.target


@dataclass
class HabitGroup(HabitComponent):
    id: str
    name: str
    description: str
    created_at: date = field(default_factory=date.today)
    habits: List[HabitComponent] = field(default_factory=list)

    def add(self, component: HabitComponent) -> None:
        self.habits.append(component)

    def get_progress(self, target_date: date) -> float:
        if not self.habits:
            return 0.0
        completed = sum(1 for h in self.habits if h.is_completed(target_date))
        return (completed / len(self.habits)) * 100

    def is_completed(self, target_date: date) -> bool:
        if not self.habits:
            return False
        return all(h.is_completed(target_date) for h in self.habits)
