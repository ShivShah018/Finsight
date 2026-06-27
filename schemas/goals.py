from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date


class GoalCreate(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    deadline: Optional[date] = None
    auto_fund_amount: float = 0
    auto_fund_category_id: Optional[int] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Goal name is required")
        return v

    @field_validator("deadline")
    @classmethod
    def validate_deadline(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v <= date.today():
            raise ValueError("Deadline must be in the future")
        return v


class GoalResponse(BaseModel):
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[date] = None
    status: str
    progress_pct: float = 0.0


class GoalFundRequest(BaseModel):
    amount: float = Field(gt=0)
