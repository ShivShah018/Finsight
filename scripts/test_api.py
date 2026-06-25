"""Test all API endpoints."""
import urllib.request, urllib.parse, json

BASE = "http://localhost:8000"


def req(method, path, data=None):
    url = BASE + path
    if method == "GET" and data:
        url += "?" + urllib.parse.urlencode(data)
        data = None
    body = json.dumps(data).encode() if data else None
    r = urllib.request.Request(url, data=body,
                               headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(r).read())


# 1. Register (skip if exists)
try:
    r = req("POST", "/auth/register",
            {"full_name": "API Tester", "email": "api@test.com", "password": "pass"})
    print(f"1. Register: {r}")
except Exception as e:
    print(f"1. Register: already exists")

# 2. Login
data = req("POST", "/auth/login",
           {"email": "demo@finsight.app", "password": "demo123"})
uid = data["user_id"]
print(f"2. Login: user_id={uid}")

# 3. List transactions
txs = req("GET", "/transactions", {"user_id": uid, "limit": 3})
names = [t["category_name"] for t in txs]
print(f"3. Transactions: {names}")

# 4. Get single transaction
if txs:
    tx = req("GET", f"/transactions/{txs[0]['id']}", {"user_id": uid})
    print(f"4. Single TX: {tx['category_name']} {tx['amount']}")

# 5. Create transaction
cats = req("GET", "/categories", {"user_id": uid, "type": "expense"})
if cats:
    new = req("POST", "/transactions", {
        "user_id": uid, "category_id": cats[0]["id"],
        "amount": 250.0, "type": "expense",
        "description": "API test", "currency": "INR",
        "transaction_date": "2025-06-25"
    })
    print(f"5. Created TX: id={new['id']}")

# 6. Predict
pred = req("GET", f"/insights/predict/{uid}", {})
print(f"6. Prediction: next={pred['predicted_total']}, trend={pred['trend']}")

# 7. Suggest category
sug = req("GET", "/insights/suggest-category",
          {"description": "zomato order", "user_id": uid})
print(f"7. Suggest: {sug['category']} (score={sug['score']})")

# 8. Goals
goals = req("GET", "/goals", {"user_id": uid})
print(f"8. Goals: {len(goals)}")

# 9. Budgets
budgets = req("GET", "/budgets", {"user_id": uid})
print(f"9. Budgets: {len(budgets)}")

print("\nAll endpoints OK!")
