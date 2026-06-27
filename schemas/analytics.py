from pydantic import BaseModel
from typing import Optional
from datetime import date


class CategoryBreakdown(BaseModel):
    name: str
    color: str
    icon: str
    total: float
    percentage: float


class MonthlyTrend(BaseModel):
    month: str
    income: float
    expense: float
    net: float


class DashboardSummary(BaseModel):
    total_income: float
    total_expense: float
    net_savings: float
    savings_rate: float
    avg_daily_spending: float
    top_categories: list[CategoryBreakdown]
    monthly_trends: list[MonthlyTrend]
    budget_utilization: Optional[dict] = None
    largest_expenses: Optional[list[dict]] = None
    income_expense_ratio: float
