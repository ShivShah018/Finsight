"""
FinSight REST API — FastAPI
Run:  uv run uvicorn api.main:app --reload
Docs:  http://localhost:8000/docs
"""
import os
from datetime import date, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr

from utils.db_manager import DatabaseManager

app = FastAPI(title="FinSight API", version="1.0.0",
              description="Budget Planner REST API — manage transactions, goals, budgets & insights")
db = DatabaseManager.get_instance()


# ── Auth / User ──────────────────────────────────────────────
class AuthRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str

@app.post("/auth/login")
def login(req: AuthRequest):
    db.connect()
    user = db.authenticate_user(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return {"user_id": user.id, "name": user.full_name, "email": user.email}

@app.post("/auth/register")
def register(req: RegisterRequest):
    db.connect()
    try:
        user = db.register_user(req.full_name, req.email, req.password)
        return {"user_id": user.id, "name": user.full_name, "email": user.email}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Transactions ─────────────────────────────────────────────
class TransactionCreate(BaseModel):
    user_id: int
    category_id: int
    amount: float
    type: str
    description: Optional[str] = None
    currency: str = "INR"
    transaction_date: date
    is_bill: bool = False

class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    amount: Optional[float] = None
    type: Optional[str] = None
    description: Optional[str] = None
    currency: Optional[str] = None
    transaction_date: Optional[date] = None

@app.get("/transactions")
def list_transactions(user_id: int, limit: int = 100, month: Optional[int] = None, year: Optional[int] = None):
    db.connect()
    return db.get_transactions(user_id, month, year, limit)

@app.get("/transactions/{tx_id}")
def get_transaction(tx_id: int, user_id: int):
    db.connect()
    tx = db.get_transaction_by_id(tx_id, user_id)
    if not tx:
        raise HTTPException(404, "Transaction not found")
    return tx

@app.post("/transactions")
def create_transaction(tx: TransactionCreate):
    db.connect()
    tx_id = db.add_transaction(tx.user_id, tx.category_id, tx.amount, tx.type,
                                tx.description, tx.transaction_date, tx.currency)
    if tx.is_bill:
        db.mark_transaction_as_bill(tx_id, tx.user_id)
    return {"id": tx_id, "message": "Transaction created"}

@app.put("/transactions/{tx_id}")
def update_transaction(tx_id: int, user_id: int, tx: TransactionUpdate):
    db.connect()
    existing = db.get_transaction_by_id(tx_id, user_id)
    if not existing:
        raise HTTPException(404, "Transaction not found")
    db.update_transaction(
        tx_id, user_id,
        tx.category_id or existing.category_id,
        tx.amount or existing.amount,
        tx.type or existing.type,
        tx.description if tx.description is not None else existing.description,
        tx.transaction_date or existing.transaction_date,
        tx.currency or existing.currency,
    )
    return {"message": "Updated"}

@app.delete("/transactions/{tx_id}")
def delete_transaction(tx_id: int, user_id: int, soft: bool = True):
    db.connect()
    if soft:
        db.soft_delete_transaction(tx_id, user_id)
        return {"message": "Soft-deleted"}
    db.delete_transaction(tx_id, user_id)
    return {"message": "Permanently deleted"}


# ── Categories ───────────────────────────────────────────────
@app.get("/categories")
def list_categories(user_id: int, type: Optional[str] = None):
    db.connect()
    return db.get_categories(user_id, type)


# ── Goals ────────────────────────────────────────────────────
class GoalCreate(BaseModel):
    user_id: int
    name: str
    target_amount: float
    deadline: Optional[date] = None
    auto_fund_amount: float = 0
    auto_fund_category_id: Optional[int] = None

@app.get("/goals")
def list_goals(user_id: int):
    db.connect()
    return db.get_goals(user_id)

@app.post("/goals")
def create_goal(g: GoalCreate):
    db.connect()
    gid = db.add_goal(g.user_id, g.name, g.target_amount, g.deadline)
    if g.auto_fund_amount > 0:
        db.set_goal_auto_fund(gid, g.user_id, g.auto_fund_amount, g.auto_fund_category_id)
    return {"id": gid}

@app.post("/goals/{goal_id}/fund")
def fund_goal(goal_id: int, user_id: int, amount: float):
    db.connect()
    db.update_goal_progress(goal_id, amount)
    return {"message": f"Added {amount}"}

@app.post("/goals/{goal_id}/complete")
def complete_goal(goal_id: int, user_id: int):
    db.connect()
    db.complete_goal(goal_id)
    return {"message": "Completed"}


# ── Budgets ──────────────────────────────────────────────────
class BudgetCreate(BaseModel):
    user_id: int
    category_id: int
    monthly_limit: float

@app.get("/budgets")
def list_budgets(user_id: int):
    db.connect()
    return db.get_budget_limits(user_id)

@app.post("/budgets")
def set_budget(b: BudgetCreate):
    db.connect()
    db.set_budget_limit(b.user_id, b.category_id, b.monthly_limit)
    return {"message": "Budget set"}

@app.delete("/budgets/{budget_id}")
def delete_budget(budget_id: int, user_id: int):
    db.connect()
    db.delete_budget_limit(budget_id, user_id)
    return {"message": "Deleted"}


# ── Insights ─────────────────────────────────────────────────
@app.get("/insights/predict/{user_id}")
def predict_spending(user_id: int):
    db.connect()
    from utils.insights import train_spending_model
    txs = db.get_transactions(user_id, limit=5000)
    return train_spending_model(txs)

@app.get("/insights/suggest-category")
def suggest_category(description: str, user_id: int):
    db.connect()
    from utils.insights import suggest_category
    cats = db.get_categories(user_id, "expense")
    result = suggest_category(description, cats)
    if result:
        return {"category": result[0].name, "category_id": result[0].id, "score": result[1]}
    return {"category": None, "score": 0}

@app.get("/insights/cluster/{user_id}")
def clustering(user_id: int):
    db.connect()
    from utils.insights import cluster_transactions
    txs = db.get_transactions(user_id, limit=5000)
    return cluster_transactions(txs)


# ── Report ───────────────────────────────────────────────────
@app.post("/report/generate/{user_id}")
def generate_report(user_id: int, email_to: Optional[str] = None):
    db.connect()
    from utils.report_generator import generate_pdf_report
    user = db.authenticate_user_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    txs = db.get_transactions(user_id, limit=5000)
    goals = db.get_goals(user_id)
    budgets = db.get_budget_limits(user_id)
    path = generate_pdf_report(user, txs, goals, budgets)
    return {"path": path, "message": f"Report generated at {path}"}
