"""
FinSight — Budget Planner with Savings Goals
A premium personal-finance desktop application.
"""

import sys
import os
import io

# Force UTF-8 for console output (fixes ₹, रू symbols etc.)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import customtkinter as ctk

from views.dashboard_view import DashboardView
from views.add_transaction_view import AddTransactionView
from views.goals_view import GoalsView
from views.budget_view import BudgetView
from views.auth_view import AuthView
from utils.db_manager import DatabaseManager, User
from utils.config_manager import load_credentials
from utils.recurring import process_recurring_transactions

# ── Theme ─────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(
    os.path.join(PROJECT_ROOT, "assets", "finsight_theme.json")
    if os.path.isfile(os.path.join(PROJECT_ROOT, "assets", "finsight_theme.json"))
    else "blue"
)

COLORS = {
    "sidebar_bg":       "#0f1222",
    "content_bg":       "#0b0e1a",
    "card_bg":          "#13172b",
    "accent":           "#6366f1",
    "accent_hover":     "#4f46e5",
    "text_primary":     "#f1f5f9",
    "text_secondary":   "#94a3b8",
    "text_muted":       "#475569",
    "border":           "#1e2140",
    "income":           "#22c55e",
    "expense":          "#ef4444",
    "warning":          "#eab308",
}


class FinSightApp(ctk.CTk):
    """Main application window."""

    NAV_ITEMS = [
        ("Dashboard",        "\u2302",       DashboardView),
        ("Add Transaction",  "\u2795",       AddTransactionView),
        ("Goals",            "\U0001F3AF",   GoalsView),
        ("Budget",           "\U0001F4CA",   BudgetView),
    ]

    def __init__(self):
        super().__init__()

        self.title("FinSight \u2014 Budget Planner with Savings Goals")
        self.geometry("1200x740")
        self.minsize(960, 600)

        self._current_user: User | None = None
        self._nav_buttons: list[ctk.CTkButton] = []
        self._current_view: ctk.CTkFrame | None = None

        self.bind("<Control-d>", lambda e: self._safe_switch(0))
        self.bind("<Control-n>", lambda e: self._safe_switch(1))
        self.bind("<Control-g>", lambda e: self._safe_switch(2))
        self.bind("<Control-b>", lambda e: self._safe_switch(3))

        # Try auto-login first
        if not self._try_auto_login():
            self._show_auth()

    # ── Auto Login ───────────────────────────────────────────
    def _try_auto_login(self) -> bool:
        creds = load_credentials()
        if not creds:
            return False
        try:
            db = DatabaseManager.get_instance()
            db.connect()
            user = db.authenticate_user(creds["email"], creds["password"])
            if user:
                self._current_user = user
                count = process_recurring_transactions(user.id)
                self._build_ui()
                self._user_label.configure(text=f"\U0001F464  {user.full_name}")
                if count:
                    self.after(500, lambda: self._show_recurring_notice(count))
                return True
        except Exception:
            pass
        return False

    # ── Auth ──────────────────────────────────────────────────
    def _show_auth(self):
        self._auth_view = AuthView(self, on_auth_success=self._on_auth_success)
        self._auth_view.grid(row=0, column=0, sticky="nswe")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _on_auth_success(self, user: User):
        self._current_user = user
        self._auth_view.destroy()
        count = process_recurring_transactions(user.id)
        self._build_ui()
        self._user_label.configure(text=f"\U0001F464  {user.full_name}")
        if count:
            self.after(500, lambda: self._show_recurring_notice(count))

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._switch_view(0)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(
            self, width=220, corner_radius=0, fg_color=COLORS["sidebar_bg"],
        )
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)

        # Logo
        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=18, pady=(28, 6))

        ctk.CTkLabel(
            logo_frame, text="\U0001F4C8",
            font=ctk.CTkFont(size=32),
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame, text="FinSight",
            font=ctk.CTkFont(size=22, weight="bold"),
            anchor="w", text_color=COLORS["text_primary"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            logo_frame, text="Budget Planner",
            font=ctk.CTkFont(size=11),
            anchor="w", text_color=COLORS["text_muted"],
        ).pack(anchor="w")

        # User greeting
        self._user_label = ctk.CTkLabel(
            sidebar,
            text="",
            font=ctk.CTkFont(size=12),
            anchor="w",
            text_color=COLORS["text_secondary"],
        )
        self._user_label.pack(fill="x", padx=18, pady=(4, 12))

        # Separator
        ctk.CTkFrame(sidebar, height=1, fg_color=COLORS["border"]).pack(
            fill="x", padx=18, pady=(0, 14)
        )

        # Nav buttons
        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.pack(fill="x", padx=12, pady=0)

        for idx, (label, icon, _) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(
                nav_container,
                text=f"  {icon}  {label}",
                anchor="w", height=46, corner_radius=10,
                font=ctk.CTkFont(size=14, weight="normal"),
                fg_color="transparent",
                text_color=COLORS["text_secondary"],
                hover_color="#1a1f3a",
                command=lambda i=idx: self._switch_view(i),
            )
            btn.pack(fill="x", pady=3)
            self._nav_buttons.append(btn)

        # Spacer + logout
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        logout_btn = ctk.CTkButton(
            sidebar,
            text="  \U0001F6AA  Logout",
            anchor="w", height=40, corner_radius=10,
            font=ctk.CTkFont(size=12),
            fg_color="transparent",
            text_color=COLORS["text_muted"],
            hover_color="#1a1f3a",
            command=self._logout,
        )
        logout_btn.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(
            sidebar, text="v1.0.0",
            font=ctk.CTkFont(size=10),
            text_color=COLORS["text_muted"],
        ).pack(side="bottom", pady=10)

    def _build_content_area(self):
        content = ctk.CTkFrame(
            self, corner_radius=0, fg_color=COLORS["content_bg"],
        )
        content.grid(row=0, column=1, sticky="nswe")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self._content_frame = content

    def _switch_view(self, index: int):
        if self._current_view is not None:
            self._current_view.destroy()

        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(
                    fg_color=COLORS["accent"],
                    text_color=COLORS["text_primary"],
                    font=ctk.CTkFont(size=14, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_secondary"],
                    font=ctk.CTkFont(size=14, weight="normal"),
                )

        _label, _icon, view_class = self.NAV_ITEMS[index]
        self._current_view = view_class(
            self._content_frame,
            user=self._current_user,
        )
        self._current_view.grid(row=0, column=0, sticky="nswe")
        self._current_view.grid_columnconfigure(0, weight=1)

    def _safe_switch(self, index):
        if self._current_user and self._content_frame:
            self._switch_view(index)

    def _logout(self):
        self._current_user = None
        if self._current_view is not None:
            self._current_view.destroy()
        self._content_frame.destroy()
        # Remove sidebar + content grid
        for w in self.grid_slaves():
            w.destroy()
        self._nav_buttons.clear()
        self._show_auth()


# ── Entry Point ─────────────────────────────────────────────
    def _show_recurring_notice(self, count):
        from tkinter import messagebox
        messagebox.showinfo("Recurring Transactions",
                            f"{count} recurring transaction(s) auto-added for today.",
                            parent=self)

if __name__ == "__main__":
    app = FinSightApp()
    app.mainloop()
