"""Tests for the FinSight REST API using httpx test client."""
import os
import pytest
from fastapi.testclient import TestClient
from api.main import app
from utils.config_manager import load_env

load_env()

client = TestClient(app)

pytestmark = pytest.mark.skipif(
    not os.getenv("FINSIGHT_DB_PASSWORD"),
    reason="FINSIGHT_DB_PASSWORD not set",
)


@pytest.fixture
def test_user():
    """Register a test user and return credentials + token."""
    import random
    suffix = random.randint(10000, 99999)
    email = f"apitest{suffix}@example.com"
    resp = client.post("/auth/register", json={
        "full_name": "API Test",
        "email": email,
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    return {
        **data,
        "email": email,
        "password": "testpass123",
        "user_id": data["user_id"],
    }


class TestAuth:
    def test_register(self):
        import random
        suffix = random.randint(10000, 99999)
        resp = client.post("/auth/register", json={
            "full_name": "Test User",
            "email": f"reg{suffix}@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["name"] == "Test User"

    def test_register_duplicate(self, test_user):
        resp = client.post("/auth/register", json={
            "full_name": "Dup",
            "email": test_user["email"],
            "password": "testpass123",
        })
        assert resp.status_code == 409

    def test_login_success(self, test_user):
        resp = client.post("/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data

    def test_login_failure(self):
        resp = client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "wrongpass",
        })
        assert resp.status_code == 401


class TestTransactions:
    def test_create_transaction(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/categories", headers=headers)
        assert resp.status_code == 200
        cats = resp.json()
        assert len(cats) > 0

        resp = client.post("/transactions", headers=headers, json={
            "category_id": cats[0]["id"],
            "amount": 500.0,
            "type": "expense",
            "description": "Test transaction",
            "currency": "INR",
            "transaction_date": "2025-06-01",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    def test_list_transactions(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/transactions", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "transactions" in data

    def test_get_transaction(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/categories", headers=headers)
        cats = resp.json()
        resp = client.post("/transactions", headers=headers, json={
            "category_id": cats[0]["id"], "amount": 250.0, "type": "expense",
            "description": "Get test", "currency": "INR", "transaction_date": "2025-06-01",
        })
        tx_id = resp.json()["id"]
        resp = client.get(f"/transactions/{tx_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["amount"] == 250.0


class TestGoals:
    def test_create_goal(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/goals", headers=headers, json={
            "name": "Test Goal", "target_amount": 10000.0,
            "deadline": "2026-12-31",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data

    def test_list_goals(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/goals", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestBudgets:
    def test_set_budget(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/categories", headers=headers)
        cats = [c for c in resp.json() if c["type"] == "expense"]
        assert len(cats) > 0

        resp = client.post("/budgets", headers=headers, json={
            "category_id": cats[0]["id"], "monthly_limit": 5000.0,
        })
        assert resp.status_code == 201

    def test_list_budgets(self, test_user):
        token = test_user["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/budgets", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
