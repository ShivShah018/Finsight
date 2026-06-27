import os
import customtkinter as ctk
from utils.date_picker import DatePickerPopup
from utils.currency import CURRENCY_NAMES, SYMBOLS
from datetime import datetime, date

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
    "accent":        "#6366f1",
    "accent_hover":  "#4f46e5",
    "income":        "#22c55e",
    "expense":       "#ef4444",
    "success":       "#22c55e",
    "error":         "#ef4444",
}


class AddTransactionView(ctk.CTkFrame):

    def __init__(self, master, api, user, user_data, **kwargs):
        super().__init__(master, **kwargs)
        self.api = api
        self.user = user
        self.user_data = user_data
        self.configure(fg_color="transparent")
        self._categories = []
        self._selected_date = date.today()
        self._build_ui()
        self._load_categories()

    def _build_ui(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(scroll, text="Add Transaction",
                     font=ctk.CTkFont(size=28, weight="bold"), anchor="w"
                     ).pack(anchor="w", padx=20, pady=(12, 2))
        ctk.CTkLabel(scroll, text="Record an income or expense entry",
                     font=ctk.CTkFont(size=13), text_color=COLORS["text_secondary"], anchor="w"
                     ).pack(anchor="w", padx=20, pady=(0, 18))

        card = ctk.CTkFrame(scroll, corner_radius=14, border_width=1,
                            border_color=COLORS["border"], fg_color=COLORS["card_bg"])
        card.pack(fill="x", padx=20, pady=(0, 30), ipadx=10, ipady=10)
        card.grid_columnconfigure(0, weight=0)
        card.grid_columnconfigure(1, weight=1)

        row = 0
        ctk.CTkLabel(card, text="Type", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(18, 0))
        self._type_var = ctk.StringVar(value="expense")
        type_sel = ctk.CTkSegmentedButton(card, values=["Expense", "Income"],
                                          variable=self._type_var, selected_color=COLORS["accent"],
                                          selected_hover_color=COLORS["accent_hover"],
                                          font=ctk.CTkFont(size=13, weight="bold"),
                                          command=self._on_type_change)
        type_sel.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(18, 0))
        row += 1

        ctk.CTkLabel(card, text="Category", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(14, 0))
        self._category_var = ctk.StringVar()
        self._category_menu = ctk.CTkOptionMenu(card, variable=self._category_var, values=["Loading..."],
                                                fg_color="#1a1f3a", button_color=COLORS["accent"],
                                                button_hover_color=COLORS["accent_hover"],
                                                dropdown_fg_color="#1a1f3a",
                                                dropdown_hover_color=COLORS["accent"],
                                                font=ctk.CTkFont(size=13), dropdown_font=ctk.CTkFont(size=12))
        self._category_menu.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(14, 0))
        row += 1

        ctk.CTkLabel(card, text="Currency", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(14, 0))
        self._currency_var = ctk.StringVar(value="INR")
        currency_menu = ctk.CTkOptionMenu(card, variable=self._currency_var, values=CURRENCY_NAMES,
                                          fg_color="#1a1f3a", button_color=COLORS["accent"],
                                          button_hover_color=COLORS["accent_hover"],
                                          dropdown_fg_color="#1a1f3a",
                                          dropdown_hover_color=COLORS["accent"],
                                          font=ctk.CTkFont(size=13), dropdown_font=ctk.CTkFont(size=12))
        currency_menu.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(14, 0))
        row += 1

        ctk.CTkLabel(card, text="Amount", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(14, 0))
        amount_frame = ctk.CTkFrame(card, fg_color="transparent")
        amount_frame.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(14, 0))
        amount_frame.grid_columnconfigure(0, weight=1)
        self._amount_entry = ctk.CTkEntry(amount_frame, height=40, corner_radius=8,
                                          placeholder_text="0.00", border_color=COLORS["border"],
                                          font=ctk.CTkFont(size=15))
        self._amount_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._amount_sym = ctk.CTkLabel(amount_frame, text=SYMBOLS.get("INR", "\u20B9"),
                                        font=ctk.CTkFont(size=20, weight="bold"),
                                        text_color=COLORS["text_primary"], width=40)
        self._amount_sym.grid(row=0, column=1)

        def _update_sym(*_):
            self._amount_sym.configure(text=SYMBOLS.get(self._currency_var.get(), ""))
        self._currency_var.trace_add("write", _update_sym)
        row += 1

        ctk.CTkLabel(card, text="Date", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(14, 0))
        date_frame = ctk.CTkFrame(card, fg_color="transparent")
        date_frame.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(14, 0))
        date_frame.grid_columnconfigure(0, weight=1)
        self._date_entry = ctk.CTkEntry(date_frame, height=40, corner_radius=8,
                                        placeholder_text="YYYY-MM-DD", border_color=COLORS["border"],
                                        font=ctk.CTkFont(size=15))
        self._date_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._date_entry.insert(0, self._selected_date.strftime("%Y-%m-%d"))
        self._date_entry.bind("<Return>", lambda e: self._parse_date_entry())
        ctk.CTkButton(date_frame, text="\U0001F4C5", width=40, height=34,
                       fg_color="transparent", text_color=COLORS["text_secondary"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=16),
                       command=self._open_calendar).grid(row=0, column=1)
        row += 1

        ctk.CTkLabel(card, text="Description", font=ctk.CTkFont(size=13),
                     text_color=COLORS["text_secondary"]).grid(row=row, column=0, sticky="w", padx=(16, 12), pady=(14, 0))
        self._desc_entry = ctk.CTkEntry(card, height=40, corner_radius=8,
                                        placeholder_text="Optional note", border_color=COLORS["border"],
                                        font=ctk.CTkFont(size=15))
        self._desc_entry.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(14, 0))
        row += 1

        self._recurring_var = ctk.BooleanVar(value=False)
        self._recurring_cb = ctk.CTkCheckBox(card, text="Repeat every month",
                                              variable=self._recurring_var,
                                              fg_color=COLORS["accent"],
                                              font=ctk.CTkFont(size=12),
                                              text_color=COLORS["text_secondary"])
        self._recurring_cb.grid(row=row, column=1, sticky="w", padx=(0, 16), pady=(6, 0))
        row += 1

        self._receipt_path = None
        receipt_row = ctk.CTkFrame(card, fg_color="transparent")
        receipt_row.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=(8, 0))
        self._receipt_label = ctk.CTkLabel(receipt_row, text="No receipt",
                                           font=ctk.CTkFont(size=11),
                                           text_color=COLORS["text_muted"])
        self._receipt_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(receipt_row, text="\U0001F4CE Attach", width=80, height=28, corner_radius=6,
                       fg_color="#1a1f3a", text_color=COLORS["text_secondary"],
                       font=ctk.CTkFont(size=11), command=self._pick_receipt).pack(side="right")
        row += 1

        self._status_label = ctk.CTkLabel(card, text="", font=ctk.CTkFont(size=12),
                                           text_color=COLORS["text_secondary"])
        self._status_label.grid(row=row, column=0, columnspan=2, pady=(10, 0))
        row += 1

        ctk.CTkButton(card, text="Save Transaction", height=50, corner_radius=12,
                       fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                       font=ctk.CTkFont(size=15, weight="bold"),
                       command=self._on_save).grid(row=row, column=0, columnspan=2, sticky="ew", padx=60, pady=(14, 20))

    def _open_calendar(self):
        DatePickerPopup(self.winfo_toplevel(), on_select=self._on_date_picked,
                        initial_date=self._selected_date)

    def _on_date_picked(self, d: date):
        self._selected_date = d
        self._date_entry.delete(0, "end")
        self._date_entry.insert(0, d.strftime("%Y-%m-%d"))

    def _parse_date_entry(self):
        raw = self._date_entry.get().strip()
        try:
            d = datetime.strptime(raw, "%Y-%m-%d").date()
            self._selected_date = d
            self._date_entry.configure(border_color=COLORS["border"])
        except ValueError:
            self._date_entry.configure(border_color="#ef4444")

    def _load_categories(self):
        try:
            self._categories = self.api.get_categories("expense")
            self._update_category_menu()
        except Exception:
            self._category_menu.configure(values=["Error loading"], state="disabled")

    def _on_type_change(self, value: str):
        try:
            self._categories = self.api.get_categories(value.lower())
            self._update_category_menu()
        except Exception:
            pass

    def _update_category_menu(self):
        if not self._categories:
            self._category_menu.configure(values=["No categories"], state="disabled")
            return
        names = [c["name"] for c in self._categories]
        self._category_menu.configure(values=names, state="normal")
        self._category_var.set(names[0])

    def _pick_receipt(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(parent=self.winfo_toplevel(),
                                          title="Select Receipt Image",
                                          filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
        if path:
            self._receipt_path = path
            name = os.path.basename(path)
            self._receipt_label.configure(text=f"\U0001F4CE {name}", text_color=COLORS["text_primary"])

    def _on_save(self):
        self._status_label.configure(text="")

        try:
            amount = float(self._amount_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            self._status_label.configure(text="\u26A0  Enter a valid amount greater than 0",
                                         text_color=COLORS["error"])
            return

        cat_name = self._category_var.get()
        matching = [c for c in self._categories if c["name"] == cat_name]
        if not matching:
            self._status_label.configure(text="\u26A0  Select a valid category", text_color=COLORS["error"])
            return

        tx_type = self._type_var.get().lower()
        description = self._desc_entry.get().strip() or None
        currency = self._currency_var.get()

        try:
            self._selected_date = datetime.strptime(self._date_entry.get().strip(), "%Y-%m-%d").date()
        except ValueError:
            self._status_label.configure(text="\u26A0  Use YYYY-MM-DD format", text_color=COLORS["error"])
            self._date_entry.configure(border_color="#ef4444")
            return

        try:
            result = self.api.create_transaction(
                category_id=matching[0]["id"], amount=amount, tx_type=tx_type,
                description=description, currency=currency,
                transaction_date=self._selected_date.isoformat(),
            )

            if self._recurring_var.get():
                from utils.db_manager import DatabaseManager
                db = DatabaseManager.get_instance()
                db.connect()
                next_due = self._selected_date.replace(
                    year=self._selected_date.year + 1 if (self._selected_date.month == 2 and self._selected_date.day > 28) else self._selected_date.year,
                    month=self._selected_date.month % 12 + 1 if self._selected_date.month < 12 else 1,
                    day=min(self._selected_date.day, 28))
                db.add_recurring(self.user.id, matching[0]["id"], amount, tx_type,
                                 description, currency, "monthly", next_due)

            self._status_label.configure(
                text=f"\u2713  {tx_type.title()} of {SYMBOLS.get(currency)}{amount:,.2f} recorded!",
                text_color=COLORS["success"])
            self._amount_entry.delete(0, "end")
            self._desc_entry.delete(0, "end")
            self._date_entry.delete(0, "end")
            self._date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self._selected_date = datetime.now().date()
            self._date_entry.configure(border_color=COLORS["border"])
            self._receipt_path = None
            self._receipt_label.configure(text="No receipt")
            self._recurring_var.set(False)
            self._amount_entry.focus()
        except Exception as e:
            self._status_label.configure(text=f"\u26A0  Failed: {e}", text_color=COLORS["error"])
