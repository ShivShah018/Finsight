import logging
from datetime import date
from typing import Optional
from repositories.transaction_repository import TransactionRepository
from repositories.category_repository import CategoryRepository

logger = logging.getLogger(__name__)


class TransactionService:
    def __init__(self):
        self.tx_repo = TransactionRepository()
        self.cat_repo = CategoryRepository()

    def create(self, user_id: int, category_id: int, amount: float, tx_type: str,
               description: Optional[str], tx_date: date, currency: str = "INR",
               is_bill: bool = False) -> int:
        tx_id = self.tx_repo.create(user_id, category_id, amount, tx_type, description, tx_date, currency)
        if is_bill:
            self.tx_repo.mark_as_bill(tx_id, user_id)
        return tx_id

    def get_by_id(self, tx_id: int, user_id: int):
        return self.tx_repo.find_by_id(tx_id, user_id)

    def list_all(self, user_id: int, month: Optional[int] = None,
                 year: Optional[int] = None, limit: int = 100):
        return self.tx_repo.find_by_user(user_id, month, year, limit)

    def update(self, tx_id: int, user_id: int, **kwargs):
        existing = self.tx_repo.find_by_id(tx_id, user_id)
        if not existing:
            raise ValueError("Transaction not found")
        self.tx_repo.update(
            tx_id, user_id,
            kwargs.get("category_id", existing.category_id),
            kwargs.get("amount", existing.amount),
            kwargs.get("type", existing.type),
            kwargs.get("description", existing.description),
            kwargs.get("transaction_date", existing.transaction_date),
            kwargs.get("currency", existing.currency),
        )

    def delete(self, tx_id: int, user_id: int, soft: bool = True):
        if soft:
            self.tx_repo.soft_delete(tx_id, user_id)
        else:
            self.tx_repo.delete(tx_id, user_id)

    def restore(self, tx_id: int, user_id: int):
        self.tx_repo.restore(tx_id, user_id)

    def get_deleted(self, user_id: int):
        return self.tx_repo.get_deleted(user_id)

    def get_summary(self, user_id: int, month: Optional[int] = None, year: Optional[int] = None):
        return self.tx_repo.get_summary(user_id, month, year)

    def get_spending_by_category(self, user_id: int, month: Optional[int] = None, year: Optional[int] = None):
        return self.tx_repo.get_spending_by_category(user_id, month, year)

    def get_categories(self, user_id: int, cat_type: Optional[str] = None):
        return self.cat_repo.find_by_user(user_id, cat_type)
