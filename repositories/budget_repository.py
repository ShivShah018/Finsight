import logging
from repositories.base import BaseRepository
from utils.db_manager import BudgetLimit

logger = logging.getLogger(__name__)


class BudgetRepository(BaseRepository):
    def set_limit(self, user_id: int, category_id: int, monthly_limit: float) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO budget_limits (user_id, category_id, monthly_limit) VALUES (%s, %s, %s) "
                "ON DUPLICATE KEY UPDATE monthly_limit = %s",
                (user_id, category_id, monthly_limit, monthly_limit),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def update_limit(self, budget_id: int, user_id: int, monthly_limit: float) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE budget_limits SET monthly_limit = %s WHERE id = %s AND user_id = %s",
                (monthly_limit, budget_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def delete(self, budget_id: int, user_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM budget_limits WHERE id = %s AND user_id = %s",
                (budget_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def find_by_user(self, user_id: int) -> list[BudgetLimit]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT b.id, b.category_id, c.name AS category_name, b.monthly_limit "
                "FROM budget_limits b JOIN categories c ON b.category_id = c.id "
                "WHERE b.user_id = %s ORDER BY c.name",
                (user_id,),
            )
            results = []
            for r in cursor.fetchall():
                r["monthly_limit"] = float(r["monthly_limit"])
                results.append(BudgetLimit(**r))
            return results
        finally:
            cursor.close()

    def get_utilization(self, user_id: int, month: int, year: int) -> dict:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT b.id, b.monthly_limit, c.name AS category_name, "
                "COALESCE(SUM(t.amount), 0) AS spent "
                "FROM budget_limits b "
                "JOIN categories c ON b.category_id = c.id "
                "LEFT JOIN transactions t ON t.category_id = c.id "
                "AND t.user_id = %s AND t.type = 'expense' AND t.deleted_at IS NULL "
                "AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s "
                "WHERE b.user_id = %s GROUP BY b.id, b.monthly_limit, c.name",
                (user_id, year, month, user_id),
            )
            result = {}
            for r in cursor.fetchall():
                result[r["category_name"]] = {
                    "limit": float(r["monthly_limit"]),
                    "spent": float(r["spent"]),
                    "percentage": round(float(r["spent"]) / float(r["monthly_limit"]) * 100, 1) if float(r["monthly_limit"]) > 0 else 0,
                }
            return result
        finally:
            cursor.close()
