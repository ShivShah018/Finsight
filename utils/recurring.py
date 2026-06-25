"""Check and process recurring transactions on startup."""
from datetime import date, timedelta
from utils.db_manager import DatabaseManager


def process_recurring_transactions(user_id: int) -> int:
    """
    Process all due recurring transactions for a user.
    Returns the number of transactions created.
    """
    db = DatabaseManager.get_instance()
    recurring = db.get_due_recurring(user_id)
    count = 0
    for r in recurring:
        db.add_transaction(
            user_id=user_id,
            category_id=r["category_id"],
            amount=r["amount"],
            tx_type=r["type"],
            description=f"[Auto] {r['description'] or r['category_name']}",
            tx_date=date.today(),
            currency=r["currency"],
        )
        # Calculate next due date
        next_date = r["next_due_date"]
        if r["frequency"] == "monthly":
            m = next_date.month + 1
            y = next_date.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            try:
                next_date = date(y, m, next_date.day)
            except ValueError:
                next_date = date(y, m, 1) + timedelta(days=28)
        elif r["frequency"] == "weekly":
            next_date = next_date + timedelta(days=7)
        elif r["frequency"] == "yearly":
            next_date = date(next_date.year + 1, next_date.month, next_date.day)

        db.update_recurring_next_date(r["id"], next_date)
        count += 1
    return count
