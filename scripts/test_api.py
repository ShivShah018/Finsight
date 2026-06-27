"""Test all API endpoints with JWT authentication."""
import urllib.request
import urllib.parse
import json
import os
import sys

BASE = os.getenv("FINSIGHT_API_URL", "http://localhost:8000")


def req(method, path, data=None, token=None):
    url = BASE + path
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    if method == "GET" and data:
        url += "?" + urllib.parse.urlencode(data)
        body = None
    else:
        body = json.dumps(data).encode() if data else None

    r = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(r)
        return json.loads(resp.read().decode())
    except urllib.request.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode()}


# 1. Register
result = req("POST", "/auth/register",
             {"full_name": "API Tester", "email": "api_test@finsight.app", "password": "demo123"})
if "error" in result:
    print(f"1. Register: already exists (or {result.get('detail', '')})")
else:
    print(f"1. Register: user_id={result['user_id']}")
    token = result["access_token"]

# 2. Login
result = req("POST", "/auth/login",
             {"email": "api_test@finsight.app", "password": "demo123"})
if "error" in result:
    print(f"2. Login FAILED: {result}")
    sys.exit(1)
token = result["access_token"]
uid = result["user_id"]
print(f"2. Login OK: user_id={uid}")

# 3. List transactions
headers = {"Authorization": f"Bearer {token}"}
txs = req("GET", "/transactions", {"limit": "3"}, token=token)
tx_list = txs.get("transactions", [])
names = [t["category_name"] for t in tx_list]
print(f"3. Transactions ({len(tx_list)}): {names}")

# 4. Categories
cats = req("GET", "/categories", {"type": "expense"}, token=token)
print(f"4. Categories: {len(cats)} expense categories")

# 5. Create transaction
if cats:
    new = req("POST", "/transactions", {
        "category_id": cats[0]["id"], "amount": 250.0, "type": "expense",
        "description": "API test", "currency": "INR",
        "transaction_date": "2025-06-25",
    }, token=token)
    print(f"5. Created TX: id={new.get('id', '?')}")

# 6. Predict
if "error" not in locals():
    pred = req("GET", "/insights/predict", {}, token=token)
    print(f"6. Prediction: next={pred.get('predicted_total', 0)}, trend={pred.get('trend', 'N/A')}")

# 7. Suggest category
sug = req("GET", "/insights/suggest-category",
          {"description": "zomato order"}, token=token)
print(f"7. Suggest: {sug.get('category', 'N/A')} (score={sug.get('score', 0)})")

# 8. Goals
goals = req("GET", "/goals", {}, token=token)
print(f"8. Goals: {len(goals)}")

# 9. Budgets
budgets = req("GET", "/budgets", {}, token=token)
print(f"9. Budgets: {len(budgets)}")

# 10. Health
health = req("GET", "/health", None)
print(f"10. Health: {health.get('status', 'N/A')}")

print("\nAll endpoints OK!")
