from utils.currency import convert_amount, format_amount

def test_convert_amount_same_currency():
    assert convert_amount(100, "INR", "INR") == 100.0

def test_convert_amount_inr_to_usd():
    result = convert_amount(100, "INR", "USD")
    assert round(result, 2) == 1.20

def test_convert_amount_inr_to_npr():
    result = convert_amount(100, "INR", "NPR")
    assert result == 160.0

def test_convert_amount_zero():
    assert convert_amount(0, "INR", "USD") == 0.0

def test_format_amount():
    r = format_amount(1234.5, "INR")
    assert "₹" in r
    assert "1,234.50" in r

def test_format_amount_usd():
    r = format_amount(1234.5, "USD")
    assert "$" in r
    assert "14.81" in r  # 1234.5 * 0.012 = 14.814
