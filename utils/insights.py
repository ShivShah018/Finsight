"""AI/ML insights, predictions, anomaly detection, and smart tips."""
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from datetime import date, timedelta
from collections import defaultdict


def train_spending_model(transactions):
    """
    Predict next month's spending using linear regression.
    transactions: list of TransactionRow (must include transaction_date and amount)
    Returns dict with predicted_total, trend (rising/falling/stable), confidence
    """
    if len(transactions) < 3:
        return {"predicted_total": 0, "trend": "insufficient_data", "confidence": 0}

    expenses = [t for t in transactions if t.type == "expense"]
    if len(expenses) < 3:
        return {"predicted_total": 0, "trend": "insufficient_data", "confidence": 0}

    # Aggregate by month
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
    next_month_idx = len(sorted_months)
    predicted = float(model.predict([[next_month_idx]])[0])

    slope = model.coef_[0]
    if slope > 0.05 * np.mean(y):
        trend = "rising"
    elif slope < -0.05 * np.mean(y):
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


def detect_anomalies(transactions, contamination=0.05):
    """
    Flag unusual transactions using Isolation Forest.
    Returns list of (transaction, anomaly_score) for flagged items.
    """
    expenses = [t for t in transactions if t.type == "expense"]
    if len(expenses) < 5:
        return []

    # Features: amount, day_of_month, is_weekend
    X = []
    tx_list = []
    for t in expenses:
        X.append([
            float(t.amount),
            t.transaction_date.day,
            1 if t.transaction_date.weekday() >= 5 else 0,
        ])
        tx_list.append(t)

    X = np.array(X)
    model = IsolationForest(contamination=contamination, random_state=42)
    preds = model.fit_predict(X)
    scores = model.score_samples(X)

    anomalies = []
    for i, (tx, pred) in enumerate(zip(tx_list, preds)):
        if pred == -1:
            anomalies.append((tx, round(float(scores[i]), 4)))
    return sorted(anomalies, key=lambda x: x[1])[:10]


def suggest_category(description, categories):
    """
    Suggest a category based on transaction description using TF-IDF + cosine similarity.
    categories: list of Category objects with name attribute
    Returns (category_name, similarity_score) or None
    """
    if not description or not categories:
        return None

    # Category keywords for matching
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
        "Salary": ["salary", "payroll", "wage", "income"],
        "Freelance": ["freelance", "contract", "gig", "upwork", "fiverr"],
        "Investments": ["investment", "mutual fund", "stock", "dividend", "interest",
                        "returns"],
    }

    desc_lower = description.lower()
    words = desc_lower.split()

    # Direct keyword match first
    best_cat = None
    best_score = 0
    for cat_name, keywords in keyword_map.items():
        for kw in keywords:
            if kw in desc_lower:
                score = len(kw) / len(desc_lower)
                if score > best_score:
                    best_score = score
                    best_cat = cat_name

    # TF-IDF fallback for fuzzy matching
    if not best_cat:
        corpus = [c.name for c in categories] + [description]
        vectorizer = TfidfVectorizer().fit_transform(corpus)
        vectors = vectorizer.toarray()
        if vectors.shape[0] >= 2:
            similarities = cosine_similarity(vectors[-1:], vectors[:-1])[0]
            best_match_idx = similarities.argmax()
            if similarities[best_match_idx] > 0.1:
                best_cat = categories[best_match_idx].name
                best_score = similarities[best_match_idx]

    if best_cat:
        cat_match = [c for c in categories if c.name == best_cat]
        if cat_match:
            return (cat_match[0], round(best_score, 2))
    return None


def generate_tips(user, transactions, goals, budgets, spending_prediction):
    """Generate personalized financial tips."""
    tips = []
    income_total = sum(t.amount for t in transactions if t.type == "income")
    expense_total = sum(t.amount for t in transactions if t.type == "expense")

    # Tip 1: Savings rate
    if income_total > 0:
        savings_rate = (income_total - expense_total) / income_total * 100
        if savings_rate < 10:
            tips.append({"type": "warning", "icon": "\u26A0",
                         "text": f"Savings rate is {savings_rate:.0f}%. Aim for at least 20%."})
        elif savings_rate > 30:
            tips.append({"type": "success", "icon": "\u2714",
                         "text": f"Great savings rate of {savings_rate:.0f}%! You're on track."})

    # Tip 2: Budget alerts
    if budgets:
        over_budget = [b for b in budgets if b.monthly_limit > 0]
        # This requires category spending data - passed separately

    # Tip 3: Goal progress
    active_goals = [g for g in goals if g.status == "active"]
    for g in active_goals:
        remaining = g.target_amount - g.current_amount
        if remaining > 0 and expense_total > 0:
            months_to_goal = remaining / (income_total - expense_total) if (income_total - expense_total) > 0 else 999
            if months_to_goal > 0 and months_to_goal < 99:
                tips.append({"type": "info", "icon": "\U0001F3AF",
                             "text": f"Goal '{g.name}': ~{months_to_goal:.0f} months away at current rate."})

    # Tip 4: Spending trend
    if spending_prediction and spending_prediction.get("trend") == "rising":
        tips.append({"type": "warning", "icon": "\U0001F4C8",
                     "text": f"Spending is rising ({spending_prediction['slope']:+.0f}/mo). "
                             f"Next month predicted: \u20B9{spending_prediction['predicted_total']:,.0f}."})

    # Tip 5: Anomaly tip
    anomalies = detect_anomalies(transactions)
    if anomalies:
        tips.append({"type": "info", "icon": "\U0001F50D",
                     "text": f"{len(anomalies)} unusual transaction(s) detected. Check the Insights tab."})

    return tips
