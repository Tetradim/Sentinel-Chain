from decimal import Decimal

import pytest

from autocrypto.signals import SignalValidationError, normalize_signal


def test_normalizes_tradingview_crypto_signal_with_stable_id():
    payload = {
        "symbol": "btcusdt",
        "side": "long",
        "exchange": "coinbase",
        "quote_amount": "125.50",
        "price": "65000",
        "stop_loss_pct": "2.5",
        "take_profit_pct": "7.5",
        "trailing_stop_pct": "3",
        "breakeven_trigger_pct": "2",
        "max_slippage_bps": 50,
        "strategy_id": "tv-breakout",
    }

    signal = normalize_signal(payload, source="tradingview")
    same_signal = normalize_signal(dict(payload), source="tradingview")

    assert signal.symbol == "BTC/USDT"
    assert signal.side == "buy"
    assert signal.exchange == "coinbase"
    assert signal.quote_amount == Decimal("125.50")
    assert signal.price == Decimal("65000")
    assert signal.stop_loss_pct == Decimal("2.5")
    assert signal.take_profit_pct == Decimal("7.5")
    assert signal.trailing_stop_pct == Decimal("3")
    assert signal.breakeven_trigger_pct == Decimal("2")
    assert signal.max_slippage_bps == 50
    assert signal.strategy_id == "tv-breakout"
    assert signal.signal_id == same_signal.signal_id


def test_normalizes_staged_take_profit_targets():
    signal = normalize_signal(
        {
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_targets": [
                {"pct": "8", "close_pct": "60"},
                {"pct": "4", "close_pct": "40"},
            ],
        },
        source="test",
    )

    assert signal.take_profit_pct == Decimal("4")
    assert [(target.pct, target.close_pct) for target in signal.take_profit_targets] == [
        (Decimal("4"), Decimal("40")),
        (Decimal("8"), Decimal("60")),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {"symbol": "BTC/USDT", "side": "withdraw", "quote_amount": 10},
        {"symbol": "BTC/USDT", "side": "buy"},
        {"symbol": "", "side": "buy", "quote_amount": 10},
        {"symbol": "BTC/USDT", "side": "buy", "quote_amount": "-10"},
        {
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "take_profit_targets": [{"pct": "2", "close_pct": "60"}, {"pct": "4", "close_pct": "60"}],
        },
    ],
)
def test_rejects_unsafe_or_ambiguous_signals(payload):
    with pytest.raises(SignalValidationError):
        normalize_signal(payload, source="test")
