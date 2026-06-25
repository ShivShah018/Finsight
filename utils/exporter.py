import os
import pandas as pd
from tkinter import filedialog, messagebox
from datetime import date
from utils.db_manager import DatabaseManager
from utils.currency import SYMBOLS


def export_to_excel(user_id: int, start_date: date, end_date: date, parent=None):
    db = DatabaseManager.get_instance()
    txs = db.get_transactions(user_id, limit=50000)
    txs = [t for t in txs if start_date <= t.transaction_date <= end_date]
    if not txs:
        messagebox.showinfo("Export", "No transactions in selected period.", parent=parent)
        return None

    filepath = filedialog.asksaveasfilename(
        parent=parent,
        defaultextension=".xlsx",
        filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")],
        title="Export Transactions",
        initialfile=f"finsight_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx",
    )
    if not filepath:
        return None

    rows = []
    for t in txs:
        rows.append({
            "Date": t.transaction_date.strftime("%Y-%m-%d"),
            "Type": t.type.title(),
            "Category": t.category_name,
            "Amount": t.amount,
            "Currency": t.currency,
            "Display Amount": f"{SYMBOLS.get(t.currency, '')}{t.amount:,.2f}",
            "Description": t.description or "",
        })

    df = pd.DataFrame(rows)
    ext = os.path.splitext(filepath)[1].lower()
    try:
        if ext == ".csv":
            df.to_csv(filepath, index=False, encoding="utf-8-sig")
        else:
            df.to_excel(filepath, index=False, engine="openpyxl")
        messagebox.showinfo("Export", f"Exported {len(rows)} rows to:\n{filepath}", parent=parent)
        return filepath
    except Exception as e:
        messagebox.showerror("Export Error", str(e), parent=parent)
        return None
