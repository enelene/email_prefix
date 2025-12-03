from enum import Enum


class HabitType(str, Enum):
    """Defines how a habit is measured."""

    BOOLEAN = "boolean"  # Simple Done/Not Done (1.0 or 0.0)
    NUMERIC = "numeric"  # Measurable quantities (e.g., 5.0 km)


class Category(str, Enum):
    """Categories for organizing habits."""

    HEALTH = "health"
    LEARNING = "learning"
    PRODUCTIVITY = "productivity"
