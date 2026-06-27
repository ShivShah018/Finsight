"""
FinSight REST API — FastAPI
Run:  uv run uvicorn api.main:app --reload
Docs:  http://localhost:8000/docs
"""
import os
import logging
from datetime import date
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from services.auth_service import AuthService
from services.transaction_service import TransactionService
from services.goal_service import GoalService
from services.budget_service import BudgetService
from services.analytics_service import AnalyticsService
from schemas.auth import AuthRequest, RegisterRequest, TokenResponse
from schemas.transactions import TransactionCreate, TransactionUpdate, TransactionResponse, TransactionListResponse
from schemas.goals import GoalCreate, GoalResponse, GoalFundRequest
from schemas.budgets import BudgetCreate, BudgetResponse, BudgetUpdate
from schemas.analytics import DashboardSummary
from utils.config_manager import load_env

load_env()

logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("finsight.api")

security = HTTPBearer(auto_error=False)

auth_service = AuthService()
tx_service = TransactionService()
goal_service = GoalService()
budget_service = BudgetService()
analytics_service = AnalyticsService()


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = auth_service.get_current_user(credentials.credentials)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("FinSight API starting up")
    yield
    logger.info("FinSight API shutting down")


app = FastAPI(
    title="FinSight API",
    version="2.0.0",
    description="""Production-ready REST API for the FinSight personal finance manager.
    Manage transactions, goals, budgets, and get AI-powered analytics.
    All endpoints except /auth/* require JWT authentication (Bearer token).
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Auth ────────────────────────────────────────────────────────
@app.post("/auth/login",
          summary="Authenticate user and return JWT token",
          description="Validates email and password. Returns a JWT access token for subsequent requests.")
def login(req: AuthRequest):
    try:
        result = auth_service.login(req.email.strip().lower(), req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.post("/auth/register",
          summary="Register a new user",
          description="Creates a new user account with default categories. Returns JWT token.")
def register(req: RegisterRequest):
    try:
        result = auth_service.register(req.full_name.strip(), req.email.strip().lower(), req.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@app.get("/auth/me",
         summary="Get current user profile",
         description="Returns the authenticated user's profile information.")
def get_me(user=Depends(get_current_user)):
    return {"user_id": user.id, "name": user.full_name, "email": user.email, "currency": user.preferred_currency}


# ── Transactions ────────────────────────────────────────────────
@app.get("/transactions",
         summary="List transactions",
         description="Returns transactions for the authenticated user. Supports filtering by month/year and pagination.")
def list_transactions(
    limit: int = Query(100, ge=1, le=5000),
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000, le=2100),
    user=Depends(get_current_user),
):
    txs = tx_service.list_all(user.id, month, year, limit)
    return TransactionListResponse(
        transactions=[
            TransactionResponse(
                id=t.id, category_id=t.category_id, category_name=t.category_name,
                amount=t.amount, type=t.type, description=t.description,
                transaction_date=t.transaction_date, currency=t.currency,
            ) for t in txs
        ],
        total=len(txs),
    )


@app.get("/transactions/{tx_id}",
         summary="Get a single transaction",
         description="Returns details of a specific transaction by ID.")
def get_transaction(tx_id: int, user=Depends(get_current_user)):
    tx = tx_service.get_by_id(tx_id, user.id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return TransactionResponse(
        id=tx.id, category_id=tx.category_id, category_name=tx.category_name,
        amount=tx.amount, type=tx.type, description=tx.description,
        transaction_date=tx.transaction_date, currency=tx.currency,
    )


@app.post("/transactions",
          summary="Create a transaction",
          description="Creates a new income or expense transaction. Optionally mark as a bill.",
          status_code=status.HTTP_201_CREATED)
def create_transaction(tx: TransactionCreate, user=Depends(get_current_user)):
    try:
        tx_id = tx_service.create(
            user.id, tx.category_id, tx.amount, tx.type.lower(),
            tx.description, tx.transaction_date, tx.currency, tx.is_bill,
        )
        return {"id": tx_id, "message": "Transaction created"}
    except Exception as e:
        logger.error(f"Failed to create transaction: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/transactions/{tx_id}",
         summary="Update a transaction",
         description="Updates an existing transaction. Only provided fields are changed.")
def update_transaction(tx_id: int, tx: TransactionUpdate, user=Depends(get_current_user)):
    try:
        tx_service.update(
            tx_id, user.id,
            category_id=tx.category_id,
            amount=tx.amount,
            type=tx.type,
            description=tx.description,
            transaction_date=tx.transaction_date,
            currency=tx.currency,
        )
        return {"message": "Transaction updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@app.delete("/transactions/{tx_id}",
            summary="Delete a transaction",
            description="Soft-deletes by default. Use soft=false for permanent deletion.")
def delete_transaction(tx_id: int, soft: bool = Query(True), user=Depends(get_current_user)):
    tx_service.delete(tx_id, user.id, soft=soft)
    return {"message": "Soft-deleted" if soft else "Permanently deleted"}


@app.post("/transactions/{tx_id}/restore",
          summary="Restore a soft-deleted transaction",
          description="Restores a previously soft-deleted transaction.")
def restore_transaction(tx_id: int, user=Depends(get_current_user)):
    tx_service.restore(tx_id, user.id)
    return {"message": "Transaction restored"}


@app.get("/transactions/deleted/recent",
         summary="Get recently deleted transactions",
         description="Returns the 20 most recently soft-deleted transactions for undo.")
def get_deleted_transactions(user=Depends(get_current_user)):
    txs = tx_service.get_deleted(user.id)
    return [
        TransactionResponse(
            id=t.id, category_id=t.category_id, category_name=t.category_name,
            amount=t.amount, type=t.type, description=t.description,
            transaction_date=t.transaction_date, currency=t.currency,
        ) for t in txs
    ]


# ── Categories ──────────────────────────────────────────────────
@app.get("/categories",
         summary="List categories",
         description="Returns all categories for the authenticated user. Filter by type (income/expense).")
def list_categories(type: Optional[str] = Query(None, regex="^(income|expense)?$"), user=Depends(get_current_user)):
    cats = tx_service.get_categories(user.id, type)
    return [{"id": c.id, "name": c.name, "type": c.type, "icon": c.icon, "color": c.color} for c in cats]


# ── Goals ───────────────────────────────────────────────────────
@app.get("/goals",
         summary="List savings goals",
         description="Returns all active and completed savings goals for the authenticated user.")
def list_goals(user=Depends(get_current_user)):
    goals = goal_service.list_all(user.id)
    return [
        GoalResponse(
            id=g.id, name=g.name, target_amount=g.target_amount,
            current_amount=g.current_amount, deadline=g.deadline,
            status=g.status, progress_pct=g.progress_pct,
        ) for g in goals
    ]


@app.post("/goals",
          summary="Create a savings goal",
          description="Creates a new savings goal with optional auto-fund settings.",
          status_code=status.HTTP_201_CREATED)
def create_goal(g: GoalCreate, user=Depends(get_current_user)):
    try:
        gid = goal_service.create(
            user.id, g.name, g.target_amount, g.deadline,
            g.auto_fund_amount, g.auto_fund_category_id,
        )
        return {"id": gid, "message": "Goal created"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post("/goals/{goal_id}/fund",
          summary="Add funds to a goal",
          description="Adds money to an existing savings goal's current amount.")
def fund_goal(goal_id: int, req: GoalFundRequest, user=Depends(get_current_user)):
    goal_service.add_funds(goal_id, req.amount)
    return {"message": f"Added {req.amount} to goal"}


@app.post("/goals/{goal_id}/complete",
          summary="Complete a goal",
          description="Marks a savings goal as completed.")
def complete_goal(goal_id: int, user=Depends(get_current_user)):
    goal_service.complete(goal_id)
    return {"message": "Goal completed"}


@app.post("/goals/{goal_id}/cancel",
          summary="Cancel a goal",
          description="Cancels a savings goal (hides it from the active list).")
def cancel_goal(goal_id: int, user=Depends(get_current_user)):
    goal_service.cancel(goal_id)
    return {"message": "Goal cancelled"}


# ── Budgets ─────────────────────────────────────────────────────
@app.get("/budgets",
         summary="List budget limits",
         description="Returns all budget limits per category for the authenticated user.")
def list_budgets(user=Depends(get_current_user)):
    budgets = budget_service.list_all(user.id)
    return [
        BudgetResponse(id=b.id, category_id=b.category_id,
                       category_name=b.category_name, monthly_limit=b.monthly_limit)
        for b in budgets
    ]


@app.get("/budgets/spending",
         summary="Spending by category",
         description="Returns total expense per category for a given month/year.")
def spending_by_category(month: Optional[int] = Query(None, ge=1, le=12),
                         year: Optional[int] = Query(None, ge=2000, le=2100),
                         user=Depends(get_current_user)):
    today = date.today()
    return tx_service.get_spending_by_category(user.id, month or today.month, year or today.year)


@app.post("/budgets",
          summary="Set a budget limit",
          description="Sets or updates a monthly budget limit for a category.",
          status_code=status.HTTP_201_CREATED)
def set_budget(b: BudgetCreate, user=Depends(get_current_user)):
    try:
        budget_service.set_limit(user.id, b.category_id, b.monthly_limit)
        return {"message": "Budget limit set"}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.put("/budgets/{budget_id}",
         summary="Update a budget limit",
         description="Updates an existing budget limit.")
def update_budget(budget_id: int, b: BudgetUpdate, user=Depends(get_current_user)):
    budget_service.update_limit(budget_id, user.id, b.monthly_limit)
    return {"message": "Budget updated"}


@app.delete("/budgets/{budget_id}",
            summary="Delete a budget limit",
            description="Removes a budget limit.")
def delete_budget(budget_id: int, user=Depends(get_current_user)):
    budget_service.delete(budget_id, user.id)
    return {"message": "Budget deleted"}


@app.get("/budgets/utilization",
         summary="Get budget utilization",
         description="Returns how much of each budget has been spent for a given month.")
def get_budget_utilization(month: Optional[int] = Query(None, ge=1, le=12),
                            year: Optional[int] = Query(None, ge=2000, le=2100),
                            user=Depends(get_current_user)):
    today = date.today()
    month = month or today.month
    year = year or today.year
    return budget_service.get_utilization(user.id, month, year)


# ── Dashboard / Analytics ──────────────────────────────────────
@app.get("/dashboard",
         summary="Get financial dashboard summary",
         description="Returns a comprehensive financial overview including income, expenses, savings rate, top categories, monthly trends, and budget utilization.")
def get_dashboard(month: Optional[int] = Query(None, ge=1, le=12),
                  year: Optional[int] = Query(None, ge=2000, le=2100),
                  user=Depends(get_current_user)):
    today = date.today()
    data = analytics_service.get_dashboard(
        user.id,
        month or today.month,
        year or today.year,
    )
    return data


@app.get("/analytics/trends",
         summary="Get monthly income/expense trends",
         description="Returns monthly income and expense data for the last N months for trend analysis.")
def get_trends(months: int = Query(12, ge=1, le=60), user=Depends(get_current_user)):
    return analytics_service.get_monthly_trends(user.id, months)


@app.get("/analytics/summary",
         summary="Get summary for a period",
         description="Returns total income, expense, and net savings for a given month/year.")
def get_summary(month: Optional[int] = Query(None, ge=1, le=12),
                year: Optional[int] = Query(None, ge=2000, le=2100),
                user=Depends(get_current_user)):
    today = date.today()
    return tx_service.get_summary(user.id, month or today.month, year or today.year)


# ── Insights ────────────────────────────────────────────────────
@app.get("/insights/predict",
         summary="Predict next month's spending",
         description="Uses linear regression to predict next month's total spending based on historical data.")
def predict_spending(user=Depends(get_current_user)):
    from utils.insights import train_spending_model
    txs = tx_service.list_all(user.id, limit=5000)
    return train_spending_model(txs)


@app.get("/insights/suggest-category",
         summary="Suggest a category for a description",
         description="Uses ML to suggest the most likely expense category for a given transaction description.")
def suggest_category(description: str = Query(..., min_length=1), user=Depends(get_current_user)):
    from utils.insights import suggest_category as suggest_cat
    cats = tx_service.get_categories(user.id, "expense")
    result = suggest_cat(description, cats)
    if result:
        return {"category": result[0].name, "category_id": result[0].id, "score": result[1]}
    return {"category": None, "score": 0}


@app.get("/insights/cluster",
         summary="Get spending behavior clusters",
         description="Uses K-Means clustering to group expenses into spending behavior categories.")
def clustering(user=Depends(get_current_user)):
    from utils.insights import cluster_transactions
    txs = tx_service.list_all(user.id, limit=5000)
    return cluster_transactions(txs)


@app.get("/insights/all",
         summary="All insights data in one call",
         description="Returns transactions, goals, budgets, prediction, and clusters in a single request.")
def insights_all(user=Depends(get_current_user)):
    from utils.insights import train_spending_model, cluster_transactions
    txs = tx_service.list_all(user.id, limit=5000)
    goals = goal_service.list_all(user.id)
    budgets = budget_service.list_all(user.id)
    txs_list = [TransactionResponse(
        id=t.id, category_id=t.category_id, category_name=t.category_name,
        amount=t.amount, type=t.type, description=t.description,
        transaction_date=t.transaction_date.isoformat(), currency=t.currency,
    ) for t in txs]
    txs_dict = {"transactions": txs_list}
    goals_dict = [{"id": g.id, "name": g.name, "target_amount": g.target_amount,
                   "current_amount": g.current_amount, "deadline": g.deadline.isoformat() if g.deadline else None,
                   "status": g.status, "progress_pct": g.progress_pct} for g in goals]
    budgets_dict = [{"id": b.id, "category_id": b.category_id,
                     "category_name": b.category_name, "monthly_limit": b.monthly_limit} for b in budgets]
    return {
        "transactions": txs_dict["transactions"],
        "goals": goals_dict,
        "budgets": budgets_dict,
        "prediction": train_spending_model(txs),
        "clusters": cluster_transactions(txs),
    }


# ── Report ─────────────────────────────────────────────────────
@app.post("/report/generate",
          summary="Generate PDF financial report",
          description="Generates a PDF report with transactions, goals, and budgets for the authenticated user.")
def generate_report(email_to: Optional[str] = None, user=Depends(get_current_user)):
    from utils.report_generator import generate_pdf_report
    data = analytics_service.get_export_data(user.id)
    path = generate_pdf_report(user, data["transactions"], data["goals"], data["budgets"])
    return {"path": path, "message": f"Report generated at {path}"}


# ── Health ──────────────────────────────────────────────────────
@app.get("/health",
         summary="Health check",
         description="Returns the API health status.")
def health_check():
    return {"status": "healthy", "version": "2.0.0"}
