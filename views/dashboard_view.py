import customtkinter as ctk
from utils.db_manager import DatabaseManager, User, TransactionRow
from utils.currency import (
    convert_amount, format_amount, get_conversion_note,
    CURRENCY_NAMES, SYMBOLS, PLAIN, RATES,
)
from utils.date_picker import DatePickerPopup
from datetime import datetime, timedelta, date
from collections import defaultdict
from tkinter import messagebox
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "accent":        "#6366f1",
    "income":        "#22c55e",
    "expense":       "#ef4444",
}


class Tooltip:
    """A simple hover tooltip that follows the mouse."""

    def __init__(self, widget, text, delay_ms=400):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._tip_window = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<Motion>", self._on_motion, add="+")

    def _on_enter(self, event=None):
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _on_leave(self, event=None):
        if self._after_id:
            self.widget.after_cancel(self._after_id)
            self._after_id = None
        self._hide()

    def _on_motion(self, event=None):
        if self._tip_window:
            x = event.x_root + 14
            y = event.y_root + 8
            self._tip_window.geometry(f"+{x}+{y}")

    def _show(self):
        if self._tip_window:
            return
        x = self.widget.winfo_pointerx() + 14
        y = self.widget.winfo_pointery() + 8
        self._tip_window = ctk.CTkToplevel(self.widget)
        self._tip_window.wm_overrideredirect(True)
        self._tip_window.wm_geometry(f"+{x}+{y}")
        self._tip_window.configure(fg_color="#1e2140")
        label = ctk.CTkLabel(
            self._tip_window, text=self.text,
            font=ctk.CTkFont(size=11),
            text_color="#f1f5f9",
            fg_color="#1e2140",
            padx=8, pady=4,
        )
        label.pack()
        self._after_id = None

    def _hide(self):
        if self._tip_window:
            self._tip_window.destroy()
            self._tip_window = None

RANGE_OPTIONS = [
    ("7 Days",  7),
    ("15 Days", 15),
    ("1 Month", 30),
    ("2 Months", 60),
    ("3 Months", 90),
    ("6 Months", 180),
    ("Custom",  None),
]

today = date.today()


