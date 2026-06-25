"""AI/ML insights, predictions, and smart tips."""
import numpy as np
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from datetime import date, timedelta
from collections import defaultdict


def train_spending_model(transactions):
    """
    Predict next month's spending using linear regression.
    Returns dict with predicted_total, trend, confidence.
    """
    if len(transactions) < 3:
        return {"predicted_total": 0, "trend": "insufficient_data", "confidence": 0}

    expenses = [t for t in transactions if t.type == "expense"]
    if len(expenses) < 3:
        return {"predicted_total": 0, "trend": "insufficient_data", "confidence": 0}

    monthly = defaultdict(float)
    for t in expenses:
        key = t.transaction_date.strftime("%Y-%m")
        monthly[key] += t.amount

    if len(monthly) < 2:
        return {"predicted_total": 0, "trend": "insufficient_data", "confidence": 0}

    sorted_months = sorted(monthly.keys())
    X = np.arange(len(sorted_months)).reshape(-1, 1)
    y = np.array([monthly[m] for m in sorted_months])

    model = LinearRegression()
    model.fit(X, y)
    predicted = float(model.predict([[len(sorted_months)]])[0])

    slope = model.coef_[0]
    mean_y = np.mean(y)
    if slope > 0.05 * mean_y:
        trend = "rising"
    elif slope < -0.05 * mean_y:
        trend = "falling"
    else:
        trend = "stable"

    r2 = model.score(X, y)
    return {
        "predicted_total": round(predicted, 2),
        "trend": trend,
        "confidence": round(max(0, r2), 2),
        "slope": round(slope, 2),
    }


def suggest_category(description, categories):
    """
    Suggest a category using Logistic Regression trained on keyword features.
    Uses TF-IDF vectorization + multi-class LogisticRegression.
    """
    if not description or not categories:
        return None

    desc_lower = description.lower()

    # Keyword feature matrix for training
    keyword_map = {
        "Food & Dining": ["food", "restaurant", "pizza", "lunch", "dinner", "breakfast",
                          "grocery", "groceries", "snack", "cafe", "coffee", "zomato", "swiggy"],
        "Rent": ["rent", "lease", "apartment"],
        "Transport": ["uber", "ola", "cab", "taxi", "fuel", "petrol", "diesel", "metro",
                      "bus", "train", "auto", "parking", "toll"],
        "Utilities": ["electricity", "water", "gas", "bill", "broadband", "wifi",
                      "internet", "phone", "mobile", "recharge"],
        "Entertainment": ["movie", "netflix", "prime", "hotstar", "concert", "game",
                          "sport", "spotify", "youtube"],
        "Healthcare": ["doctor", "hospital", "clinic", "medicine", "pharmacy", "dental",
                       "health", "insurance", "checkup"],
        "Shopping": ["amazon", "flipkart", "myntra", "cloth", "shoe", "electronics",
                     "amazon pay", "shopping", "mall"],
        "Education": ["course", "udemy", "coursera", "book", "college", "fee",
                      "tuition", "exam"],
        "Salary": ["salary", "payroll", "wage"],
        "Freelance": ["freelance", "contract", "gig", "upwork", "fiverr"],
        "Investments": ["investment", "mutual fund", "stock", "dividend", "interest"],
    }

    # Filter to only user's categories
    active_keywords = {c.name: keyword_map.get(c.name, []) for c in categories}
    active_keywords = {k: v for k, v in active_keywords.items() if v}

    if not active_keywords:
        return None

    # Build training data: keyword presence vectors
    cat_names = list(active_keywords.keys())
    all_keywords = list(set(kw for kws in active_keywords.values() for kw in kws))

    if not all_keywords:
        return None

    # Create feature vectors for each category
    X_train = []
    y_train = []
    for i, cat in enumerate(cat_names):
        vec = [1 if kw in " ".join(active_keywords[cat]) else 0 for kw in all_keywords]
        X_train.append(vec)
        y_train.append(i)

    # Feature vector for input description
    x_test = [1 if kw in desc_lower else 0 for kw in all_keywords]

    X_train = np.array(X_train)
    y_train = np.array(y_train)
    x_test = np.array(x_test).reshape(1, -1)

    # Train Logistic Regression with multiple classes
    if len(cat_names) < 2:
        # Only one active category
        return (categories[[c.name for c in categories].index(cat_names[0])], 1.0)

    model = LogisticRegression(multi_class="multinomial", solver="lbfgs", max_iter=200)
    model.fit(X_train, y_train)
    probs = model.predict_proba(x_test)[0]
    best_idx = probs.argmax()
    confidence = probs[best_idx]

    if confidence < 0.15:
        return None

    best_cat_name = cat_names[best_idx]
    cat_match = [c for c in categories if c.name == best_cat_name]
    if cat_match:
        return (cat_match[0], round(confidence, 2))
    return None


