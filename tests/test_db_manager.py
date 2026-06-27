"""Tests for DatabaseManager with a real MySQL connection (requires finsight DB)."""
import os
import pytest
from datetime import date, timedelta
from utils.db_manager import DatabaseManager, BudgetLimit
from utils.config_manager import load_env

load_env()

pytestmark = pytest.mark.skipif(
    not os.getenv("FINSIGHT_DB_PASSWORD"),
    reason="FINSIGHT_DB_PASSWORD not set",
)


def test_db_connect():
    db = DatabaseManager.get_instance()
    db.connect()
    assert db._conn is not None
    assert db._conn.is_connected()
    db.disconnect()


def test_user_register_and_auth():
    db = DatabaseManager.get_instance()
    import random
    suffix = random.randint(10000, 99999)
    email = f"test{suffix}@example.com"
    user = db.register_user("Test User", email, "testpass123")
    assert user.id > 0
    assert user.full_name == "Test User"

    authed = db.authenticate_user(email, "testpass123")
    assert authed is not None
    assert authed.id == user.id

    bad = db.authenticate_user(email, "wrongpass")
    assert bad is None

    with pytest.raises(ValueError, match="Email already registered"):
        db.register_user("Dup", email, "pass")


def test_categories_seeded():
    db = DatabaseManager.get_instance()
    import random
    suffix = random.randint(10000, 99999)
    user = db.register_user("Cat Test", f"cat{suffix}@example.com", "pass")
    cats = db.get_categories(user.id)
    assert len(cats) > 0
    income_cats = db.get_categories(user.id, "income")
    expense_cats = db.get_categories(user.id, "expense")
    assert len(income_cats) >= 1
    assert len(expense_cats) >= 1


def test_transaction_crud():
    db = DatabaseManager.get_instance()
    import random
    suffix = random.randint(10000, 99999)
    user = db.register_user("Tx Test", f"tx{suffix}@example.com", "pass")
    cats = db.get_categories(user.id, "expense")
    cat = cats[0]

    tx_id = db.add_transaction(user.id, cat.id, 500.0, "expense", "Test tx",
                                date.today(), "INR")
    assert tx_id > 0

    txs = db.get_transactions(user.id, limit=50)
    assert any(t.id == tx_id for t in txs)

    tx = db.get_transaction_by_id(tx_id, user.id)
    assert tx is not None
    assert tx.amount == 500.0
    assert tx.description == "Test tx"

    db.update_transaction(tx_id, user.id, cat.id, 750.0, "expense",
                          "Updated", date.today(), "INR")
    tx = db.get_transaction_by_id(tx_id, user.id)
    assert tx.amount == 750.0

    db.delete_transaction(tx_id, user.id)
    assert db.get_transaction_by_id(tx_id, user.id) is None


def test_budget_limits():
    db = DatabaseManager.get_instance()
    import random
    suffix = random.randint(10000, 99999)
    user = db.register_user("Budget Test", f"budget{suffix}@example.com", "pass")
    cats = db.get_categories(user.id, "expense")
    cat = cats[0]

    db.set_budget_limit(user.id, cat.id, 5000.0)
    budgets = db.get_budget_limits(user.id)
    assert len(budgets) >= 1
    match = [b for b in budgets if b.category_id == cat.id]
    assert len(match) == 1
    assert match[0].monthly_limit == 5000.0

    bl = match[0]
    db.update_budget_limit(bl.id, user.id, 6000.0)
    budgets = db.get_budget_limits(user.id)
    match = [b for b in budgets if b.id == bl.id]
    assert match[0].monthly_limit == 6000.0

    db.delete_budget_limit(bl.id, user.id)
    budgets = db.get_budget_limits(user.id)
    assert all(b.id != bl.id for b in budgets)


def test_recurring():
    db = DatabaseManager.get_instance()
    import random
    suffix = random.randint(10000, 99999)
    user = db.register_user("Recur Test", f"recur{suffix}@example.com", "pass")
    cats = db.get_categories(user.id, "expense")
    cat = cats[0]

    rid = db.add_recurring(user.id, cat.id, 1000.0, "expense",
                           "Monthly rent", "INR", "monthly", date.today())
    assert rid > 0

    due = db.get_due_recurring(user.id)
    assert len(due) >= 1

    next_due = date.today() + timedelta(days=30)
    db.update_recurring_next_date(rid, next_due)
    due = db.get_due_recurring(user.id)
    assert all(d["id"] != rid for d in due)
