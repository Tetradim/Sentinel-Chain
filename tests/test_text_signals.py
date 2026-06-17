from decimal import Decimal

import pytest

from autocrypto.signals import SignalValidationError
from autocrypto.text_signals import parse_text_signal


def test_parse_text_signal_accepts_common_crypto_alert_format():
    signal = parse_text_signal("BUY BTCUSDT $125 @ 50000 SL 2.5% TP 5%", source="discord")

    assert signal.symbol == "BTC/USDT"
    assert signal.side == "buy"
    assert signal.quote_amount == Decimal("125")
    assert signal.price == Decimal("50000")
    assert signal.stop_loss_pct == Decimal("2.5")
    assert signal.take_profit_pct == Decimal("5")


def test_parse_text_signal_supports_base_quantity_and_slash_symbol():
    signal = parse_text_signal("SELL ETH/USDT 0.25 @ 3000", source="discord")

    assert signal.symbol == "ETH/USDT"
    assert signal.side == "sell"
    assert signal.base_amount == Decimal("0.25")
    assert signal.price == Decimal("3000")


@pytest.mark.parametrize("message", ["BTC looks strong", "BUY BTCUSDT", "WITHDRAW BTCUSDT $100 @ 1"])
def test_parse_text_signal_rejects_ambiguous_messages(message):
    with pytest.raises(SignalValidationError):
        parse_text_signal(message, source="discord")

