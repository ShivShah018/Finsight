import customtkinter as ctk
from utils.db_manager import DatabaseManager, User
from utils.currency import SYMBOLS, convert_amount
from datetime import datetime, date
from collections import defaultdict

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "accent":        "#6366f1",
    "income":        "#22c55e",
    "expense":       "#ef4444",
    "warning":       "#eab308",
}


class BudgetView(ctk.CTkFrame):

    def __init__(self, master, user: User, **kwargs):
        super().__init__(master, **kwargs)
        self.user = user
        self.db = DatabaseManager.get_instance()
        self.configure(fg_color="transparent")
        self._build_ui()
        self._refresh()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        head = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head.pack(fill="x", padx=20, pady=(12, 2))
        ctk.CTkLabel(head, text="Budget Planner",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(head, text="+ Set Budget", width=100, height=34, corner_radius=10,
                       fg_color=COLORS["accent"], font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._show_set_budget_popup).pack(side="right")
        ctk.CTkLabel(self.scroll, text="Monthly budget limits vs actual spending per category",
                     font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"], anchor="w"
                     ).pack(anchor="w", padx=20, pady=(0, 6))

        self._month_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._month_frame.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(self._month_frame, text="Month:",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 8))
        now = date.today()
        self._month_var = ctk.StringVar(value=f"{now.year}-{now.month:02d}")
        self._month_menu = ctk.CTkOptionMenu(self._month_frame, variable=self._month_var,
                                              values=self._month_options(),
                                              fg_color="#1a1f3a", button_color=COLORS["accent"],
                                              dropdown_fg_color="#1a1f3a",
                                              font=ctk.CTkFont(size=12),
                                              command=lambda _: self._refresh())
        self._month_menu.pack(side="left")

        self._cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._cards_frame.pack(fill="x", padx=20)

    def _month_options(self):
        opts = []
        for y in range(2024, date.today().year + 2):
            for m in range(1, 13):
                opts.append(f"{y}-{m:02d}")
        return opts[-24:]

    def _refresh(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        try:
            ym = self._month_var.get().split("-")
            year, month = int(ym[0]), int(ym[1])
            budgets = self.db.get_budget_limits(self.user.id)
            spending = self.db.get_spending_by_category(self.user.id, month, year)
            cat_expense = {r["name"]: float(r["total"]) for r in spending}

            if not budgets:
                ctk.CTkLabel(self._cards_frame, text="No budgets set — click '+ Set Budget' to add one.",
                             text_color=COLORS["text_muted"]).pack(pady=40)
                return

            sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
            for b in budgets:
                spent = cat_expense.get(b.category_name, 0.0)
                limit = b.monthly_limit
                pct = (spent / limit * 100) if limit > 0 else 0
                over = pct > 100

                card = ctk.CTkFrame(self._cards_frame, corner_radius=14, border_width=1,
                                     border_color=COLORS["border"], fg_color=COLORS["card_bg"])
                card.pack(fill="x", pady=(0, 8))

                top = ctk.CTkFrame(card, fg_color="transparent")
                top.pack(fill="x", padx=16, pady=(12, 4))
                ctk.CTkLabel(top, text=b.category_name, font=ctk.CTkFont(size=15, weight="bold"),
                             text_color=COLORS["text_primary"]).pack(side="left")

                status_color = COLORS["expense"] if over else COLORS["income"]
                status_text = f"{'OVER!' if over else 'On track'}"
                ctk.CTkLabel(top, text=status_text, font=ctk.CTkFont(size=11, weight="bold"),
                             text_color=status_color).pack(side="right", padx=(6, 0))

                bar_frame = ctk.CTkFrame(card, fg_color="transparent")
                bar_frame.pack(fill="x", padx=16, pady=(4, 2))
                bar_bg = ctk.CTkFrame(bar_frame, height=12, corner_radius=6, fg_color="#1a1f3a")
                bar_bg.pack(fill="x")
                bar_fill = ctk.CTkFrame(bar_bg, height=12, corner_radius=6,
                                        fg_color=COLORS["expense"] if over else COLORS["accent"])
                fill_w = min(pct, 100) / 100
                bar_fill.place(relx=0, rely=0, relwidth=fill_w, relheight=1)
                if pct > 100:
                    excess = ctk.CTkFrame(bar_bg, height=12, corner_radius=0,
                                          fg_color=COLORS["expense"])
                    excess.place(relx=1, rely=0, relwidth=min((pct - 100) / 100, 0.2), relheight=1,
                                 bordermode="outside")

                info = ctk.CTkFrame(card, fg_color="transparent")
                info.pack(fill="x", padx=16, pady=(2, 10))
                ctk.CTkLabel(info, text=f"{sym}{spent:,.2f} / {sym}{limit:,.2f}",
                             font=ctk.CTkFont(size=13, weight="bold"),
                             text_color=COLORS["expense"] if over else COLORS["text_primary"]
                             ).pack(side="left")
                ctk.CTkLabel(info, text=f"{pct:.0f}% used",
                             font=ctk.CTkFont(size=12),
                             text_color=COLORS["expense"] if over else COLORS["text_muted"]
                             ).pack(side="right")

                act = ctk.CTkFrame(card, fg_color="transparent")
                act.pack(fill="x", padx=16, pady=(0, 10))
                ctk.CTkButton(act, text="Edit", width=50, height=26, corner_radius=6,
                               fg_color="#1a1f3a", text_color=COLORS["text_secondary"],
                               font=ctk.CTkFont(size=11),
                               command=lambda bi=b: self._edit_budget(bi)).pack(side="left", padx=(0, 6))
                ctk.CTkButton(act, text="Remove", width=60, height=26, corner_radius=6,
                               fg_color="#1a1f3a", text_color=COLORS["expense"],
                               font=ctk.CTkFont(size=11),
                               command=lambda bi=b: self._remove_budget(bi)).pack(side="left")

        except Exception as e:
            import traceback; traceback.print_exc()
            ctk.CTkLabel(self._cards_frame, text=f"Error: {e}",
                         text_color="#ef4444").pack()

    def _show_set_budget_popup(self):
        SetBudgetPopup(self.winfo_toplevel(), self.db, self.user, on_done=lambda: self._refresh())

    def _edit_budget(self, budget):
        SetBudgetPopup(self.winfo_toplevel(), self.db, self.user, edit_budget=budget,
                       on_done=lambda: self._refresh())

    def _remove_budget(self, budget):
        from tkinter import messagebox
        ok = messagebox.askyesno("Remove Budget", f"Remove budget for {budget.category_name}?",
                                  parent=self.winfo_toplevel())
        if ok:
            self.db.delete_budget_limit(budget.id, self.user.id)
            self._refresh()


class SetBudgetPopup(ctk.CTkToplevel):

    def __init__(self, master, db, user, on_done, edit_budget=None):
        super().__init__(master)
        self.db = db
        self.user = user
        self.on_done = on_done
        self.edit_budget = edit_budget
        title = "Edit Budget" if edit_budget else "Set Budget"
        self.title(title)
        self.geometry("380x280")
        self.configure(fg_color="#13172b")
        self.resizable(False, False)
        self.minsize(380, 280)
        if master:
            x = master.winfo_rootx() + 150; y = master.winfo_rooty() + 120
            self.geometry(f"380x280+{x}+{y}")
        self._build()
        self.grab_set(); self.focus()

    def _build(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=20)

        row = 0
        main.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(main, text="Set Budget Limit", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["text_primary"]).grid(row=row, column=0, pady=(0, 16), sticky="w")
        row += 1

        ctk.CTkLabel(main, text="Category", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        cats = self.db.get_categories(self.user.id, "expense")
        cat_names = [c.name for c in cats]
        self._cat_var = ctk.StringVar(value=self.edit_budget.category_name if self.edit_budget else (cat_names[0] if cat_names else ""))
        self._cat_menu = ctk.CTkOptionMenu(main, variable=self._cat_var, values=cat_names,
                                           fg_color="#1a1f3a", button_color=COLORS["accent"],
                                           dropdown_fg_color="#1a1f3a", font=ctk.CTkFont(size=13))
        self._cat_menu.grid(row=row, column=0, sticky="ew", pady=(4, 12))
        row += 1

        ctk.CTkLabel(main, text="Monthly Limit (INR)", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        self._limit_entry = ctk.CTkEntry(main, height=40, corner_radius=8,
                                         border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        if self.edit_budget:
            self._limit_entry.insert(0, str(self.edit_budget.monthly_limit))
        self._limit_entry.grid(row=row, column=0, sticky="ew", pady=(4, 6))
        row += 1

        self._status = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=12))
        self._status.grid(row=row, column=0, pady=4)
        row += 1

        main.grid_rowconfigure(row, weight=1)
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="s", pady=(8, 0))
        ctk.CTkButton(btn_frame, text="  Save  ", width=100, height=40, corner_radius=10,
                       fg_color="#22c55e", text_color="#ffffff", hover_color="#16a34a",
                       font=ctk.CTkFont(size=14, weight="bold"),
                       command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="  Cancel  ", width=100, height=40, corner_radius=10,
                       fg_color="#334155", text_color="#f1f5f9", hover_color="#475569",
                       font=ctk.CTkFont(size=14), command=self.destroy).pack(side="left", padx=8)

    def _save(self):
        cat_name = self._cat_var.get()
        cats = self.db.get_categories(self.user.id, "expense")
        matching = [c for c in cats if c.name == cat_name]
        if not matching:
            self._status.configure(text="Select a category", text_color="#ef4444"); return
        try:
            limit = float(self._limit_entry.get().strip())
            if limit <= 0: raise ValueError
        except ValueError:
            self._status.configure(text="Enter a valid limit", text_color="#ef4444"); return
        if self.edit_budget:
            self.db.update_budget_limit(self.edit_budget.id, self.user.id, limit)
        else:
            self.db.set_budget_limit(self.user.id, matching[0].id, limit)
        self.on_done()
        self.destroy()
