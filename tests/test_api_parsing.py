from decimal import Decimal

import pytest

from sentinel_chain.api.parsing import candle_payload, positive_decimal


def test_positive_decimal_accepts_positive_numeric_strings():
    assert positive_decimal("1.25") == Decimal("1.25")


def test_positive_decimal_rejects_zero_and_negative_values():
    with pytest.raises(ValueError):
        positive_decimal("0")
    with pytest.raises(ValueError):
        positive_decimal("-1")


def test_candle_payload_normalizes_price_range_payloads():
    candle = candle_payload(
        {"time": "T1", "high": "12", "low": "9", "close": "11"}
    )
    assert candle == {
        "label": "T1",
        "high": Decimal("12"),
        "low": Decimal("9"),
        "close": Decimal("11"),
    }


def test_candle_payload_rejects_low_above_high():
    with pytest.raises(ValueError, match="low cannot exceed high"):
        candle_payload({"high": "9", "low": "12", "close": "11"})
