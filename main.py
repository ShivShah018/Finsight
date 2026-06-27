import sys
import os
import io

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
from views.insights_view import InsightsView
from views.auth_view import AuthView
from api_client.client import FinSightClient, ApiError
from utils.config_manager import load_credentials, clear_credentials, load_env
from utils.recurring import process_recurring_transactions
from utils.db_manager import DatabaseManager, User

load_env()

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
    """Main application window with API client architecture."""

    NAV_ITEMS = [
        ("Dashboard",        "\u2302",       DashboardView),
        ("Add Transaction",  "\u2795",       AddTransactionView),
        ("Goals",            "\U0001F3AF",   GoalsView),
        ("Budget",           "\U0001F4CA",   BudgetView),
        ("AI Insights",      "\U0001F9E0",   InsightsView),
    ]

    def __init__(self):
        super().__init__()
        self.title("FinSight \u2014 Budget Planner with Savings Goals")
        self.geometry("1200x740")
        self.minsize(960, 600)

        self._api = FinSightClient()
        self._current_user = None
        self._current_user_data = None
        self._nav_buttons = []
        self._current_view = None

        self.bind("<Control-d>", lambda e: self._safe_switch(0))
        self.bind("<Control-n>", lambda e: self._safe_switch(1))
        self.bind("<Control-g>", lambda e: self._safe_switch(2))
        self.bind("<Control-b>", lambda e: self._safe_switch(3))
        self.bind("<Control-i>", lambda e: self._safe_switch(4))

        if not self._try_auto_login():
            self._show_auth()

    def _try_auto_login(self) -> bool:
        creds = load_credentials()
        if not creds:
            return False
        try:
            self._api.set_token(creds["token"])
            me = self._api.get_me()
            self._current_user_data = me
            self._current_user = User(id=me["user_id"], full_name=me["name"],
                                      email=me["email"], currency=me.get("currency", "INR"))
            # Process recurring via DB directly (keeping for backward compat)
            db = DatabaseManager.get_instance()
            db.connect()
            count = process_recurring_transactions(self._current_user.id)
            self._build_ui()
            self._user_label.configure(text=f"\U0001F464  {me['name']}")
            if count:
                self.after(500, lambda: self._show_recurring_notice(count))
            return True
        except (ApiError, Exception):
            clear_credentials()
        return False

    def _show_auth(self):
        self._auth_view = AuthView(self, on_auth_success=self._on_auth_success)
        self._auth_view.grid(row=0, column=0, sticky="nswe")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _on_auth_success(self, result: dict):
        self._api.set_token(result["access_token"])
        self._current_user_data = result
        self._current_user = User(id=result["user_id"], full_name=result["name"],
                                  email=result["email"], currency="INR")
        self._auth_view.destroy()
        db = DatabaseManager.get_instance()
        db.connect()
        count = process_recurring_transactions(self._current_user.id)
        self._build_ui()
        self._user_label.configure(text=f"\U0001F464  {result['name']}")
        if count:
            self.after(500, lambda: self._show_recurring_notice(count))

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self._build_content_area()
        self._switch_view(0)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=COLORS["sidebar_bg"])
        sidebar.grid(row=0, column=0, sticky="nswe")
        sidebar.grid_propagate(False)

        logo_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=18, pady=(28, 6))
        ctk.CTkLabel(logo_frame, text="\U0001F4C8", font=ctk.CTkFont(size=32)).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="FinSight", font=ctk.CTkFont(size=22, weight="bold"),
                     anchor="w", text_color=COLORS["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(logo_frame, text="Budget Planner", font=ctk.CTkFont(size=11),
                     anchor="w", text_color=COLORS["text_muted"]).pack(anchor="w")

        self._user_label = ctk.CTkLabel(sidebar, text="", font=ctk.CTkFont(size=12),
                                         anchor="w", text_color=COLORS["text_secondary"])
        self._user_label.pack(fill="x", padx=18, pady=(4, 12))

        ctk.CTkFrame(sidebar, height=1, fg_color=COLORS["border"]).pack(fill="x", padx=18, pady=(0, 14))

        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.pack(fill="x", padx=12, pady=0)

        for idx, (label, icon, _) in enumerate(self.NAV_ITEMS):
            btn = ctk.CTkButton(nav_container, text=f"  {icon}  {label}",
                                anchor="w", height=46, corner_radius=10,
                                font=ctk.CTkFont(size=14, weight="normal"),
                                fg_color="transparent", text_color=COLORS["text_secondary"],
                                hover_color="#1a1f3a", command=lambda i=idx: self._switch_view(i))
            btn.pack(fill="x", pady=3)
            self._nav_buttons.append(btn)

        ctk.CTkFrame(sidebar, fg_color="transparent").pack(fill="both", expand=True)

        logout_btn = ctk.CTkButton(sidebar, text="  \U0001F6AA  Logout",
                                    anchor="w", height=40, corner_radius=10,
                                    font=ctk.CTkFont(size=12), fg_color="transparent",
                                    text_color=COLORS["text_muted"], hover_color="#1a1f3a",
                                    command=self._logout)
        logout_btn.pack(fill="x", padx=12, pady=(0, 6))

        ctk.CTkLabel(sidebar, text="v2.0.0", font=ctk.CTkFont(size=10),
                     text_color=COLORS["text_muted"]).pack(side="bottom", pady=10)

    def _build_content_area(self):
        content = ctk.CTkFrame(self, corner_radius=0, fg_color=COLORS["content_bg"])
        content.grid(row=0, column=1, sticky="nswe")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)
        self._content_frame = content

    def _switch_view(self, index: int):
        if self._current_view is not None:
            self._current_view.destroy()

        for i, btn in enumerate(self._nav_buttons):
            if i == index:
                btn.configure(fg_color=COLORS["accent"], text_color=COLORS["text_primary"],
                              font=ctk.CTkFont(size=14, weight="bold"))
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_secondary"],
                              font=ctk.CTkFont(size=14, weight="normal"))

        _label, _icon, view_class = self.NAV_ITEMS[index]
        self._current_view = view_class(self._content_frame, api=self._api, user=self._current_user,
                                         user_data=self._current_user_data)
        self._current_view.grid(row=0, column=0, sticky="nswe")
        self._current_view.grid_columnconfigure(0, weight=1)

    def _safe_switch(self, index):
        if self._current_user and self._content_frame:
            self._switch_view(index)

    def _logout(self):
        self._api.clear_token()
        self._current_user = None
        self._current_user_data = None
        if self._current_view is not None:
            self._current_view.destroy()
        self._content_frame.destroy()
        for w in self.grid_slaves():
            w.destroy()
        self._nav_buttons.clear()
        self._show_auth()

    def _show_recurring_notice(self, count):
        from tkinter import messagebox
        messagebox.showinfo("Recurring Transactions",
                            f"{count} recurring transaction(s) auto-added for today.",
                            parent=self)


if __name__ == "__main__":
    app = FinSightApp()
    app.mainloop()
