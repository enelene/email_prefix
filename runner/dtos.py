from pydantic import BaseModel, Field
from typing import Optional
from core.domain.enums import Category, HabitType


class CreateHabitRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the habit")
    description: str = Field(..., description="Short description")
    category: Category = Field(
        default=Category.HEALTH, description="Category of the habit"
    )
    habit_type: HabitType = Field(
        default=HabitType.BOOLEAN, description="Type of tracking"
    )
    target: float = Field(
        default=1.0, gt=0, description="Target value (e.g., 1.0 for Yes/No, 5.0 for km)"
    )
    is_group: bool = Field(
        default=False, description="Set to True if this is a Routine/Group"
    )


class UpdateHabitRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target: Optional[float] = None


class LogRequest(BaseModel):
    value: float = Field(
        ..., description="Amount to log (e.g., 1.0 for done, 0.5 for half)"
    )


class OperationResponse(BaseModel):
    status: str
    message: Optional[str] = None
