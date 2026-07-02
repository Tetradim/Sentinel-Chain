from __future__ import annotations

from sentinel_chain.exchanges.futures_native import build_native_futures_plan
from sentinel_chain.signals import normalize_signal


def make_signal(**overrides):
    payload = {
        "signal_id": "plan-001",
        "symbol": "BTCUSDT",
        "side": "buy",
        "exchange": "bitunix",
        "market_type": "swap",
        "quote_amount": "100",
        "price": "65000",
        "stop_loss_price": "63500",
        "take_profit_price": "68000",
        "leverage": "3",
    }
    payload.update(overrides)
    return normalize_signal(payload, source="test")


def test_bitunix_simple_bracket_uses_attached_entry_tpsl():
    plan = build_native_futures_plan(make_signal(), venue="bitunix")
    data = plan.to_dict()

    assert data["strategy"] == "bitunix_attached_tpsl_on_entry"
    entry = next(leg for leg in data["legs"] if leg["id"] == "entry")
    assert entry["endpoint"] == "/api/v1/futures/trade/place_order"
    assert entry["body"]["tpPrice"] == "68000"
    assert entry["body"]["slPrice"] == "63500"


def test_bitunix_complex_bracket_waits_for_position_id_and_marks_trailing_synthetic():
    signal = make_signal(
        take_profit_price="",
        take_profit_targets=[
            {"trigger_price": "68000", "close_pct": "50"},
            {"trigger_price": "70000", "close_pct": "50"},
        ],
        trailing_stop_pct="1.5",
        trailing_activation_price="66500",
    )

    plan = build_native_futures_plan(signal, venue="bitunix")
    ids = {leg.id for leg in plan.legs}

    assert plan.strategy == "bitunix_entry_then_position_or_batch_tpsl"
    assert "await-position-id" in ids
    assert "synthetic-trailing-stop" in ids
    assert plan.unsupported_features


def test_ccxt_attached_capability_adds_attached_params():
    signal = make_signal(exchange="bybit")
    plan = build_native_futures_plan(
        signal,
        venue="bybit",
        ccxt_capabilities={"attachedStopLossTakeProfit": True, "reduceOnly": True},
    )
    entry = next(leg for leg in plan.legs if leg.id == "entry")

    assert plan.strategy == "ccxt_attached_tpsl"
    assert "stopLoss" in entry.params["params"]
    assert "takeProfit" in entry.params["params"]