class DashboardView(ctk.CTkFrame):

    def __init__(self, master, user: User, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.db = DatabaseManager.get_instance()
        self.configure(fg_color="transparent")
        self._display_currency = ctk.StringVar(value=user.preferred_currency or "INR")
        self._range_days = 30
        self._custom_start = today - timedelta(days=30)
        self._custom_end = today
        self._all_txs = []
        self._build_ui()
        self._refresh_data()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        head_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 2))
        ctk.CTkLabel(head_row, text="Dashboard",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")

        cur_frame = ctk.CTkFrame(head_row, fg_color="transparent")
        cur_frame.pack(side="right")
        ctk.CTkLabel(cur_frame, text="Show in:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 6))
        self._currency_menu = ctk.CTkOptionMenu(
            cur_frame, variable=self._display_currency, values=CURRENCY_NAMES,
            fg_color="#1a1f3a", button_color=COLORS["accent"],
            button_hover_color="#4f46e5", dropdown_fg_color="#1a1f3a",
            dropdown_hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=12), dropdown_font=ctk.CTkFont(size=12), width=80,
            command=self._on_currency_change,
        )
        self._currency_menu.pack(side="left")
        ctk.CTkButton(cur_frame, text="\u2B07 Export", width=72, height=28, corner_radius=8,
                       fg_color="#22c55e", text_color="#ffffff", hover_color="#16a34a",
                       font=ctk.CTkFont(size=11, weight="bold"),
                       command=self._export_data).pack(side="left", padx=(8, 0))

        # Search / Filter bar
        filter_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=(4, 4))
        self._search_var = ctk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._refresh_data())
        ctk.CTkEntry(filter_frame, textvariable=self._search_var, height=32, corner_radius=8,
                      placeholder_text="\U0001F50D  Search transactions...",
                      border_color=COLORS["border"], font=ctk.CTkFont(size=12)
                      ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(filter_frame, text="Undo delete", width=90, height=30, corner_radius=8,
                       fg_color="#1a1f3a", text_color=COLORS["text_muted"],
                       font=ctk.CTkFont(size=11), command=self._show_undo_delete).pack(side="right")

        ctk.CTkLabel(self.scroll, text="Your financial snapshot",
                     font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"], anchor="w"
                     ).pack(anchor="w", padx=20, pady=(0, 6))

        range_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        range_frame.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(range_frame, text="Period:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 8))

        self._range_btns = []
        for label, days in RANGE_OPTIONS:
            btn = ctk.CTkButton(
                range_frame, text=label, width=72, height=28, corner_radius=8,
                font=ctk.CTkFont(size=11, weight="bold" if days == 30 else "normal"),
                fg_color=COLORS["accent"] if days == 30 else "transparent",
                text_color="#f1f5f9" if days == 30 else COLORS["text_secondary"],
                hover_color="#1a1f3a",
                command=lambda d=days: self._set_range(d),
            )
            btn.pack(side="left", padx=(0, 5))
            self._range_btns.append(btn)

        self._custom_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._custom_frame.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(self._custom_frame, text="From:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left")
        self._start_label = ctk.CTkLabel(self._custom_frame, text=self._custom_start.strftime("%d %b %Y"),
                                         font=ctk.CTkFont(size=12, weight="bold"),
                                         text_color=COLORS["text_primary"], width=90)
        self._start_label.pack(side="left", padx=(4, 2))
        ctk.CTkButton(self._custom_frame, text="\U0001F4C5", width=28, height=24,
                       fg_color="transparent", text_color=COLORS["text_secondary"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=12),
                       command=lambda: self._pick_date("start")).pack(side="left", padx=(0, 12))
        ctk.CTkLabel(self._custom_frame, text="To:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left")
        self._end_label = ctk.CTkLabel(self._custom_frame, text=self._custom_end.strftime("%d %b %Y"),
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color=COLORS["text_primary"], width=90)
        self._end_label.pack(side="left", padx=(4, 2))
        ctk.CTkButton(self._custom_frame, text="\U0001F4C5", width=28, height=24,
                       fg_color="transparent", text_color=COLORS["text_secondary"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=12),
                       command=lambda: self._pick_date("end")).pack(side="left")
        ctk.CTkButton(self._custom_frame, text="Apply", width=60, height=26, corner_radius=8,
                       fg_color=COLORS["accent"], font=ctk.CTkFont(size=11, weight="bold"),
                       command=self._apply_custom_range).pack(side="left", padx=(12, 0))
        self._custom_frame.pack_forget()

        self._rate_note = ctk.CTkLabel(self.scroll, text="", font=ctk.CTkFont(size=11),
                                       text_color=COLORS["text_muted"], anchor="w")
        self._rate_note.pack(anchor="w", padx=20, pady=(0, 10))

        cards = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards.pack(fill="x", padx=20, pady=(0, 16))
        self._income_card = self._make_summary_card(cards, "Income", COLORS["income"])
        self._expense_card = self._make_summary_card(cards, "Expenses", COLORS["expense"])
        self._balance_card = self._make_summary_card(cards, "Balance", COLORS["accent"])
        for i, c in enumerate([self._income_card, self._expense_card, self._balance_card]):
            c.pack(side="left", fill="both", expand=True, padx=(0, 12) if i < 2 else 0)

        chart_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        pie_container = ctk.CTkFrame(chart_frame, corner_radius=14, border_width=1,
                                     border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        pie_container.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(pie_container, text="Spending by Category",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(14, 4))
        self._pie_canvas_container = ctk.CTkFrame(pie_container, fg_color="transparent")
        self._pie_canvas_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        bar_container = ctk.CTkFrame(chart_frame, corner_radius=14, border_width=1,
                                     border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        bar_container.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(bar_container, text="Income vs Expenses Trend",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=16, pady=(14, 4))
        self._bar_canvas_container = ctk.CTkFrame(bar_container, fg_color="transparent")
        self._bar_canvas_container.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        tx_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        tx_frame.pack(fill="x", padx=20, pady=(0, 20))
        ctk.CTkLabel(tx_frame, text="Recent Transactions",
                     font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(anchor="w", pady=(0, 8))
        self._tx_list = ctk.CTkFrame(tx_frame, fg_color=COLORS["card_bg"],
                                     corner_radius=14, border_width=1, border_color=COLORS["border"])
        self._tx_list.pack(fill="x")

    def _make_summary_card(self, parent, label, color):
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1,
                            border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=18, pady=(14, 2))
        vl = ctk.CTkLabel(card, text="0.00", font=ctk.CTkFont(size=26, weight="bold"))
        vl.pack(anchor="w", padx=18, pady=(0, 14))
        card._value_label = vl
        return card

    def _set_range(self, days):
        self._range_days = days
        for btn, (label, d) in zip(self._range_btns, RANGE_OPTIONS):
            a = (d == days)
            btn.configure(fg_color=COLORS["accent"] if a else "transparent",
                          text_color="#f1f5f9" if a else COLORS["text_secondary"],
                          font=ctk.CTkFont(size=11, weight="bold" if a else "normal"))
        if days is None:
            self._custom_frame.pack(fill="x", padx=20, pady=(0, 6))
        else:
            self._custom_frame.pack_forget()
            self._refresh_data()

    def _pick_date(self, which):
        initial = self._custom_start if which == "start" else self._custom_end
        DatePickerPopup(self.winfo_toplevel(), on_select=lambda d: self._on_date_picked(which, d), initial_date=initial)

    def _on_date_picked(self, which, d):
        if which == "start":
            self._custom_start = d
            self._start_label.configure(text=d.strftime("%d %b %Y"))
        else:
            self._custom_end = d
            self._end_label.configure(text=d.strftime("%d %b %Y"))

    def _apply_custom_range(self):
        if self._custom_start > self._custom_end:
            self._custom_start, self._custom_end = self._custom_end, self._custom_start
            self._start_label.configure(text=self._custom_start.strftime("%d %b %Y"))
            self._end_label.configure(text=self._custom_end.strftime("%d %b %Y"))
        self._refresh_data()

    def _on_currency_change(self, _=None):
        self._refresh_data()
        self.db.update_preferred_currency(self.user.id, self._display_currency.get())
        self.user.preferred_currency = self._display_currency.get()

    def _export_data(self):
        from utils.exporter import export_to_excel
        start, end = self._get_date_range()
        export_to_excel(self.user.id, start, end, parent=self.winfo_toplevel())

    def _show_undo_delete(self):
        deleted = self.db.get_deleted_transactions(self.user.id)
        if not deleted:
            messagebox.showinfo("Undo Delete", "No recently deleted transactions.", parent=self.winfo_toplevel())
            return
        popup = ctk.CTkToplevel(self.winfo_toplevel())
        popup.title("Recently Deleted")
        popup.geometry("500x400")
        popup.configure(fg_color="#13172b")
        ctk.CTkLabel(popup, text="Recently Deleted Transactions",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(pady=(12, 8))
        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=6)
        for tx in deleted:
            row = ctk.CTkFrame(scroll, fg_color="#1a1f3a", corner_radius=8)
            row.pack(fill="x", pady=3)
            ctk.CTkLabel(row, text=f"{tx.transaction_date.strftime('%d %b')}  {tx.category_name}  \u20B9{tx.amount:,.2f}",
                         font=ctk.CTkFont(size=12), text_color=COLORS["text_secondary"], anchor="w"
                         ).pack(side="left", padx=12, pady=6)
            ctk.CTkButton(row, text="Restore", width=60, height=26, corner_radius=6,
                           fg_color=COLORS["accent"], font=ctk.CTkFont(size=11),
                           command=lambda txi=tx, p=popup: self._restore_tx(txi, p)).pack(side="right", padx=8, pady=4)

    def _restore_tx(self, tx, popup):
        self.db.restore_transaction(tx.id, self.user.id)
        self._refresh_data()
        popup.destroy()

    def _get_data_range(self):
        return self._get_date_range()  # alias for export

    def _get_date_range(self):
        if self._range_days is not None:
            end = today
            start = end - timedelta(days=self._range_days)
            return start, end
        return self._custom_start, self._custom_end

    def _refresh_data(self):
        cur = self._display_currency.get()
        self._rate_note.configure(text=get_conversion_note("INR", cur))
        try:
            all_txs = self.db.get_transactions(self.user.id, limit=5000)
            range_start, range_end = self._get_date_range()
            self._all_txs = [t for t in all_txs if range_start <= t.transaction_date <= range_end]

            # Search filter
            q = self._search_var.get().strip().lower()
            if q:
                self._all_txs = [t for t in self._all_txs
                                 if q in t.category_name.lower()
                                 or (t.description and q in t.description.lower())
                                 or q in t.currency.lower()
                                 or q in t.transaction_date.strftime("%d %b %Y").lower()
                                 or q in f"{t.amount:.2f}"]

            income_total = sum(convert_amount(t.amount, t.currency, cur) for t in self._all_txs if t.type == "income")
            expense_total = sum(convert_amount(t.amount, t.currency, cur) for t in self._all_txs if t.type == "expense")
            net = income_total - expense_total
            sym = SYMBOLS.get(cur, "")
            self._income_card._value_label.configure(text=f"{sym}{income_total:,.2f}")
            self._expense_card._value_label.configure(text=f"{sym}{expense_total:,.2f}")
            self._balance_card._value_label.configure(text=f"{sym}{net:,.2f}")

            self._draw_pie_chart(cur)
            self._draw_bar_chart(cur)
            self._refresh_tx_list(cur)
        except Exception as e:
            import traceback; traceback.print_exc()
            for c in [self._pie_canvas_container, self._bar_canvas_container, self._tx_list]:
                for w in c.winfo_children(): w.destroy()
            ctk.CTkLabel(self._pie_canvas_container, text=f"Error: {e}",
                         font=ctk.CTkFont(size=12), text_color="#ef4444").pack(expand=True)

    def _draw_pie_chart(self, cur):
        for w in self._pie_canvas_container.winfo_children(): w.destroy()
        expenses = [t for t in self._all_txs if t.type == "expense"]
        if not expenses:
            ctk.CTkLabel(self._pie_canvas_container, text="No expenses in this period",
                         text_color=COLORS["text_muted"]).pack(expand=True)
            return
        cat_totals = defaultdict(float)
        for t in expenses:
            cat_totals[t.category_name] += convert_amount(t.amount, t.currency, cur)
        db_cats = self.db.get_categories(self.user.id, "expense")
        color_map = {c.name: c.color for c in db_cats}
        labels = list(cat_totals.keys())
        sizes = list(cat_totals.values())
        colors_pie = [color_map.get(l, "#6366f1") for l in labels]

        # Budget warnings
        budgets = self.db.get_budget_limits(self.user.id)
        budget_map = {b.category_name: b.monthly_limit for b in budgets}
        over_budget_cats = set()
        for name, total in cat_totals.items():
            if name in budget_map and total > budget_map[name]:
                over_budget_cats.add(name)

        fig = Figure(figsize=(4.5, 3), dpi=90)
        fig.patch.set_facecolor("#13172b")
        fig.subplots_adjust(left=0.32, right=0.95, top=0.9, bottom=0.1)
        ax = fig.add_subplot(111)
        ax.set_facecolor("#13172b")
        explode = [0.05 if l in over_budget_cats else 0 for l in labels]
        wedges, texts, autotexts = ax.pie(sizes, labels=None, autopct="", startangle=140,
                                           colors=colors_pie, explode=explode,
                                           wedgeprops={"linewidth": 1, "edgecolor": "#13172b"})
        sym = PLAIN.get(cur, cur)
        legend_labels = []
        for l, s in zip(labels, sizes):
            warn = " \u26A0" if l in over_budget_cats else ""
            legend_labels.append(f"{l}{warn} ({sym}{s:,.0f})")
        ax.legend(wedges, legend_labels,
                  loc="center left", bbox_to_anchor=(-0.75, 0.5), fontsize=7,
                  facecolor="#13172b", edgecolor="none", labelcolor="#94a3b8", framealpha=0.9)
        if over_budget_cats:
            fig.text(0.5, -0.02, "\u26A0 Over budget", fontsize=7, color="#ef4444",
                     ha="center", va="top", fontstyle="italic",
                     bbox=dict(facecolor="#13172b", edgecolor="#ef4444", boxstyle="round,pad=0.3"))
        canvas = FigureCanvasTkAgg(fig, master=self._pie_canvas_container)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    def _draw_bar_chart(self, cur):
        for w in self._bar_canvas_container.winfo_children(): w.destroy()
        range_start, range_end = self._get_date_range()
        total_days = (range_end - range_start).days

        if total_days <= 60:
            buckets = {}
            for i in range(total_days + 1):
                d = range_start + timedelta(days=i)
                buckets[d] = {"income": 0.0, "expense": 0.0}
            for t in self._all_txs:
                d = t.transaction_date
                if d in buckets:
                    val = convert_amount(t.amount, t.currency, cur)
                    buckets[d][t.type] += val
            labels = [d.strftime("%d %b") for d in buckets]
            income_vals = [v["income"] for v in buckets.values()]
            expense_vals = [v["expense"] for v in buckets.values()]
        else:
            from collections import OrderedDict
            weekly = OrderedDict()
            d = range_start
            while d <= range_end:
                week_start = d
                week_end = min(d + timedelta(days=6), range_end)
                label = week_start.strftime("%d %b")
                weekly[label] = {"income": 0.0, "expense": 0.0}
                for t in self._all_txs:
                    if week_start <= t.transaction_date <= week_end:
                        val = convert_amount(t.amount, t.currency, cur)
                        weekly[label][t.type] += val
                d = week_end + timedelta(days=1)
            labels = list(weekly.keys())
            income_vals = [v["income"] for v in weekly.values()]
            expense_vals = [v["expense"] for v in weekly.values()]

        fig = Figure(figsize=(4.2, 3), dpi=90)
        fig.patch.set_facecolor("#13172b")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#13172b")
        x = range(len(labels))
        ax.bar(x, income_vals, width=0.35, label="Income", color=COLORS["income"], alpha=0.85)
        ax.bar([i + 0.35 for i in x], expense_vals, width=0.35, label="Expenses", color=COLORS["expense"], alpha=0.85)
        ax.set_xticks([i + 0.175 for i in x])
        tick_step = max(1, len(labels) // 10)
        vis = [l if i % tick_step == 0 else "" for i, l in enumerate(labels)]
        ax.set_xticklabels(vis, fontsize=6 if len(labels) > 20 else 7, color="#94a3b8", rotation=45, ha="right")
        ax.legend(fontsize=7, facecolor="#13172b", edgecolor="none", labelcolor="#94a3b8")
        ax.tick_params(colors="#64748b", labelsize=7)
        for spine in ax.spines.values(): spine.set_visible(False)
        ax.yaxis.set_visible(False)
        canvas = FigureCanvasTkAgg(fig, master=self._bar_canvas_container)
        canvas.draw(); canvas.get_tk_widget().pack(fill="both", expand=True)

    # ── Edit / Delete ─────────────────────────────────────────
    def _delete_transaction(self, tx):
        ok = messagebox.askyesno("Delete Transaction",
                                 f"Delete this {tx.type} of {tx.currency}{tx.amount:,.2f}?\n"
                                 f'"{tx.description or tx.category_name}"',
                                 parent=self.winfo_toplevel())
        if ok:
            self.db.delete_transaction(tx.id, self.user.id)
            self._refresh_data()

    def _edit_transaction(self, tx):
        EditTransactionPopup(self.winfo_toplevel(), self.db, self.user, tx,
                             on_save=lambda: self._refresh_data())

    # ── Transaction list ─────────────────────────────────────
    def _refresh_tx_list(self, cur):
        for w in self._tx_list.winfo_children(): w.destroy()
        txs = sorted(self._all_txs, key=lambda t: (t.transaction_date, t.id), reverse=True)[:15]
        if not txs:
            ctk.CTkLabel(self._tx_list, text="No transactions in this period",
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return

        hdr = ctk.CTkFrame(self._tx_list, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(10, 4))
        for i, txt in enumerate(["Date", "Category", "Description", "Amount", ""]):
            w = 80 if i == 4 else (90 if i == 3 else 100)
            ctk.CTkLabel(hdr, text=txt, font=ctk.CTkFont(size=11, weight="bold"),
                         text_color=COLORS["text_muted"], width=w, anchor="w").pack(side="left")
        ctk.CTkFrame(self._tx_list, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=16)

        for tx in txs:
            row = ctk.CTkFrame(self._tx_list, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=4)
            color = COLORS["income"] if tx.type == "income" else COLORS["expense"]
            sign = "+" if tx.type == "income" else "-"
            converted = convert_amount(tx.amount, tx.currency, cur)
            sym = SYMBOLS.get(cur, "")

            ctk.CTkLabel(row, text=tx.transaction_date.strftime("%d %b %Y"),
                         font=ctk.CTkFont(size=12), width=100, anchor="w",
                         text_color=COLORS["text_secondary"]).pack(side="left")
            ctk.CTkLabel(row, text=tx.category_name,
                         font=ctk.CTkFont(size=12), width=100, anchor="w",
                         text_color=COLORS["text_secondary"]).pack(side="left")
            ctk.CTkLabel(row, text=tx.description or "",
                         font=ctk.CTkFont(size=12), width=100, anchor="w",
                         text_color=COLORS["text_secondary"]).pack(side="left")
            ctk.CTkLabel(row, text=f"{sign}{sym}{converted:,.2f}",
                         font=ctk.CTkFont(size=12, weight="bold"), width=90, anchor="e",
                         text_color=color).pack(side="left")

            act = ctk.CTkFrame(row, fg_color="transparent", width=90)
            act.pack(side="left")
            edit_btn = ctk.CTkButton(act, text="\u270F\uFE0F", width=30, height=26,
                                     fg_color=COLORS["card_bg"], text_color="#94a3b8",
                                     hover_color="#1e2140", hover=True,
                                     font=ctk.CTkFont(size=12), corner_radius=6,
                                     command=lambda txi=tx: self._edit_transaction(txi))
            edit_btn.pack(side="left", padx=2)
            Tooltip(edit_btn, "Edit")

            del_btn = ctk.CTkButton(act, text="\uD83D\uDDD1\uFE0F", width=30, height=26,
                                    fg_color=COLORS["card_bg"], text_color="#94a3b8",
                                    hover_color="#3b1a1a", hover=True,
                                    font=ctk.CTkFont(size=12), corner_radius=6,
                                    command=lambda txi=tx: self._delete_transaction(txi))
            del_btn.pack(side="left", padx=2)
            Tooltip(del_btn, "Delete")


class EditTransactionPopup(ctk.CTkToplevel):
    """Popup window to edit a transaction."""

    def __init__(self, master, db, user, tx: TransactionRow, on_save):
        super().__init__(master)
        self.db = db
        self.user = user
        self.tx = tx
        self.on_save = on_save

        self.title("Edit Transaction")
        self.geometry("460x520")
        self.configure(fg_color="#13172b")
        self.resizable(False, False)

        if master:
            x = master.winfo_rootx() + 120
            y = master.winfo_rooty() + 80
            self.geometry(f"460x520+{x}+{y}")

        self._categories = []
        self._build_form()
        self._load_categories()
        self.grab_set()
        self.focus()

    def _build_form(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=20, pady=20)
        main.grid_columnconfigure(0, weight=0)
        main.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(main, text="Edit Transaction",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["text_primary"]).grid(row=row, column=0, columnspan=2, pady=(0, 16))
        row += 1

        # Type
        ctk.CTkLabel(main, text="Type", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._type_var = ctk.StringVar(value=self.tx.type.title())
        seg = ctk.CTkSegmentedButton(main, values=["Expense", "Income"],
                                     variable=self._type_var,
                                     selected_color=COLORS["accent"],
                                     font=ctk.CTkFont(size=12, weight="bold"),
                                     command=self._on_type_change)
        seg.grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        # Category
        ctk.CTkLabel(main, text="Category", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._cat_var = ctk.StringVar()
        self._cat_menu = ctk.CTkOptionMenu(main, variable=self._cat_var, values=["Loading..."],
                                           fg_color="#1a1f3a", button_color=COLORS["accent"],
                                           dropdown_fg_color="#1a1f3a", font=ctk.CTkFont(size=12))
        self._cat_menu.grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        # Amount
        ctk.CTkLabel(main, text="Amount", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._amount_entry = ctk.CTkEntry(main, height=38, corner_radius=8,
                                          border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        self._amount_entry.grid(row=row, column=1, sticky="ew", pady=6)
        self._amount_entry.insert(0, str(self.tx.amount))
        row += 1

        # Currency
        ctk.CTkLabel(main, text="Currency", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._cur_var = ctk.StringVar(value=self.tx.currency or "INR")
        cur_m = ctk.CTkOptionMenu(main, variable=self._cur_var, values=CURRENCY_NAMES,
                                  fg_color="#1a1f3a", button_color=COLORS["accent"],
                                  dropdown_fg_color="#1a1f3a", font=ctk.CTkFont(size=12))
        cur_m.grid(row=row, column=1, sticky="ew", pady=6)
        row += 1

        # Date
        ctk.CTkLabel(main, text="Date", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._date_entry = ctk.CTkEntry(main, height=38, corner_radius=8,
                                        border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        self._date_entry.grid(row=row, column=1, sticky="ew", pady=6)
        self._date_entry.insert(0, self.tx.transaction_date.strftime("%Y-%m-%d"))
        row += 1

        # Description
        ctk.CTkLabel(main, text="Description", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)
        self._desc_entry = ctk.CTkEntry(main, height=38, corner_radius=8,
                                        border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        self._desc_entry.grid(row=row, column=1, sticky="ew", pady=6)
        if self.tx.description:
            self._desc_entry.insert(0, self.tx.description)
        row += 1

        # Status
        self._status = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=12))
        self._status.grid(row=row, column=0, columnspan=2, pady=6)
        row += 1

        # Buttons
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        ctk.CTkButton(btn_frame, text="Save", width=100, height=40, corner_radius=10,
                       fg_color=COLORS["accent"], font=ctk.CTkFont(size=14, weight="bold"),
                       command=self._save).pack(side="left", padx=6)
        ctk.CTkButton(btn_frame, text="Cancel", width=100, height=40, corner_radius=10,
                       fg_color="#1a1f3a", text_color=COLORS["text_secondary"],
                       font=ctk.CTkFont(size=14), command=self.destroy).pack(side="left", padx=6)

    def _load_categories(self):
        cat_type = self._type_var.get().lower()
        self._categories = self.db.get_categories(self.user.id, cat_type)
        names = [c.name for c in self._categories]
        self._cat_menu.configure(values=names, state="normal")
        # Select the current category if it exists
        if self.tx.category_name in names:
            self._cat_var.set(self.tx.category_name)
        else:
            self._cat_var.set(names[0] if names else "No categories")

    def _on_type_change(self, value):
        self._categories = self.db.get_categories(self.user.id, value.lower())
        names = [c.name for c in self._categories]
        self._cat_menu.configure(values=names)
        self._cat_var.set(names[0] if names else "No categories")

    def _save(self):
        try:
            amount = float(self._amount_entry.get().strip())
            if amount <= 0: raise ValueError
        except ValueError:
            self._status.configure(text="\u26A0 Invalid amount", text_color="#ef4444")
            return
        cat_name = self._cat_var.get()
        matching = [c for c in self._categories if c.name == cat_name]
        if not matching:
            self._status.configure(text="\u26A0 Select a category", text_color="#ef4444")
            return
        try:
            d = datetime.strptime(self._date_entry.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            self._status.configure(text="\u26A0 Use YYYY-MM-DD", text_color="#ef4444")
            return
        self.db.update_transaction(
            self.tx.id, self.user.id, matching[0].id, amount,
            self._type_var.get().lower(), self._desc_entry.get().strip() or None,
            d, self._cur_var.get(),
        )
        self.on_save()
        self.destroy()
