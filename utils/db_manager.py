"""
Database connection manager for FinSight.
Handles connections, user auth, categories, transactions & savings goals.
"""

import os
import hashlib
import mysql.connector
from mysql.connector import Error
from dataclasses import dataclass
from typing import Optional
from datetime import date, datetime

# ── Config ─────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("FINSIGHT_DB_HOST", "localhost"),
    "user": os.getenv("FINSIGHT_DB_USER", "root"),
    "password": os.getenv("FINSIGHT_DB_PASSWORD", ""),
    "database": os.getenv("FINSIGHT_DB_NAME", "finsight"),
}


# ── Data classes ───────────────────────────────────────────────
@dataclass
class User:
    id: int
    full_name: str
    email: str
    currency: str
    preferred_currency: str = "INR"


@dataclass
class Category:
    id: int
    name: str
    type: str  # 'income' | 'expense'
    icon: str
    color: str


@dataclass
class TransactionRow:
    id: int
    category_id: int
    category_name: str
    amount: float
    type: str
    description: Optional[str]
    transaction_date: date
    currency: str = "INR"


@dataclass
class BudgetLimit:
    id: int
    category_id: int
    category_name: str
    monthly_limit: float


@dataclass
class SavingsGoal:
    id: int
    name: str
    target_amount: float
    current_amount: float
    deadline: Optional[date]
    status: str
    progress_pct: float = 0.0


# ── Default categories (seeded on registration) ────────────────
DEFAULT_INCOME_CATEGORIES = [
    ("Salary",         "\U0001F4B0", "#22c55e"),
    ("Freelance",      "\U0001F4BB", "#3b82f6"),
    ("Investments",    "\U0001F4C8", "#a855f7"),
    ("Other Income",   "\U0001F4B5", "#06b6d4"),
]

DEFAULT_EXPENSE_CATEGORIES = [
    ("Food & Dining",  "\U0001F372", "#ef4444"),
    ("Rent",           "\U0001F3E0", "#f97316"),
    ("Transport",      "\U0001F697", "#eab308"),
    ("Utilities",      "\U0001F4A1", "#64748b"),
    ("Entertainment",  "\U0001F3AC", "#ec4899"),
    ("Healthcare",     "\U0001F3E5", "#14b8a6"),
    ("Shopping",       "\U0001F6CD", "#8b5cf6"),
    ("Education",      "\U0001F4DA", "#6366f1"),
    ("Other",          "\U0001F4C2", "#78716c"),
]


