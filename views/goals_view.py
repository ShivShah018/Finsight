import random
import customtkinter as ctk
from utils.currency import SYMBOLS
from datetime import datetime, date
from tkinter import messagebox

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "accent":        "#6366f1",
    "success":       "#22c55e",
    "expense":       "#ef4444",
}


class GoalsView(ctk.CTkFrame):

    def __init__(self, master, api, user, user_data, **kwargs):
        super().__init__(master, **kwargs)
        self.api = api
        self.user = user
        self.user_data = user_data
        self.configure(fg_color="transparent")
        self._build_ui()
        self.after(50, self._refresh)

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        head_row = ctk.CTkFrame(self.scroll, fg_color="transparent")
        head_row.pack(fill="x", padx=20, pady=(12, 2))
        ctk.CTkLabel(head_row, text="Savings Goals",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(side="left")
        ctk.CTkButton(head_row, text="+ New Goal", width=100, height=34, corner_radius=10,
                       fg_color=COLORS["accent"], font=ctk.CTkFont(size=13, weight="bold"),
                       command=self._show_new_goal_popup).pack(side="right")
        ctk.CTkLabel(self.scroll, text="Set and track your financial targets",
                     font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"], anchor="w"
                     ).pack(anchor="w", padx=20, pady=(0, 6))

        self._stats_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._stats_frame.pack(fill="x", padx=20, pady=(0, 16))

        self._goals_container = ctk.CTkFrame(self.scroll, fg_color="transparent")
        self._goals_container.pack(fill="x", padx=20, pady=(0, 20))

    def _refresh(self):
        try:
            goals = self.api.get_goals()
        except Exception as e:
            for w in self._goals_container.winfo_children(): w.destroy()
            ctk.CTkLabel(self._goals_container, text=f"Error: {e}",
                         text_color="#ef4444").pack()
            return
        self._render_stats(goals)
        self._render_goals(goals)

    def _render_stats(self, goals):
        for w in self._stats_frame.winfo_children(): w.destroy()
        sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
        active = [g for g in goals if g["status"] == "active"]
        completed = [g for g in goals if g["status"] == "completed"]
        total_saved = sum(g["current_amount"] for g in goals)

        stats = [
            ("Total Saved", f"{sym}{total_saved:,.0f}", COLORS["success"]),
            ("Active Goals", str(len(active)), COLORS["accent"]),
            ("Completed", str(len(completed)), COLORS["text_secondary"]),
        ]
        for label, value, color in stats:
            c = self._make_stat_card(self._stats_frame, label, value, color)
            c.pack(side="left", fill="both", expand=True, padx=(0, 10))

    def _make_stat_card(self, parent, label, value, color):
        card = ctk.CTkFrame(parent, corner_radius=14, border_width=1,
                            border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        ctk.CTkFrame(card, height=4, fg_color=color, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"]).pack(anchor="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(anchor="w", padx=18, pady=(0, 14))
        return card

    def _render_goals(self, goals):
        for w in self._goals_container.winfo_children(): w.destroy()
        if not goals:
            ctk.CTkLabel(self._goals_container, text="No goals yet - click '+ New Goal' to start.",
                         text_color=COLORS["text_muted"]).pack(pady=40)
            return
        for g in goals:
            self._render_goal_card(g)

    def _render_goal_card(self, g):
        sym = SYMBOLS.get(self.user.preferred_currency or "INR", "")
        card = ctk.CTkFrame(self._goals_container, corner_radius=14, border_width=1,
                            border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        card.pack(fill="x", pady=(0, 10))

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 4))

        status_color = COLORS["success"] if g["status"] == "completed" else COLORS["accent"]
        badge = ctk.CTkLabel(top, text=g["status"].title(), font=ctk.CTkFont(size=10, weight="bold"),
                             text_color=status_color, fg_color="#1a1f3a", corner_radius=6,
                             padx=8, pady=2)
        badge.pack(side="right", padx=(6, 0))
        ctk.CTkLabel(top, text=f"  {g['name']}", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=COLORS["text_primary"], anchor="w").pack(side="left")

        if g.get("deadline"):
            dl = datetime.strptime(g["deadline"], "%Y-%m-%d").date() if isinstance(g["deadline"], str) else g["deadline"]
            remaining = (dl - date.today()).days
            if remaining > 0:
                dl_text = f"Due in {remaining}d ({dl.strftime('%d %b %Y')})"
            elif remaining == 0:
                dl_text = "Due today!"
            else:
                dl_text = f"Overdue by {-remaining}d"
            dl_color = COLORS["expense"] if remaining < 0 else COLORS["text_secondary"]
            ctk.CTkLabel(card, text=dl_text, font=ctk.CTkFont(size=11),
                         text_color=dl_color, anchor="w").pack(anchor="w", padx=16, pady=(0, 4))

        amt_frame = ctk.CTkFrame(card, fg_color="transparent")
        amt_frame.pack(fill="x", padx=16, pady=(4, 4))
        ctk.CTkLabel(amt_frame, text=f"{sym}{g['current_amount']:,.2f} / {sym}{g['target_amount']:,.2f}",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        pct_color = COLORS["success"] if g["progress_pct"] >= 100 else COLORS["accent"]
        ctk.CTkLabel(amt_frame, text=f"{g['progress_pct']:.1f}%",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=pct_color).pack(side="right")

        bar_bg = ctk.CTkFrame(card, height=10, corner_radius=5, fg_color="#1a1f3a")
        bar_bg.pack(fill="x", padx=16, pady=(0, 4))
        pct = min(g["progress_pct"], 100) / 100
        fill_color = COLORS["success"] if g["progress_pct"] >= 100 else COLORS["accent"]
        bar_fill = ctk.CTkFrame(bar_bg, height=10, corner_radius=5, fg_color=fill_color)
        bar_fill.place(relx=0, rely=0, relwidth=pct, relheight=1)

        act = ctk.CTkFrame(card, fg_color="transparent")
        act.pack(fill="x", padx=16, pady=(4, 14))
        if g["status"] == "active":
            ctk.CTkButton(act, text="+ Add Funds", width=90, height=30, corner_radius=8,
                           fg_color=COLORS["accent"], font=ctk.CTkFont(size=11, weight="bold"),
                           command=lambda gi=g["id"]: self._show_add_funds_popup(gi)).pack(side="left", padx=(0, 6))
            ctk.CTkButton(act, text="Complete", width=80, height=30, corner_radius=8,
                           fg_color="transparent", text_color=COLORS["success"],
                           border_color=COLORS["success"], border_width=1,
                           font=ctk.CTkFont(size=11, weight="bold"),
                           command=lambda gi=g["id"]: self._complete_goal(gi)).pack(side="left", padx=6)
            ctk.CTkButton(act, text="Cancel", width=70, height=30, corner_radius=8,
                           fg_color="transparent", text_color=COLORS["expense"],
                           hover_color="#1a1f3a", font=ctk.CTkFont(size=11),
                           command=lambda gi=g["id"]: self._cancel_goal(gi)).pack(side="left", padx=6)
        else:
            ctk.CTkLabel(act, text="\u2713 Completed" if g["status"] == "completed" else "\u2717 Cancelled",
                         font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=COLORS["success"] if g["status"] == "completed" else COLORS["text_muted"]
                         ).pack(side="left")

    def _show_new_goal_popup(self):
        NewGoalPopup(self.winfo_toplevel(), self.api, self.user, on_done=lambda: self._refresh())

    def _show_add_funds_popup(self, goal_id):
        AddFundsPopup(self.winfo_toplevel(), self.api, goal_id, on_done=lambda: self._refresh())

    def _confetti(self):
        top = self.winfo_toplevel()
        colors = ["#22c55e", "#6366f1", "#eab308", "#ef4444", "#ec4899", "#06b6d4"]
        particles = []
        for _ in range(40):
            x = random.randint(50, top.winfo_width() - 50)
            y = random.randint(50, top.winfo_height() - 50)
            size = random.randint(4, 10)
            lbl = ctk.CTkLabel(top, text="\u2B1B", font=ctk.CTkFont(size=size),
                               text_color=random.choice(colors), fg_color="transparent")
            lbl.place(x=x, y=y)
            particles.append(lbl)

        def fade():
            for p in particles:
                try:
                    p.place_forget()
                except Exception:
                    pass
        top.after(1500, fade)

    def _complete_goal(self, goal_id):
        ok = messagebox.askyesno("Complete Goal", "Mark this goal as completed?",
                                 parent=self.winfo_toplevel())
        if ok:
            try:
                self.api.complete_goal(goal_id)
                self._confetti()
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.winfo_toplevel())

    def _cancel_goal(self, goal_id):
        ok = messagebox.askyesno("Cancel Goal", "Cancel this goal? It will be hidden from the list.",
                                 parent=self.winfo_toplevel())
        if ok:
            try:
                self.api.cancel_goal(goal_id)
                self._refresh()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=self.winfo_toplevel())


class NewGoalPopup(ctk.CTkToplevel):

    def __init__(self, master, api, user, on_done):
        super().__init__(master)
        self.api = api
        self.user = user
        self.on_done = on_done
        self.title("New Savings Goal")
        self.geometry("420x520")
        self.configure(fg_color="#13172b")
        self.resizable(False, False)
        self.minsize(420, 520)
        if master:
            x = master.winfo_rootx() + 120; y = master.winfo_rooty() + 60
            self.geometry(f"420x520+{x}+{y}")
        self._build()
        self.grab_set(); self.focus()

    def _build(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28, pady=24)
        row = 0
        main.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main, text="New Savings Goal", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=COLORS["text_primary"]).grid(row=row, column=0, pady=(0, 18), sticky="w")
        row += 1

        ctk.CTkLabel(main, text="Goal Name", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        self._name_entry = ctk.CTkEntry(main, height=40, corner_radius=8,
                                        border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        self._name_entry.grid(row=row, column=0, sticky="ew", pady=(4, 12))
        row += 1

        ctk.CTkLabel(main, text="Target Amount", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        self._target_entry = ctk.CTkEntry(main, height=40, corner_radius=8,
                                          border_color=COLORS["border"], font=ctk.CTkFont(size=14))
        self._target_entry.grid(row=row, column=0, sticky="ew", pady=(4, 12))
        row += 1

        ctk.CTkLabel(main, text="Deadline (YYYY-MM-DD, optional)", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        self._deadline_entry = ctk.CTkEntry(main, height=40, corner_radius=8,
                                            border_color=COLORS["border"],
                                            font=ctk.CTkFont(size=14), placeholder_text="Optional")
        self._deadline_entry.grid(row=row, column=0, sticky="ew", pady=(4, 6))
        row += 1

        self._auto_fund_var = ctk.BooleanVar(value=False)
        self._auto_fund_cb = ctk.CTkCheckBox(main, text="Auto-fund from income category",
                                              variable=self._auto_fund_var,
                                              fg_color=COLORS["accent"],
                                              font=ctk.CTkFont(size=12),
                                              text_color=COLORS["text_secondary"],
                                              command=self._toggle_auto_fund)
        self._auto_fund_cb.grid(row=row, column=0, sticky="w", pady=(4, 0))
        row += 1

        self._auto_fund_amount_entry = ctk.CTkEntry(main, height=38, corner_radius=8,
                                                     border_color=COLORS["border"],
                                                     font=ctk.CTkFont(size=13),
                                                     placeholder_text="Monthly auto-fund amount")
        self._auto_fund_amount_entry.grid(row=row, column=0, sticky="ew", pady=(4, 6))
        self._auto_fund_amount_entry.configure(state="disabled")

        self._status = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=12))
        self._status.grid(row=row, column=0, pady=6)
        row += 1

        main.grid_rowconfigure(row, weight=1)
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="s", pady=(8, 0))
        ctk.CTkButton(btn_frame, text="  Add Goal  ", width=100, height=42, corner_radius=10,
                       fg_color="#22c55e", text_color="#ffffff", hover_color="#16a34a",
                       font=ctk.CTkFont(size=15, weight="bold"),
                       command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="  Cancel  ", width=100, height=42, corner_radius=10,
                       fg_color="#334155", text_color="#f1f5f9", hover_color="#475569",
                       font=ctk.CTkFont(size=15), command=self.destroy).pack(side="left", padx=8)

    def _toggle_auto_fund(self):
        state = "normal" if self._auto_fund_var.get() else "disabled"
        self._auto_fund_amount_entry.configure(state=state)

    def _save(self):
        name = self._name_entry.get().strip()
        if not name:
            self._status.configure(text="\u26A0 Enter a goal name", text_color="#ef4444"); return
        try:
            target = float(self._target_entry.get().strip())
            if target <= 0: raise ValueError
        except ValueError:
            self._status.configure(text="\u26A0 Enter a valid target amount", text_color="#ef4444"); return
        dl = self._deadline_entry.get().strip()
        deadline = None
        if dl:
            try:
                dl_date = datetime.strptime(dl, "%Y-%m-%d").date()
                if dl_date <= date.today():
                    self._status.configure(text="\u26A0 Deadline must be in the future", text_color="#ef4444")
                    return
                deadline = dl
            except ValueError:
                self._status.configure(text="\u26A0 Use YYYY-MM-DD format", text_color="#ef4444")
                return
        auto_fund_amount = 0
        if self._auto_fund_var.get():
            try:
                auto_fund_amount = float(self._auto_fund_amount_entry.get().strip())
                if auto_fund_amount <= 0:
                    auto_fund_amount = 0
            except ValueError:
                auto_fund_amount = 0
        try:
            self.api.create_goal(name, target, deadline, auto_fund_amount)
            self.on_done()
            self.destroy()
        except Exception as e:
            self._status.configure(text=f"\u26A0 {e}", text_color="#ef4444")


class AddFundsPopup(ctk.CTkToplevel):

    def __init__(self, master, api, goal_id, on_done):
        super().__init__(master)
        self.api = api
        self.goal_id = goal_id
        self.on_done = on_done
        self.title("Add Funds to Goal")
        self.geometry("360x280")
        self.configure(fg_color="#13172b")
        self.resizable(False, False)
        self.minsize(360, 280)
        if master:
            x = master.winfo_rootx() + 150; y = master.winfo_rooty() + 150
            self.geometry(f"360x280+{x}+{y}")
        self._build()
        self.grab_set(); self.focus()

    def _build(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=28, pady=24)
        row = 0
        main.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(main, text="Add Funds", font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=COLORS["text_primary"]).grid(row=row, column=0, pady=(0, 18), sticky="w")
        row += 1
        ctk.CTkLabel(main, text="Amount to add", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"], anchor="w").grid(row=row, column=0, sticky="w")
        row += 1
        self._amount_entry = ctk.CTkEntry(main, height=40, corner_radius=8,
                                          border_color=COLORS["border"],
                                          font=ctk.CTkFont(size=14), placeholder_text="0.00")
        self._amount_entry.grid(row=row, column=0, sticky="ew", pady=(4, 12))
        row += 1
        self._status = ctk.CTkLabel(main, text="", font=ctk.CTkFont(size=12))
        self._status.grid(row=row, column=0, pady=4)
        row += 1
        main.grid_rowconfigure(row, weight=1)
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=row, column=0, sticky="s", pady=(8, 0))
        ctk.CTkButton(btn_frame, text="  Add Funds  ", width=100, height=42, corner_radius=10,
                       fg_color="#22c55e", text_color="#ffffff", hover_color="#16a34a",
                       font=ctk.CTkFont(size=15, weight="bold"),
                       command=self._save).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="  Cancel  ", width=100, height=42, corner_radius=10,
                       fg_color="#334155", text_color="#f1f5f9", hover_color="#475569",
                       font=ctk.CTkFont(size=15), command=self.destroy).pack(side="left", padx=8)

    def _save(self):
        try:
            amt = float(self._amount_entry.get().strip())
            if amt <= 0: raise ValueError
        except ValueError:
            self._status.configure(text="\u26A0 Enter a valid amount", text_color="#ef4444")
            return
        try:
            self.api.fund_goal(self.goal_id, amt)
            self.on_done()
            self.destroy()
        except Exception as e:
            self._status.configure(text=f"\u26A0 {e}", text_color="#ef4444")
