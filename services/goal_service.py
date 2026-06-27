import logging
from datetime import date
from typing import Optional
from repositories.goal_repository import GoalRepository

logger = logging.getLogger(__name__)


class GoalService:
    def __init__(self):
        self.goal_repo = GoalRepository()

    def create(self, user_id: int, name: str, target_amount: float,
               deadline: Optional[date] = None,
               auto_fund_amount: float = 0,
               auto_fund_category_id: Optional[int] = None) -> int:
        gid = self.goal_repo.create(user_id, name, target_amount, deadline)
        if auto_fund_amount > 0:
            self.goal_repo.set_auto_fund(gid, user_id, auto_fund_amount, auto_fund_category_id)
        return gid

    def list_all(self, user_id: int):
        return self.goal_repo.find_by_user(user_id)

    def add_funds(self, goal_id: int, amount: float):
        self.goal_repo.add_funds(goal_id, amount)

    def complete(self, goal_id: int):
        self.goal_repo.complete(goal_id)

    def cancel(self, goal_id: int):
        self.goal_repo.cancel(goal_id)
