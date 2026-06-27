import logging
from typing import Optional
from datetime import date
from repositories.base import BaseRepository
from utils.db_manager import TransactionRow

logger = logging.getLogger(__name__)


class TransactionRepository(BaseRepository):
    def create(self, user_id: int, category_id: int, amount: float, tx_type: str,
               description: Optional[str], tx_date: date, currency: str = "INR") -> int:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO transactions (user_id, category_id, amount, type, currency, description, transaction_date) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (user_id, category_id, amount, tx_type, currency, description, tx_date),
            )
            self.db.connection.commit()
            return cursor.lastrowid
        finally:
            cursor.close()

    def find_by_id(self, transaction_id: int, user_id: int) -> Optional[TransactionRow]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT t.id, t.category_id, c.name AS category_name, "
                "t.amount, t.type, t.currency, t.description, t.transaction_date "
                "FROM transactions t JOIN categories c ON t.category_id = c.id "
                "WHERE t.id = %s AND t.user_id = %s",
                (transaction_id, user_id),
            )
            row = cursor.fetchone()
            return TransactionRow(**row) if row else None
        finally:
            cursor.close()

    def find_by_user(self, user_id: int, month: Optional[int] = None,
                     year: Optional[int] = None, limit: int = 100) -> list[TransactionRow]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            query = (
                "SELECT t.id, t.category_id, c.name AS category_name, "
                "t.amount, t.type, t.currency, t.description, t.transaction_date "
                "FROM transactions t JOIN categories c ON t.category_id = c.id "
                "WHERE t.user_id = %s"
            )
            params = [user_id]
            if month and year:
                query += " AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s"
                params.extend([year, month])
            query += " AND t.deleted_at IS NULL ORDER BY t.transaction_date DESC, t.created_at DESC LIMIT %s"
            params.append(limit)
            cursor.execute(query, params)
            results = []
            for r in cursor.fetchall():
                r["amount"] = float(r["amount"])
                results.append(TransactionRow(**r))
            return results
        finally:
            cursor.close()

    def update(self, transaction_id: int, user_id: int, category_id: int, amount: float,
               tx_type: str, description: Optional[str], tx_date: date, currency: str = "INR") -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE transactions SET category_id=%s, amount=%s, type=%s, "
                "currency=%s, description=%s, transaction_date=%s "
                "WHERE id=%s AND user_id=%s",
                (category_id, amount, tx_type, currency, description, tx_date, transaction_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def delete(self, transaction_id: int, user_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM transactions WHERE id = %s AND user_id = %s",
                (transaction_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def soft_delete(self, transaction_id: int, user_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE transactions SET deleted_at = NOW() WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (transaction_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def restore(self, transaction_id: int, user_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE transactions SET deleted_at = NULL WHERE id = %s AND user_id = %s",
                (transaction_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def get_deleted(self, user_id: int) -> list[TransactionRow]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT t.id, t.category_id, c.name AS category_name, "
                "t.amount, t.type, t.currency, t.description, t.transaction_date "
                "FROM transactions t JOIN categories c ON t.category_id = c.id "
                "WHERE t.user_id = %s AND t.deleted_at IS NOT NULL "
                "ORDER BY t.deleted_at DESC LIMIT 20",
                (user_id,),
            )
            results = []
            for r in cursor.fetchall():
                r["amount"] = float(r["amount"])
                results.append(TransactionRow(**r))
            return results
        finally:
            cursor.close()

    def mark_as_bill(self, transaction_id: int, user_id: int) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE transactions SET is_bill = 1 WHERE id = %s AND user_id = %s",
                (transaction_id, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def get_summary(self, user_id: int, month: Optional[int] = None,
                    year: Optional[int] = None) -> dict:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            where = "WHERE user_id = %s"
            params = [user_id]
            if month and year:
                where += " AND YEAR(transaction_date) = %s AND MONTH(transaction_date) = %s"
                params.extend([year, month])
            cursor.execute(
                f"SELECT type, COALESCE(SUM(amount), 0) AS total FROM transactions {where} AND deleted_at IS NULL GROUP BY type",
                params,
            )
            totals = {"income": 0.0, "expense": 0.0}
            for r in cursor.fetchall():
                totals[r["type"]] = float(r["total"])
            totals["net"] = round(totals["income"] - totals["expense"], 2)
            return totals
        finally:
            cursor.close()

    def get_spending_by_category(self, user_id: int, month: Optional[int] = None,
                                  year: Optional[int] = None) -> list[dict]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            where = "WHERE t.user_id = %s AND t.type = 'expense' AND t.deleted_at IS NULL"
            params = [user_id]
            if month and year:
                where += " AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s"
                params.extend([year, month])
            cursor.execute(
                f"SELECT c.name, c.color, c.icon, COALESCE(SUM(t.amount), 0) AS total "
                f"FROM transactions t JOIN categories c ON t.category_id = c.id "
                f"{where} GROUP BY c.id ORDER BY total DESC",
                params,
            )
            return cursor.fetchall()
        finally:
            cursor.close()

    def get_monthly_trends(self, user_id: int, months: int = 12) -> list[dict]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT DATE_FORMAT(transaction_date, '%Y-%m') AS month, "
                "COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE 0 END), 0) AS income, "
                "COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS expense "
                "FROM transactions WHERE user_id = %s AND deleted_at IS NULL "
                "AND transaction_date >= DATE_SUB(CURDATE(), INTERVAL %s MONTH) "
                "GROUP BY DATE_FORMAT(transaction_date, '%Y-%m') ORDER BY month",
                (user_id, months),
            )
            results = []
            for r in cursor.fetchall():
                r["income"] = float(r["income"])
                r["expense"] = float(r["expense"])
                results.append(r)
            return results
        finally:
            cursor.close()

    def get_largest_expenses(self, user_id: int, limit: int = 5) -> list[dict]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT t.id, t.amount, t.description, t.transaction_date, c.name AS category_name "
                "FROM transactions t JOIN categories c ON t.category_id = c.id "
                "WHERE t.user_id = %s AND t.type = 'expense' AND t.deleted_at IS NULL "
                "ORDER BY t.amount DESC LIMIT %s",
                (user_id, limit),
            )
            results = []
            for r in cursor.fetchall():
                r["amount"] = float(r["amount"])
                results.append(r)
            return results
        finally:
            cursor.close()
