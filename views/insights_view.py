import customtkinter as ctk
from utils.currency import SYMBOLS
from datetime import date, timedelta
from api_client.client import ApiError

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "accent":        "#6366f1",
    "success":       "#22c55e",
    "expense":       "#ef4444",
    "warning":       "#eab308",
}


class InsightsView(ctk.CTkFrame):

    def __init__(self, master, api, user, user_data, **kwargs):
        super().__init__(master, **kwargs)
        self.api = api
        self.user = user
        self.user_data = user_data
        self.configure(fg_color="transparent")
        self._build_ui()
        self.after(50, self._load)

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(self.scroll, text="AI Insights",
                     font=ctk.CTkFont(size=28, weight="bold"), anchor="w"
                     ).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkLabel(self.scroll,
                     text="Spending predictions, spending behavior grouping, category suggester & smart tips",
                     font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"], anchor="w"
                     ).pack(anchor="w", padx=20, pady=(0, 6))

        self._refresh_btn = ctk.CTkButton(self.scroll, text="\U0001F504  Refresh Insights", width=140, height=32,
                                          corner_radius=8, fg_color=COLORS["accent"],
                                          font=ctk.CTkFont(size=12, weight="bold"),
                                          command=self._load)
        self._refresh_btn.pack(anchor="w", padx=20, pady=(0, 12))

        self._cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._cards_frame.pack(fill="x", padx=20)
        self._loading_lbl = ctk.CTkLabel(self._cards_frame, text="Loading insights...",
                                          font=ctk.CTkFont(size=13),
                                          text_color=COLORS["text_muted"])
        self._loading_lbl.pack(pady=40)

    def _load(self):
        for w in self._cards_frame.winfo_children(): w.destroy()

        def _try(method, *a, **kw):
            try:
                return method(*a, **kw)
            except ApiError:
                return None
            except Exception:
                import traceback; traceback.print_exc()
                return None

        data = None
        try:
            data = self.api.get_insights_all()
        except ApiError as e:
            if e.status_code != 404:
                ctk.CTkLabel(self._cards_frame, text=f"\u26A0  Error: {e}",
                             text_color="#ef4444").pack(pady=20)
                return
        except Exception as e:
            import traceback; traceback.print_exc()
            ctk.CTkLabel(self._cards_frame, text=f"\u26A0  Connection error",
                         text_color="#ef4444").pack(pady=20)
            return

        if data is None:
            txs_result = _try(self.api.get_transactions, limit=5000)
            txs = txs_result.get("transactions", []) if txs_result else []
            goals = _try(self.api.get_goals) or []
            budgets = _try(self.api.get_budgets) or []
            pred = _try(self.api.predict_spending) or {}
            clusters = _try(self.api.get_clusters) or []
        else:
            txs = data.get("transactions", [])
            goals = data.get("goals", [])
            budgets = data.get("budgets", [])
            pred = data.get("prediction", {})
            clusters = data.get("clusters", [])

        # Prediction card
        pred_card = self._make_card(self._cards_frame)
        ctk.CTkLabel(pred_card, text="\U0001F4CA  Spending Prediction",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        if not pred or pred.get("trend") in (None, "insufficient_data"):
            ctk.CTkLabel(pred_card, text="Not enough data yet. Add more transactions.",
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
            trend_icon = "\U0001F4C8" if pred["trend"] == "rising" else "\U0001F4C9" if pred["trend"] == "falling" else "\U0001F4CB"
            trend_color = COLORS["expense"] if pred["trend"] == "rising" else COLORS["success"]
            ctk.CTkLabel(pred_card, text=f"Next month: {sym}{pred.get('predicted_total', 0):,.0f}",
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=COLORS["text_primary"]).pack(anchor="w", padx=16)
            ctk.CTkLabel(pred_card, text=f"{trend_icon} Trend: {pred['trend'].title()}  ({pred.get('slope', 0):+.0f}/mo)",
                         font=ctk.CTkFont(size=12), text_color=trend_color, anchor="w"
                         ).pack(anchor="w", padx=16, pady=(2, 4))
            ctk.CTkLabel(pred_card, text=f"Confidence: {pred.get('confidence', 0)*100:.0f}%",
                         font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w"
                         ).pack(anchor="w", padx=16, pady=(0, 12))

        # Clustering card
        clust_card = self._make_card(self._cards_frame)
        ctk.CTkLabel(clust_card, text="\U0001F52E  Spending Behavior Groups",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        ctk.CTkLabel(clust_card, text="Expenses grouped into 3 clusters by amount, day & frequency",
                     font=ctk.CTkFont(size=11), text_color=COLORS["text_muted"], anchor="w"
                     ).pack(anchor="w", padx=16, pady=(0, 4))
        if not clusters:
            ctk.CTkLabel(clust_card, text="Not enough expense data to cluster (min 3 txns).",
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
            for c in clusters:
                bar_frame = ctk.CTkFrame(clust_card, fg_color="transparent")
                bar_frame.pack(fill="x", padx=16, pady=2)
                ctk.CTkLabel(bar_frame, text=f"{c['label']}",
                             font=ctk.CTkFont(size=12, weight="bold"),
                             text_color=COLORS["text_primary"], anchor="w", width=140
                             ).pack(side="left")
                ctk.CTkLabel(bar_frame,
                             text=f"{c['count']} txns  |  {sym}{c['avg_amount']:,.0f} avg  |  {c['percentage']:.0f}%",
                             font=ctk.CTkFont(size=11), text_color=COLORS["text_secondary"], anchor="w"
                             ).pack(side="left", padx=(4, 0))
                bar_bg = ctk.CTkFrame(clust_card, height=6, corner_radius=3, fg_color="#1a1f3a")
                bar_bg.pack(fill="x", padx=16, pady=(0, 4))
                bar = ctk.CTkFrame(bar_bg, height=6, corner_radius=3,
                                   fg_color=["#ef4444", "#eab308", "#6366f1"][c['cluster_id'] % 3])
                bar.place(relwidth=c['percentage'] / 100, relheight=1)
            ctk.CTkLabel(clust_card, text="", font=ctk.CTkFont(size=6)).pack(pady=(0, 4))

        # Tips card
        tips = self._generate_tips(txs, goals, budgets, pred)
        tips_card = self._make_card(self._cards_frame)
        ctk.CTkLabel(tips_card, text="\U0001F4A1  Smart Tips",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        if not tips:
            ctk.CTkLabel(tips_card, text="No tips available right now.",
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=16, pady=(0, 12))
        else:
            for tip in tips:
                color_map = {"warning": COLORS["expense"], "success": COLORS["success"], "info": COLORS["accent"]}
                c = color_map.get(tip["type"], COLORS["text_secondary"])
                f = ctk.CTkFrame(tips_card, fg_color="#1a1f3a", corner_radius=8)
                f.pack(fill="x", padx=16, pady=3)
                ctk.CTkLabel(f, text=f"{tip['icon']}  {tip['text']}",
                             font=ctk.CTkFont(size=12), text_color=c, anchor="w",
                             wraplength=600, justify="left").pack(padx=12, pady=8)
            ctk.CTkLabel(tips_card, text="", font=ctk.CTkFont(size=6)).pack(pady=(0, 4))

        # Category suggestion demo
        cat_card = self._make_card(self._cards_frame)
        ctk.CTkLabel(cat_card, text="\U0001F3B7  AI Category Suggester",
                     font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(anchor="w", padx=16, pady=(12, 4))
        entry_frame = ctk.CTkFrame(cat_card, fg_color="transparent")
        entry_frame.pack(fill="x", padx=16, pady=(0, 8))
        self._cat_entry = ctk.CTkEntry(entry_frame, height=36, corner_radius=8,
                                       placeholder_text="e.g. 'uber ride to airport'",
                                       border_color=COLORS["border"])
        self._cat_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(entry_frame, text="Suggest", width=70, height=34, corner_radius=8,
                      fg_color=COLORS["accent"], font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._suggest_category).pack(side="right")
        self._cat_result = ctk.CTkLabel(cat_card, text="", font=ctk.CTkFont(size=13), anchor="w")
        self._cat_result.pack(anchor="w", padx=16, pady=(0, 12))

    def _make_card(self, parent):
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1,
                            border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        card.pack(fill="x", pady=(0, 10))
        return card

    def _generate_tips(self, transactions, goals, budgets, spending_prediction):
        tips = []
        income_total = sum(t["amount"] for t in transactions if t["type"] == "income")
        expense_total = sum(t["amount"] for t in transactions if t["type"] == "expense")

        if income_total > 0:
            savings_rate = (income_total - expense_total) / income_total * 100
            if savings_rate < 10:
                tips.append({"type": "warning", "icon": "\u26A0",
                             "text": f"Savings rate is {savings_rate:.0f}%. Aim for at least 20%."})
            elif savings_rate > 30:
                tips.append({"type": "success", "icon": "\u2714",
                             "text": f"Great savings rate of {savings_rate:.0f}%! You're on track."})

        active_goals = [g for g in goals if g["status"] == "active"]
        for g in active_goals:
            remaining = g["target_amount"] - g["current_amount"]
            if remaining > 0 and expense_total > 0:
                monthly_surplus = income_total - expense_total
                months_to_goal = remaining / monthly_surplus if monthly_surplus > 0 else 999
                if months_to_goal < 99:
                    tips.append({"type": "info", "icon": "\U0001F3AF",
                                 "text": f"Goal '{g['name']}': ~{months_to_goal:.0f} months away at current rate."})

        if spending_prediction and spending_prediction.get("trend") == "rising":
            sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
            tips.append({"type": "warning", "icon": "\U0001F4C8",
                         "text": f"Spending is rising ({spending_prediction.get('slope', 0):+.0f}/mo). "
                                 f"Next month predicted: {sym}{spending_prediction.get('predicted_total', 0):,.0f}."})

        return tips

    def _suggest_category(self):
        desc = self._cat_entry.get().strip()
        if not desc:
            self._cat_result.configure(text="Enter a description first", text_color=COLORS["text_muted"])
            return
        try:
            result = self.api.suggest_category(desc)
            if result and result.get("category"):
                self._cat_result.configure(
                    text=f"\u2714  Suggested: {result['category']} (confidence: {result['score']*100:.0f}%)",
                    text_color=COLORS["success"])
            else:
                self._cat_result.configure(text="No match found", text_color=COLORS["text_muted"])
        except Exception as e:
            self._cat_result.configure(text=f"Error: {e}", text_color=COLORS["expense"])
