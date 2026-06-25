"""
Currency conversion & formatting for FinSight.
All amounts stored in original currency with a currency column.
"""

RATES = {
    "INR": 1.0,
    "USD": 0.012,
    "NPR": 1.60,
}

# Unicode symbols (will render in GUI via Tkinter)
SYMBOLS = {
    "INR": "\u20B9",
    "USD": "$",
    "NPR": "\u0930\u0941",
}

PLAIN = {
    "INR": "Rs.",
    "USD": "$",
    "NPR": "Rs.",
}

CURRENCY_NAMES = ["INR", "USD", "NPR"]


def _to_float(val) -> float:
    """Convert Decimal or int/float to float."""
    return float(val)


def convert_to_inr(amount, from_currency: str) -> float:
    amount = _to_float(amount)
    if not from_currency or from_currency == "INR":
        return round(amount, 2)
    rate_to_inr = 1.0 / RATES.get(from_currency, 1.0)
    return round(amount * rate_to_inr, 2)


def convert(amount_inr, to_currency: str) -> float:
    amount_inr = _to_float(amount_inr)
    rate = RATES.get(to_currency, 1.0)
    return round(amount_inr * rate, 2)


def convert_amount(amount, from_currency: str, to_currency: str) -> float:
    inr = convert_to_inr(amount, from_currency)
    return convert(inr, to_currency)


def format_amount(amount_inr, currency: str, plain: bool = False) -> str:
    """Format an INR amount. Set plain=True for ASCII-safe output."""
    converted = convert(amount_inr, currency)
    sym = PLAIN.get(currency, currency) if plain else SYMBOLS.get(currency, currency)
    return f"{sym}{converted:,.2f}"


def format_amount_direct(amount, currency: str, plain: bool = False) -> str:
    """Format an amount directly in its own currency (no conversion)."""
    amount = _to_float(amount)
    sym = PLAIN.get(currency, currency) if plain else SYMBOLS.get(currency, currency)
    return f"{sym}{amount:,.2f}"


def get_conversion_note(from_cur: str, to_cur: str) -> str:
    one_converted = convert(1.0, to_cur)
    return f"1 {from_cur} \u2248 {one_converted:.4f} {to_cur}"
