import logging
from datetime import date, timedelta
from repositories.transaction_repository import TransactionRepository
from repositories.goal_repository import GoalRepository
from repositories.budget_repository import BudgetRepository

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self):
        self.tx_repo = TransactionRepository()
        self.goal_repo = GoalRepository()
        self.budget_repo = BudgetRepository()

    def get_dashboard(self, user_id: int, month: int = None, year: int = None):
        today = date.today()
        month = month or today.month
        year = year or today.year

        summary = self.tx_repo.get_summary(user_id, month, year)
        categories = self.tx_repo.get_spending_by_category(user_id, month, year)
        trends = self.tx_repo.get_monthly_trends(user_id, 12)
        largest = self.tx_repo.get_largest_expenses(user_id, 5)

        income = summary["income"]
        expense = summary["expense"]
        total_days = date(year, month, 1).replace(day=28).day

        return {
            "total_income": income,
            "total_expense": expense,
            "net_savings": summary["net"],
            "savings_rate": round((income - expense) / income * 100, 2) if income > 0 else 0,
            "avg_daily_spending": round(expense / total_days, 2) if total_days > 0 else 0,
            "top_categories": [
                {"name": c["name"], "color": c["color"], "icon": c["icon"],
                 "total": float(c["total"]),
                 "percentage": round(float(c["total"]) / expense * 100, 2) if expense > 0 else 0}
                for c in categories
            ],
            "monthly_trends": [
                {"month": t["month"], "income": t["income"], "expense": t["expense"],
                 "net": t["income"] - t["expense"]}
                for t in trends
            ],
            "budget_utilization": self.budget_repo.get_utilization(user_id, month, year),
            "largest_expenses": largest,
            "income_expense_ratio": round(income / expense, 2) if expense > 0 else float("inf"),
        }

    def get_monthly_trends(self, user_id: int, months: int = 12):
        return self.tx_repo.get_monthly_trends(user_id, months)

    def get_export_data(self, user_id: int):
        txs = self.tx_repo.find_by_user(user_id, limit=5000)
        goals = self.goal_repo.find_by_user(user_id)
        budgets = self.budget_repo.find_by_user(user_id)
        summary = self.tx_repo.get_summary(user_id)
        return {"transactions": txs, "goals": goals, "budgets": budgets, "summary": summary}
