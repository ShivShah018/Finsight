import customtkinter as ctk
from api_client.client import FinSightClient, ApiError
from utils.config_manager import save_credentials, load_credentials, clear_credentials, load_env

load_env()

COLORS = {
    "bg":            "#0b0e1a",
    "card_bg":       "#13172b",
    "accent":        "#6366f1",
    "accent_hover":  "#4f46e5",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "border":        "#1e2140",
    "success":       "#22c55e",
    "error":         "#ef4444",
}


class AuthView(ctk.CTkFrame):
    """Full-window login/register overlay that communicates with the API."""

    def __init__(self, master, on_auth_success, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=COLORS["bg"])
        self.on_auth_success = on_auth_success
        self._api = FinSightClient()
        self._build_ui()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        outer = ctk.CTkFrame(self, fg_color="transparent")
        outer.grid(row=0, column=0)

        card = ctk.CTkFrame(outer, width=420, corner_radius=18,
                            fg_color=COLORS["card_bg"], border_width=1, border_color=COLORS["border"])
        card.pack(padx=40, pady=40)
        card.pack_propagate(False)
        card.configure(height=580)

        ctk.CTkLabel(card, text="\U0001F4C8", font=ctk.CTkFont(size=40)).pack(pady=(32, 4))
        ctk.CTkLabel(card, text="FinSight", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=COLORS["text_primary"]).pack()
        ctk.CTkLabel(card, text="Budget Planner with Savings Goals",
                     font=ctk.CTkFont(size=12), text_color=COLORS["text_muted"]).pack(pady=(0, 18))

        self._tab_var = ctk.StringVar(value="Login")
        tab = ctk.CTkSegmentedButton(card, values=["Login", "Register"],
                                      variable=self._tab_var,
                                      selected_color=COLORS["accent"],
                                      selected_hover_color=COLORS["accent_hover"],
                                      unselected_color="#1e2140",
                                      unselected_hover_color="#2a2f50",
                                      font=ctk.CTkFont(size=13, weight="bold"),
                                      command=self._on_tab_switch)
        tab.pack(padx=30, fill="x", pady=(0, 12))

        self._form_frame = ctk.CTkFrame(card, fg_color="transparent")
        self._form_frame.pack(padx=30, fill="x", pady=(0, 6))
        self._build_login_form()

        self._remember_var = ctk.BooleanVar(value=True)
        self._remember_cb = ctk.CTkCheckBox(card, text="Remember Me",
                                             variable=self._remember_var,
                                             font=ctk.CTkFont(size=12),
                                             text_color=COLORS["text_secondary"],
                                             fg_color=COLORS["accent"],
                                             hover_color=COLORS["accent_hover"],
                                             checkmark_color="white")
        self._remember_cb.pack(padx=30, anchor="w", pady=(4, 0))

        self._status_label = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12),
                                           text_color=COLORS["text_secondary"])
        self._status_label.pack(pady=(2, 0))

        self._action_btn = ctk.CTkButton(card, text="Login", height=52, corner_radius=12,
                                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                          font=ctk.CTkFont(size=16, weight="bold"),
                                          command=self._on_submit)
        self._action_btn.pack(padx=30, fill="x", pady=(10, 28))

        saved = load_credentials()
        if saved:
            self._email_entry.insert(0, saved["email"])
            self._password_entry.focus()

    def _clear_form(self):
        for w in self._form_frame.winfo_children():
            w.destroy()

    def _build_login_form(self):
        self._clear_form()
        ctk.CTkLabel(self._form_frame, text="Email", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 2))
        self._email_entry = ctk.CTkEntry(self._form_frame, height=40, corner_radius=8,
                                          placeholder_text="you@example.com",
                                          border_color=COLORS["border"])
        self._email_entry.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self._form_frame, text="Password", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 2))
        self._password_entry = ctk.CTkEntry(self._form_frame, height=40, corner_radius=8,
                                             placeholder_text="\u2022\u2022\u2022\u2022\u2022\u2022\u2022\u2022",
                                             show="\u2022", border_color=COLORS["border"])
        self._password_entry.pack(fill="x", pady=(0, 2))
        self._email_entry.bind("<Return>", lambda e: self._on_submit())
        self._password_entry.bind("<Return>", lambda e: self._on_submit())

    def _build_register_form(self):
        self._clear_form()
        ctk.CTkLabel(self._form_frame, text="Full Name", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 2))
        self._name_entry = ctk.CTkEntry(self._form_frame, height=40, corner_radius=8,
                                         placeholder_text="John Doe", border_color=COLORS["border"])
        self._name_entry.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self._form_frame, text="Email", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 2))
        self._email_entry = ctk.CTkEntry(self._form_frame, height=40, corner_radius=8,
                                          placeholder_text="you@example.com",
                                          border_color=COLORS["border"])
        self._email_entry.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(self._form_frame, text="Password", font=ctk.CTkFont(size=12),
                     text_color=COLORS["text_secondary"], anchor="w").pack(fill="x", pady=(0, 2))
        self._password_entry = ctk.CTkEntry(self._form_frame, height=40, corner_radius=8,
                                             placeholder_text="At least 6 characters",
                                             show="\u2022", border_color=COLORS["border"])
        self._password_entry.pack(fill="x", pady=(0, 2))
        self._name_entry.bind("<Return>", lambda e: self._on_submit())
        self._email_entry.bind("<Return>", lambda e: self._on_submit())
        self._password_entry.bind("<Return>", lambda e: self._on_submit())

    def _on_tab_switch(self, value: str):
        if value == "Register":
            self._build_register_form()
            self._action_btn.configure(text="Register")
        else:
            self._build_login_form()
            self._action_btn.configure(text="Login")
        self._status_label.configure(text="")

    def _on_submit(self):
        self._status_label.configure(text="")
        is_register = self._tab_var.get() == "Register"
        email = self._email_entry.get().strip()
        password = self._password_entry.get()

        if not email or not password:
            self._show_error("Email and password are required.")
            return

        try:
            if is_register:
                full_name = self._name_entry.get().strip()
                if not full_name:
                    self._show_error("Full name is required.")
                    return
                if len(password) < 6:
                    self._show_error("Password must be at least 6 characters.")
                    return
                result = self._api.register(full_name, email, password)
                if self._remember_var.get():
                    save_credentials(email, result["access_token"])
                self._show_success(f"Welcome, {result['name']}!")
                self.after(500, lambda: self.on_auth_success(result))
            else:
                result = self._api.login(email, password)
                if self._remember_var.get():
                    save_credentials(email, result["access_token"])
                else:
                    clear_credentials()
                self._show_success(f"Welcome back, {result['name']}!")
                self.after(500, lambda: self.on_auth_success(result))
        except ApiError as e:
            self._show_error(e.detail)
        except Exception as e:
            self._show_error(f"Connection failed: {e}")

    def _show_error(self, msg: str):
        self._status_label.configure(text=f"\u26A0  {msg}", text_color=COLORS["error"])

    def _show_success(self, msg: str):
        self._status_label.configure(text=f"\u2713  {msg}", text_color=COLORS["success"])
