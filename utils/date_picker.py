"""
Calendar date-picker popup with decade / year / month quick-jump.
"""

import customtkinter as ctk
from datetime import datetime, date
import calendar

COLORS = {
    "card_bg":       "#13172b",
    "border":        "#1e2140",
    "accent":        "#6366f1",
    "text_primary":  "#f1f5f9",
    "text_secondary":"#94a3b8",
    "text_muted":    "#475569",
}

MONTH_NAMES = [calendar.month_name[i] for i in range(1, 13)]


class DatePickerPopup(ctk.CTkToplevel):
    """A popup calendar to pick a date. Calls on_select(date) when chosen."""

    def __init__(self, master, on_select, initial_date: date = None):
        super().__init__(master)
        self.on_select = on_select
        self._current = initial_date or date.today()
        self._selected = initial_date or date.today()

        self.title("Select Date")
        self.geometry("400x420")
        self.resizable(False, False)
        self.configure(fg_color=COLORS["card_bg"])

        if master:
            x = master.winfo_rootx() + 60
            y = master.winfo_rooty() + 60
            self.geometry(f"400x420+{x}+{y}")

        self._build_ui()
        self._render_calendar()
        self.grab_set()
        self.focus()

    def _build_ui(self):
        # ── Row 1: Decade & year quick-jump ──
        jump = ctk.CTkFrame(self, fg_color="transparent")
        jump.pack(fill="x", padx=14, pady=(14, 2))

        ctk.CTkButton(jump, text="\u25C0\u25C0", width=36, height=30,
                       fg_color="transparent", text_color=COLORS["text_muted"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=10),
                       command=self._prev_decade).pack(side="left")
        ctk.CTkButton(jump, text="\u25C0", width=32, height=30,
                       fg_color="transparent", text_color=COLORS["text_secondary"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=12),
                       command=self._prev_year).pack(side="left", padx=(2, 6))

        # Year combo (editable dropdown)
        years = [str(y) for y in range(1950, 2051)]
        self._year_var = ctk.StringVar(value=str(self._current.year))
        self._year_combo = ctk.CTkComboBox(
            jump, variable=self._year_var, values=years,
            width=90, height=30,
            fg_color="#1a1f3a", border_color=COLORS["border"],
            button_color=COLORS["accent"], button_hover_color="#4f46e5",
            dropdown_fg_color="#1a1f3a", dropdown_hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=13), dropdown_font=ctk.CTkFont(size=12),
            command=self._on_year_month_change,
        )
        self._year_combo.pack(side="left", padx=(0, 4))

        # Month dropdown
        self._month_var = ctk.StringVar(value=MONTH_NAMES[self._current.month - 1])
        self._month_menu = ctk.CTkOptionMenu(
            jump, variable=self._month_var, values=MONTH_NAMES,
            width=100, height=30,
            fg_color="#1a1f3a", button_color=COLORS["accent"],
            button_hover_color="#4f46e5",
            dropdown_fg_color="#1a1f3a", dropdown_hover_color=COLORS["accent"],
            font=ctk.CTkFont(size=13), dropdown_font=ctk.CTkFont(size=12),
            command=self._on_year_month_change,
        )
        self._month_menu.pack(side="left", padx=(4, 6))

        ctk.CTkButton(jump, text="\u25B6", width=32, height=30,
                       fg_color="transparent", text_color=COLORS["text_secondary"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=12),
                       command=self._next_year).pack(side="left")
        ctk.CTkButton(jump, text="\u25B6\u25B6", width=36, height=30,
                       fg_color="transparent", text_color=COLORS["text_muted"],
                       hover_color="#1a1f3a", font=ctk.CTkFont(size=10),
                       command=self._next_decade).pack(side="left", padx=(2, 0))

        # ── Row 2: Month navigation (prev / next month) ──
        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.pack(fill="x", padx=14, pady=(2, 4))

        self._prev_month_btn = ctk.CTkButton(
            nav, text="\u25C0  Prev", height=28,
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color="#1a1f3a", font=ctk.CTkFont(size=11),
            command=self._prev_month,
        )
        self._prev_month_btn.pack(side="left")

        self._month_label = ctk.CTkLabel(
            nav, text="", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        self._month_label.pack(side="left", expand=True)

        self._next_month_btn = ctk.CTkButton(
            nav, text="Next  \u25B6", height=28,
            fg_color="transparent", text_color=COLORS["text_secondary"],
            hover_color="#1a1f3a", font=ctk.CTkFont(size=11),
            command=self._next_month,
        )
        self._next_month_btn.pack(side="right")

        # ── Row 3: Day-of-week header ──
        day_header = ctk.CTkFrame(self, fg_color="transparent")
        day_header.pack(fill="x", padx=14)
        for day_name in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
            ctk.CTkLabel(day_header, text=day_name, width=44,
                         font=ctk.CTkFont(size=11),
                         text_color=COLORS["text_muted"]).pack(side="left")

        # ── Calendar grid ──
        self._grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._grid_frame.pack(fill="both", expand=True, padx=14, pady=(2, 10))

        # ── Row: Quick date input ──
        input_row = ctk.CTkFrame(self, fg_color="transparent")
        input_row.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(input_row, text="Or type:",
                     font=ctk.CTkFont(size=11),
                     text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 6))
        self._quick_entry = ctk.CTkEntry(
            input_row, height=32, corner_radius=6,
            placeholder_text="YYYY-MM-DD", border_color=COLORS["border"],
            font=ctk.CTkFont(size=13),
        )
        self._quick_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._quick_entry.bind("<Return>", lambda e: self._quick_go())
        ctk.CTkButton(input_row, text="Go", width=50, height=32,
                       corner_radius=6, fg_color=COLORS["accent"],
                       font=ctk.CTkFont(size=12, weight="bold"),
                       command=self._quick_go).pack(side="left")

    # ── Calendar render ───────────────────────────────────────
    def _render_calendar(self):
        for w in self._grid_frame.winfo_children():
            w.destroy()

        self._month_label.configure(
            text=f"{calendar.month_name[self._current.month]} {self._current.year}"
        )
        # Sync dropdowns
        self._year_var.set(str(self._current.year))
        self._month_var.set(MONTH_NAMES[self._current.month - 1])

        cal = calendar.monthcalendar(self._current.year, self._current.month)
        today = date.today()

        for week in cal:
            row_f = ctk.CTkFrame(self._grid_frame, fg_color="transparent")
            row_f.pack(fill="x")
            for day_num in week:
                if day_num == 0:
                    ctk.CTkLabel(row_f, text="", width=44).pack(side="left")
                    continue

                cell_date = date(self._current.year, self._current.month, day_num)
                is_today = cell_date == today
                is_selected = cell_date == self._selected

                fg = COLORS["accent"] if is_selected else "transparent"
                txt_color = COLORS["text_primary"] if not is_today else COLORS["accent"]

                btn = ctk.CTkButton(
                    row_f, text=str(day_num), width=44, height=34,
                    fg_color=fg, text_color=txt_color,
                    hover_color="#1a1f3a",
                    font=ctk.CTkFont(size=13, weight="bold" if is_today or is_selected else "normal"),
                    corner_radius=8,
                    command=lambda d=cell_date: self._pick_date(d),
                )
                btn.pack(side="left", padx=1, pady=1)

    # ── Navigation ────────────────────────────────────────────
    def _prev_month(self):
        self._shift_month(-1)

    def _next_month(self):
        self._shift_month(1)

    def _shift_month(self, delta: int):
        m = self._current.month + delta
        y = self._current.year
        if m == 0:
            m = 12; y -= 1
        elif m == 13:
            m = 1; y += 1
        self._current = date(y, m, 1)
        self._render_calendar()

    def _prev_year(self):
        try:
            y = int(self._year_var.get())
            self._current = date(y - 1, self._current.month, 1)
        except ValueError:
            pass
        self._render_calendar()

    def _next_year(self):
        try:
            y = int(self._year_var.get())
            self._current = date(y + 1, self._current.month, 1)
        except ValueError:
            pass
        self._render_calendar()

    def _prev_decade(self):
        try:
            y = int(self._year_var.get())
            self._current = date(y - 10, self._current.month, 1)
        except ValueError:
            pass
        self._render_calendar()

    def _next_decade(self):
        try:
            y = int(self._year_var.get())
            self._current = date(y + 10, self._current.month, 1)
        except ValueError:
            pass
        self._render_calendar()

    def _on_year_month_change(self, _=None):
        try:
            y = int(self._year_var.get())
            m = MONTH_NAMES.index(self._month_var.get()) + 1
            self._current = date(y, m, 1)
            self._render_calendar()
        except (ValueError, IndexError):
            pass

    # ── Quick input ───────────────────────────────────────────
    def _quick_go(self):
        raw = self._quick_entry.get().strip()
        try:
            d = datetime.strptime(raw, "%Y-%m-%d").date()
            self._current = date(d.year, d.month, 1)
            self._render_calendar()
            # Also select it
            self._pick_date(d)
        except ValueError:
            self._quick_entry.configure(border_color="#ef4444")
            self.after(1000, lambda: self._quick_entry.configure(border_color=COLORS["border"]))

    # ── Select ────────────────────────────────────────────────
    def _pick_date(self, d: date):
        self._selected = d
        self.on_select(d)
        self.destroy()
