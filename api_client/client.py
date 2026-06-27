"""
HTTP client for communicating with the FinSight REST API.
All GUI views should use this instead of directly calling DatabaseManager.
"""
import os
import logging
from typing import Optional
from datetime import date

import httpx

logger = logging.getLogger(__name__)


class FinSightClient:
    """API client for FinSight backend. Handles JWT auth and all API calls."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.getenv("FINSIGHT_API_URL", "http://localhost:8000")
        self.token: Optional[str] = None
        self._client = httpx.Client(timeout=30.0)

    def set_token(self, token: str):
        self.token = token

    def clear_token(self):
        self.token = None

    @property
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _request(self, method: str, path: str, **kwargs):
        url = f"{self.base_url}{path}"
        try:
            response = self._client.request(method, url, headers=self._headers, **kwargs)
            try:
                body = response.json()
            except Exception:
                body = {}
            if response.status_code >= 400:
                detail = body.get("detail") if isinstance(body, dict) else str(response.text)
                raise ApiError(response.status_code, detail or str(response.status_code))
            return body
        except httpx.RequestError as e:
            logger.error(f"Request failed: {e}")
            raise ApiError(0, f"Connection error: {e}")

    # ── Auth ───────────────────────────────────────────────────
    def login(self, email: str, password: str) -> dict:
        result = self._request("POST", "/auth/login", json={"email": email, "password": password})
        self.token = result["access_token"]
        return result

    def register(self, full_name: str, email: str, password: str) -> dict:
        result = self._request("POST", "/auth/register", json={
            "full_name": full_name, "email": email, "password": password,
        })
        self.token = result["access_token"]
        return result

    def get_me(self) -> dict:
        return self._request("GET", "/auth/me")

    # ── Transactions ───────────────────────────────────────────
    def get_transactions(self, limit: int = 100, month: int = None, year: int = None) -> dict:
        params = {"limit": limit}
        if month: params["month"] = month
        if year: params["year"] = year
        return self._request("GET", "/transactions", params=params)

    def get_transaction(self, tx_id: int) -> dict:
        return self._request("GET", f"/transactions/{tx_id}")

    def create_transaction(self, category_id: int, amount: float, tx_type: str,
                           description: str = None, currency: str = "INR",
                           transaction_date: str = None, is_bill: bool = False) -> dict:
        payload = {
            "category_id": category_id, "amount": amount, "type": tx_type,
            "description": description, "currency": currency,
            "transaction_date": transaction_date or date.today().isoformat(),
            "is_bill": is_bill,
        }
        return self._request("POST", "/transactions", json=payload)

    def update_transaction(self, tx_id: int, **kwargs) -> dict:
        return self._request("PUT", f"/transactions/{tx_id}", json=kwargs)

    def delete_transaction(self, tx_id: int, soft: bool = True) -> dict:
        return self._request("DELETE", f"/transactions/{tx_id}", params={"soft": str(soft).lower()})

    def restore_transaction(self, tx_id: int) -> dict:
        return self._request("POST", f"/transactions/{tx_id}/restore")

    def get_deleted_transactions(self) -> list:
        return self._request("GET", "/transactions/deleted/recent")

    # ── Categories ─────────────────────────────────────────────
    def get_categories(self, type: str = None) -> list:
        params = {}
        if type:
            params["type"] = type
        return self._request("GET", "/categories", params=params)

    # ── Goals ──────────────────────────────────────────────────
    def get_goals(self) -> list:
        return self._request("GET", "/goals")

    def create_goal(self, name: str, target_amount: float, deadline: str = None,
                    auto_fund_amount: float = 0, auto_fund_category_id: int = None) -> dict:
        payload = {
            "name": name, "target_amount": target_amount, "deadline": deadline,
            "auto_fund_amount": auto_fund_amount, "auto_fund_category_id": auto_fund_category_id,
        }
        return self._request("POST", "/goals", json=payload)

    def fund_goal(self, goal_id: int, amount: float) -> dict:
        return self._request("POST", f"/goals/{goal_id}/fund", json={"amount": amount})

    def complete_goal(self, goal_id: int) -> dict:
        return self._request("POST", f"/goals/{goal_id}/complete")

    def cancel_goal(self, goal_id: int) -> dict:
        return self._request("POST", f"/goals/{goal_id}/cancel")

    # ── Budgets ────────────────────────────────────────────────
    def get_budgets(self) -> list:
        return self._request("GET", "/budgets")

    def set_budget(self, category_id: int, monthly_limit: float) -> dict:
        return self._request("POST", "/budgets", json={
            "category_id": category_id, "monthly_limit": monthly_limit,
        })

    def update_budget(self, budget_id: int, monthly_limit: float) -> dict:
        return self._request("PUT", f"/budgets/{budget_id}", json={"monthly_limit": monthly_limit})

    def delete_budget(self, budget_id: int) -> dict:
        return self._request("DELETE", f"/budgets/{budget_id}")

    def get_budget_utilization(self, month: int = None, year: int = None) -> dict:
        params = {}
        if month: params["month"] = month
        if year: params["year"] = year
        return self._request("GET", "/budgets/utilization", params=params)

    def get_spending_by_category(self, month: int = None, year: int = None) -> list:
        params = {}
        if month: params["month"] = month
        if year: params["year"] = year
        return self._request("GET", "/budgets/spending", params=params)

    # ── Dashboard / Analytics ──────────────────────────────────
    def get_dashboard(self, month: int = None, year: int = None) -> dict:
        params = {}
        if month: params["month"] = month
        if year: params["year"] = year
        return self._request("GET", "/dashboard", params=params)

    def get_trends(self, months: int = 12) -> list:
        return self._request("GET", "/analytics/trends", params={"months": months})

    def get_summary(self, month: int = None, year: int = None) -> dict:
        params = {}
        if month: params["month"] = month
        if year: params["year"] = year
        return self._request("GET", "/analytics/summary", params=params)

    # ── Insights ───────────────────────────────────────────────
    def predict_spending(self) -> dict:
        return self._request("GET", "/insights/predict")

    def suggest_category(self, description: str) -> dict:
        return self._request("GET", "/insights/suggest-category", params={"description": description})

    def get_clusters(self) -> list:
        return self._request("GET", "/insights/cluster")

    def get_insights_all(self) -> dict:
        return self._request("GET", "/insights/all")

    # ── Report ─────────────────────────────────────────────────
    def generate_report(self, email_to: str = None) -> dict:
        params = {}
        if email_to: params["email_to"] = email_to
        return self._request("POST", "/report/generate", params=params)


class ApiError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API Error {status_code}: {detail}")
