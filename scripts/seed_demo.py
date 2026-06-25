"""Seed demo transactions and goals for screenshot capture."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import DatabaseManager
from datetime import date, timedelta
import random

DEMO_EMAIL = "demo@finsight.app"
DEMO_PASSWORD = "demo123"

db = DatabaseManager.get_instance()
db.connect()

# Register demo user if not exists
try:
    user = db.register_user("Demo User", DEMO_EMAIL, DEMO_PASSWORD)
    print(f"Created demo user: {user.full_name} (id={user.id})")
except ValueError:
    user = db.authenticate_user(DEMO_EMAIL, DEMO_PASSWORD)
    print(f"Demo user already exists (id={user.id})")

cats = db.get_categories(user.id)
cat_map = {c.name: c for c in cats}

# Seed transactions over last 45 days
tx_data = [
    ("expense", "Food & Dining", 450.0),
    ("expense", "Food & Dining", 320.0),
    ("expense", "Food & Dining", 580.0),
    ("expense", "Rent", 15000.0),
    ("expense", "Rent", 15000.0),
    ("expense", "Transport", 250.0),
    ("expense", "Transport", 180.0),
    ("expense", "Transport", 420.0),
    ("expense", "Utilities", 2000.0),
    ("expense", "Utilities", 1800.0),
    ("expense", "Entertainment", 1200.0),
    ("expense", "Entertainment", 800.0),
    ("expense", "Shopping", 3500.0),
    ("expense", "Shopping", 1200.0),
    ("expense", "Healthcare", 1500.0),
    ("expense", "Education", 5000.0),
    ("income", "Salary", 85000.0),
    ("income", "Salary", 85000.0),
    ("income", "Freelance", 12000.0),
    ("income", "Investments", 3000.0),
]

today = date.today()
existing = db.get_transactions(user.id, limit=5000)
if len(existing) < 5:
    for tx_type, cat_name, amount in tx_data:
        cat = cat_map.get(cat_name)
        if not cat:
            continue
        # Random date within last 45 days
        d = today - timedelta(days=random.randint(0, 45))
        db.add_transaction(user.id, cat.id, amount, tx_type, None, d, "INR")
    print(f"Seeded {len(tx_data)} transactions")
else:
    print(f"Transactions already exist ({len(existing)}), skipping seed")

# Create goals
goals = db.get_goals(user.id)
if not goals:
    db.add_goal(user.id, "Emergency Fund", 100000, today + timedelta(days=365))
    db.add_goal(user.id, "New Laptop", 80000, today + timedelta(days=180))
    db.add_goal(user.id, "Vacation", 50000, today + timedelta(days=90))
    db.add_goal(user.id, "Gym Equipment", 15000, today + timedelta(days=60))
    print("Created 4 demo goals")
else:
    print("Goals already exist, skipping")

# Set budgets
budgets = db.get_budget_limits(user.id)
if not budgets:
    for cat_name, limit in [("Food & Dining", 8000), ("Rent", 16000),
                             ("Entertainment", 3000), ("Shopping", 4000)]:
        cat = cat_map.get(cat_name)
        if cat:
            db.set_budget_limit(user.id, cat.id, limit)
    print("Set 4 budget limits")
else:
    print("Budgets already exist, skipping")

# Update preferred currency
db.update_preferred_currency(user.id, "INR")
print("\nDemo user credentials: demo@finsight.app / demo123")
db.disconnect()
