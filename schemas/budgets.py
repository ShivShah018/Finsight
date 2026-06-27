from pydantic import BaseModel, Field
from typing import Optional


class BudgetCreate(BaseModel):
    category_id: int
    monthly_limit: float = Field(gt=0)


class BudgetResponse(BaseModel):
    id: int
    category_id: int
    category_name: str
    monthly_limit: float


class BudgetUpdate(BaseModel):
    monthly_limit: float = Field(gt=0)