class DatabaseManager:
    """Singleton-style DB manager. Call get_instance() to use."""

    _instance: Optional["DatabaseManager"] = None

    def __init__(self):
        self._conn: Optional[mysql.connector.MySQLConnection] = None

    # ── Connection ─────────────────────────────────────────────
    @classmethod
    def get_instance(cls) -> "DatabaseManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def connect(self) -> None:
        """Open connection if not already open."""
        if self._conn and self._conn.is_connected():
            return
        try:
            self._conn = mysql.connector.connect(**DB_CONFIG)
        except Error as e:
            raise RuntimeError(f"Cannot connect to MySQL: {e}") from e

    def disconnect(self) -> None:
        if self._conn and self._conn.is_connected():
            self._conn.close()
            self._conn = None

    @property
    def connection(self):
        self.connect()
        return self._conn

    # ── Hashing ────────────────────────────────────────────────
    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    # ── User operations ────────────────────────────────────────
    def register_user(self, full_name: str, email: str,
                      password: str) -> User:
        """Create a new user and seed default categories. Returns User."""
        self.connect()
        cursor = self.connection.cursor(dictionary=True)

        # Check email uniqueness
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            raise ValueError("Email already registered.")

        password_hash = self._hash_password(password)
        cursor.execute(
            "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
            (full_name, email, password_hash),
        )
        self.connection.commit()
        user_id = cursor.lastrowid

        # Seed default categories
        self._seed_categories(user_id, cursor)

        cursor.execute(
            "SELECT id, full_name, email, currency, preferred_currency FROM users WHERE id = %s",
            (user_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return User(**row)

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Returns User if credentials match, else None."""
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, full_name, email, currency, preferred_currency FROM users "
            "WHERE email = %s AND password_hash = %s",
            (email, self._hash_password(password)),
        )
        row = cursor.fetchone()
        cursor.close()
        return User(**row) if row else None

    def update_preferred_currency(self, user_id: int, currency: str) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE users SET preferred_currency = %s WHERE id = %s",
            (currency, user_id),
        )
        self.connection.commit()
        cursor.close()

    # ── Categories ─────────────────────────────────────────────
    def _seed_categories(self, user_id: int, cursor) -> None:
        for name, icon, color in DEFAULT_INCOME_CATEGORIES:
            cursor.execute(
                "INSERT INTO categories (user_id, name, type, icon, color) VALUES (%s, %s, 'income', %s, %s)",
                (user_id, name, icon, color),
            )
        for name, icon, color in DEFAULT_EXPENSE_CATEGORIES:
            cursor.execute(
                "INSERT INTO categories (user_id, name, type, icon, color) VALUES (%s, %s, 'expense', %s, %s)",
                (user_id, name, icon, color),
            )
        self.connection.commit()

    def get_categories(self, user_id: int,
                       cat_type: Optional[str] = None) -> list[Category]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        if cat_type:
            cursor.execute(
                "SELECT id, name, type, icon, color FROM categories WHERE user_id = %s AND type = %s ORDER BY name",
                (user_id, cat_type),
            )
        else:
            cursor.execute(
                "SELECT id, name, type, icon, color FROM categories WHERE user_id = %s ORDER BY type, name",
                (user_id,),
            )
        rows = cursor.fetchall()
        cursor.close()
        return [Category(**r) for r in rows]

    # ── Transactions ───────────────────────────────────────────
    def add_transaction(self, user_id: int, category_id: int,
                        amount: float, tx_type: str,
                        description: Optional[str],
                        tx_date: date,
                        currency: str = "INR") -> int:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO transactions (user_id, category_id, amount, type, currency, description, transaction_date) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, category_id, amount, tx_type, currency, description, tx_date),
        )
        self.connection.commit()
        tx_id = cursor.lastrowid
        cursor.close()
        return tx_id

    def delete_transaction(self, transaction_id: int, user_id: int) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM transactions WHERE id = %s AND user_id = %s",
            (transaction_id, user_id),
        )
        self.connection.commit()
        cursor.close()

    def update_transaction(self, transaction_id: int, user_id: int,
                           category_id: int, amount: float, tx_type: str,
                           description: Optional[str],
                           tx_date: date, currency: str = "INR") -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE transactions SET category_id=%s, amount=%s, type=%s, "
            "currency=%s, description=%s, transaction_date=%s "
            "WHERE id=%s AND user_id=%s",
            (category_id, amount, tx_type, currency, description,
             tx_date, transaction_id, user_id),
        )
        self.connection.commit()
        cursor.close()

    def get_transaction_by_id(self, transaction_id: int, user_id: int) -> Optional[TransactionRow]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT t.id, t.category_id, c.name AS category_name, "
            "t.amount, t.type, t.currency, t.description, t.transaction_date "
            "FROM transactions t "
            "JOIN categories c ON t.category_id = c.id "
            "WHERE t.id = %s AND t.user_id = %s",
            (transaction_id, user_id),
        )
        row = cursor.fetchone()
        cursor.close()
        return TransactionRow(**row) if row else None

    def get_transactions(self, user_id: int,
                         month: Optional[int] = None,
                         year: Optional[int] = None,
                         limit: int = 100) -> list[TransactionRow]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        query = (
            "SELECT t.id, t.category_id, c.name AS category_name, "
            "t.amount, t.type, t.currency, t.description, t.transaction_date "
            "FROM transactions t "
            "JOIN categories c ON t.category_id = c.id "
            "WHERE t.user_id = %s"
        )
        params = [user_id]

        if month and year:
            query += " AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s"
            params.extend([year, month])

        query += " ORDER BY t.transaction_date DESC, t.created_at DESC LIMIT %s"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return [TransactionRow(**r) for r in rows]

    def get_summary(self, user_id: int,
                    month: Optional[int] = None,
                    year: Optional[int] = None) -> dict:
        """Return total_income, total_expense, net_savings for a period."""
        self.connect()
        cursor = self.connection.cursor(dictionary=True)

        where = "WHERE user_id = %s"
        params = [user_id]
        if month and year:
            where += " AND YEAR(transaction_date) = %s AND MONTH(transaction_date) = %s"
            params.extend([year, month])

        cursor.execute(
            f"SELECT type, COALESCE(SUM(amount), 0) AS total FROM transactions {where} GROUP BY type",
            params,
        )
        rows = cursor.fetchall()
        cursor.close()

        totals = {"income": 0.0, "expense": 0.0}
        for r in rows:
            totals[r["type"]] = float(r["total"])
        totals["net"] = round(totals["income"] - totals["expense"], 2)
        return totals

    def get_spending_by_category(self, user_id: int,
                                 month: Optional[int] = None,
                                 year: Optional[int] = None) -> list[dict]:
        """Expense breakdown by category for a pie/bar chart."""
        self.connect()
        cursor = self.connection.cursor(dictionary=True)

        where = "WHERE t.user_id = %s AND t.type = 'expense'"
        params = [user_id]
        if month and year:
            where += " AND YEAR(t.transaction_date) = %s AND MONTH(t.transaction_date) = %s"
            params.extend([year, month])

        cursor.execute(
            f"SELECT c.name, c.color, c.icon, COALESCE(SUM(t.amount), 0) AS total "
            f"FROM transactions t "
            f"JOIN categories c ON t.category_id = c.id "
            f"{where} GROUP BY c.id ORDER BY total DESC",
            params,
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    # ── Savings Goals ─────────────────────────────────────────
    def add_goal(self, user_id: int, name: str,
                 target_amount: float,
                 deadline: Optional[date] = None) -> int:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO savings_goals (user_id, name, target_amount, deadline) VALUES (%s, %s, %s, %s)",
            (user_id, name, target_amount, deadline),
        )
        self.connection.commit()
        gid = cursor.lastrowid
        cursor.close()
        return gid

    def get_goals(self, user_id: int) -> list[SavingsGoal]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, target_amount, current_amount, deadline, status "
            "FROM savings_goals WHERE user_id = %s AND status != 'cancelled' ORDER BY created_at DESC",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        goals = []
        for r in rows:
            r["target_amount"] = float(r["target_amount"])
            r["current_amount"] = float(r["current_amount"])
            pct = (r["current_amount"] / r["target_amount"]) * 100 if r["target_amount"] > 0 else 0
            r["progress_pct"] = round(min(pct, 100), 1)
            goals.append(SavingsGoal(**r))
        return goals

    def update_goal_progress(self, goal_id: int, additional_amount: float) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE savings_goals SET current_amount = current_amount + %s WHERE id = %s AND status = 'active'",
            (additional_amount, goal_id),
        )
        self.connection.commit()
        cursor.close()

    def complete_goal(self, goal_id: int) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE savings_goals SET status = 'completed', current_amount = target_amount WHERE id = %s",
            (goal_id,),
        )
        self.connection.commit()
        cursor.close()

    def cancel_goal(self, goal_id: int) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE savings_goals SET status = 'cancelled' WHERE id = %s",
            (goal_id,),
        )
        self.connection.commit()
        cursor.close()

    # ── Budget Limits ─────────────────────────────────────────
    def set_budget_limit(self, user_id: int, category_id: int, monthly_limit: float) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO budget_limits (user_id, category_id, monthly_limit) VALUES (%s, %s, %s) "
            "ON DUPLICATE KEY UPDATE monthly_limit = %s",
            (user_id, category_id, monthly_limit, monthly_limit),
        )
        self.connection.commit()
        cursor.close()

    def update_budget_limit(self, budget_id: int, user_id: int, monthly_limit: float) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE budget_limits SET monthly_limit = %s WHERE id = %s AND user_id = %s",
            (monthly_limit, budget_id, user_id),
        )
        self.connection.commit()
        cursor.close()

    def delete_budget_limit(self, budget_id: int, user_id: int) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "DELETE FROM budget_limits WHERE id = %s AND user_id = %s",
            (budget_id, user_id),
        )
        self.connection.commit()
        cursor.close()

    def get_budget_limits(self, user_id: int) -> list[BudgetLimit]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT b.id, b.category_id, c.name AS category_name, b.monthly_limit "
            "FROM budget_limits b JOIN categories c ON b.category_id = c.id "
            "WHERE b.user_id = %s ORDER BY c.name",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return [BudgetLimit(**r) for r in rows]

    # ── Recurring Transactions ─────────────────────────────────
    def add_recurring(self, user_id: int, category_id: int, amount: float,
                      tx_type: str, description: Optional[str], currency: str,
                      frequency: str, next_due_date: date) -> int:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "INSERT INTO recurring_transactions (user_id, category_id, amount, type, "
            "description, currency, frequency, next_due_date) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (user_id, category_id, amount, tx_type, description, currency, frequency, next_due_date),
        )
        self.connection.commit()
        rid = cursor.lastrowid
        cursor.close()
        return rid

    def get_due_recurring(self, user_id: int) -> list[dict]:
        self.connect()
        cursor = self.connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT r.id, r.category_id, r.amount, r.type, r.description, "
            "r.currency, r.frequency, r.next_due_date, c.name AS category_name "
            "FROM recurring_transactions r "
            "JOIN categories c ON r.category_id = c.id "
            "WHERE r.user_id = %s AND r.is_active = 1 AND r.next_due_date <= CURDATE()",
            (user_id,),
        )
        rows = cursor.fetchall()
        cursor.close()
        return rows

    def update_recurring_next_date(self, recurring_id: int, next_date: date) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE recurring_transactions SET next_due_date = %s WHERE id = %s",
            (next_date, recurring_id),
        )
        self.connection.commit()
        cursor.close()

    # ── Receipt ────────────────────────────────────────────────
    def update_receipt_path(self, transaction_id: int, user_id: int, path: Optional[str]) -> None:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "UPDATE transactions SET receipt_path = %s WHERE id = %s AND user_id = %s",
            (path, transaction_id, user_id),
        )
        self.connection.commit()
        cursor.close()

    def get_receipt_path(self, transaction_id: int) -> Optional[str]:
        self.connect()
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT receipt_path FROM transactions WHERE id = %s",
            (transaction_id,),
        )
        row = cursor.fetchone()
        cursor.close()
        return row[0] if row else None
