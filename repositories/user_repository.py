import logging
from typing import Optional
from repositories.base import BaseRepository
from utils.db_manager import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    def create(self, full_name: str, email: str, password_hash: str) -> User:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                cursor.close()
                raise ValueError("Email already registered.")
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                (full_name, email, password_hash),
            )
            self.db.connection.commit()
            user_id = cursor.lastrowid
            self._seed_categories(user_id, cursor)
            cursor.execute(
                "SELECT id, full_name, email, currency, preferred_currency FROM users WHERE id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            return User(**row)
        finally:
            cursor.close()

    def find_by_email(self, email: str) -> Optional[User]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, full_name, email, currency, preferred_currency FROM users WHERE email = %s",
                (email,),
            )
            row = cursor.fetchone()
            return User(**row) if row else None
        finally:
            cursor.close()

    def find_by_id(self, user_id: int) -> Optional[User]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT id, full_name, email, currency, preferred_currency FROM users WHERE id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            return User(**row) if row else None
        finally:
            cursor.close()

    def get_password_hash(self, email: str) -> Optional[str]:
        cursor = self.db.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT password_hash FROM users WHERE email = %s",
                (email,),
            )
            row = cursor.fetchone()
            return row["password_hash"] if row else None
        finally:
            cursor.close()

    def update_preferred_currency(self, user_id: int, currency: str) -> None:
        cursor = self.db.connection.cursor()
        try:
            cursor.execute(
                "UPDATE users SET preferred_currency = %s WHERE id = %s",
                (currency, user_id),
            )
            self.db.connection.commit()
        finally:
            cursor.close()

    def _seed_categories(self, user_id: int, cursor) -> None:
        from utils.db_manager import DEFAULT_INCOME_CATEGORIES, DEFAULT_EXPENSE_CATEGORIES
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
        self.db.connection.commit()
