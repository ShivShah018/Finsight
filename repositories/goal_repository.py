import logging
from typing import Optional
from datetime import date
from repositories.base import BaseRepository
from utils.db_manager import SavingsGoal

logger = logging.getLogger(__name__)


class GoalRepository(BaseRepository):
    def create(self, user_id: int, name: str, target_amount: float,
               deadline: Optional[date] = None) -> int:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO savings_goals (user_id, name, target_amount, deadline) VALUES (%s, %s, %s, %s)",
                (user_id, name, target_amount, deadline),
            )
            self.db.connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def find_by_user(self, user_id: int) -> list[SavingsGoal]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, name, target_amount, current_amount, deadline, status "
                "FROM savings_goals WHERE user_id = %s AND status != 'cancelled' ORDER BY created_at DESC",
                (user_id,),
            )
            goals = []
            for r in cursor.fetchall():
                r["target_amount"] = float(r["target_amount"])
                r["current_amount"] = float(r["current_amount"])
                pct = (r["current_amount"] / r["target_amount"]) * 100 if r["target_amount"] > 0 else 0
                r["progress_pct"] = round(min(pct, 100), 1)
                goals.append(SavingsGoal(**r))
            return goals
        finally:
            cursor.close()

    def add_funds(self, goal_id: int, amount: float) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE savings_goals SET current_amount = current_amount + %s WHERE id = %s AND status = 'active'",
                (amount, goal_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def complete(self, goal_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE savings_goals SET status = 'completed', current_amount = target_amount WHERE id = %s",
                (goal_id,),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def cancel(self, goal_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE savings_goals SET status = 'cancelled' WHERE id = %s",
                (goal_id,),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def set_auto_fund(self, goal_id: int, user_id: int,
                       amount: float, category_id: Optional[int] = None) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE savings_goals SET auto_fund_amount = %s, auto_fund_category_id = %s "
                "WHERE id = %s AND user_id = %s",
                (amount, category_id, goal_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()