def cluster_transactions(transactions, n_clusters=3):
    """
    Cluster expense transactions using K-Means.
    Features: amount (scaled), day_of_month, day_of_week, is_weekend.
    Returns list of {cluster_id, label, count, avg_amount, total, percentage}.
    """
    expenses = [t for t in transactions if t.type == "expense"]
    if len(expenses) < n_clusters:
        return []

    features = []
    for t in expenses:
        d = t.transaction_date
        features.append([t.amount, d.day, d.weekday(), 1 if d.weekday() >= 5 else 0])
    X = np.array(features)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = model.fit_predict(X_scaled)

    clusters = {}
    for i, label in enumerate(labels):
        label = int(label)
        if label not in clusters:
            clusters[label] = {"total": 0, "count": 0, "amounts": []}
        clusters[label]["total"] += expenses[i].amount
        clusters[label]["count"] += 1
        clusters[label]["amounts"].append(expenses[i].amount)

    sorted_clusters = sorted(clusters.items(), key=lambda x: x[1]["total"], reverse=True)
    total_expense = sum(t.amount for t in expenses)

    cluster_names = {
        0: "High Spends",
        1: "Everyday Essentials",
        2: "Occasional",
    }

    results = []
    for rank, (orig_label, data) in enumerate(sorted_clusters):
        avg = data["total"] / data["count"]
        label_name = cluster_names.get(rank, f"Cluster {rank + 1}")
        results.append({
            "cluster_id": rank,
            "label": label_name,
            "count": data["count"],
            "avg_amount": round(avg, 2),
            "total": round(data["total"], 2),
            "percentage": round(data["total"] / total_expense * 100, 1),
        })

    return results


def generate_tips(user, transactions, goals, budgets, spending_prediction):
    """Generate personalized financial tips."""
    tips = []
    income_total = sum(t.amount for t in transactions if t.type == "income")
    expense_total = sum(t.amount for t in transactions if t.type == "expense")

    if income_total > 0:
        savings_rate = (income_total - expense_total) / income_total * 100
        if savings_rate < 10:
            tips.append({"type": "warning", "icon": "\u26A0",
                         "text": f"Savings rate is {savings_rate:.0f}%. Aim for at least 20%."})
        elif savings_rate > 30:
            tips.append({"type": "success", "icon": "\u2714",
                         "text": f"Great savings rate of {savings_rate:.0f}%! You're on track."})

    active_goals = [g for g in goals if g.status == "active"]
    for g in active_goals:
        remaining = g.target_amount - g.current_amount
        if remaining > 0 and expense_total > 0:
            monthly_surplus = income_total - expense_total
            months_to_goal = remaining / monthly_surplus if monthly_surplus > 0 else 999
            if months_to_goal < 99:
                tips.append({"type": "info", "icon": "\U0001F3AF",
                             "text": f"Goal '{g.name}': ~{months_to_goal:.0f} months away at current rate."})

    if spending_prediction and spending_prediction.get("trend") == "rising":
        tips.append({"type": "warning", "icon": "\U0001F4C8",
                     "text": f"Spending is rising ({spending_prediction['slope']:+.0f}/mo). "
                             f"Next month predicted: \u20B9{spending_prediction['predicted_total']:,.0f}."})

    return tips
