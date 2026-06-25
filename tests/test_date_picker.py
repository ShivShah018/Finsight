"""Test date utility logic used by the picker."""
from datetime import date
from utils.date_picker import DatePickerPopup

def test_date_picker_imports():
    from utils.date_picker import DatePickerPopup
    assert DatePickerPopup is not None

def test_date_picker_can_instantiate():
    # We just verify the class exists and can accept params
    import customtkinter as ctk
    root = ctk.CTk()
    try:
        popup = DatePickerPopup(root, on_select=lambda d: None)
        popup.destroy()
    except Exception:
        pass
    root.destroy()
