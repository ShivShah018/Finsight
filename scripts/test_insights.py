"""Quick test for insights module."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_manager import DatabaseManager
from utils.insights import train_spending_model, detect_anomalies

db = DatabaseManager.get_instance(); db.connect()
u = db.authenticate_user('demo@finsight.app', 'demo123')
txs = db.get_transactions(u.id, limit=5000)

pred = train_spending_model(txs)
print(f"Prediction: predicted={pred['predicted_total']}, trend={pred['trend']}, confidence={pred['confidence']}")

anom = detect_anomalies(txs)
print(f"Anomalies found: {len(anom)}")
for tx, s in anom[:3]:
    print(f"  {tx.category_name}: {tx.amount} (score: {s})")

db.disconnect()
print("OK")
