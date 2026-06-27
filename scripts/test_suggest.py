import sys, os
sys.path.insert(0, "D:\\SHIVAM\\Documents\\finsight")
os.chdir("D:\\SHIVAM\\Documents\\finsight")
from utils.config_manager import load_env
load_env()
from services.transaction_service import TransactionService
from utils.insights import suggest_category
tx_service = TransactionService()
cats = tx_service.get_categories(1, "expense")
for desc in ["hungry", "zomato", "netflix", "uber", "uber xl", "electricity", "amazon", "eating lunch", "dinner date", "coffee", "tea", "movie ticket", "bus pass", "college fee", "metro card", "internet bill"]:
    result = suggest_category(desc, cats)
    if result:
        print(f"{desc:20s} -> {result[0].name:20s} conf={result[1]:.0%}")
    else:
        print(f"{desc:20s} -> no match")
