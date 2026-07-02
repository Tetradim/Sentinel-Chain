from __future__ import annotations

import os

import pytest

from sentinel_chain.exchanges.bitunix_futures_execution import (
    BitunixFuturesTradingClient,
    BitunixLiveExecutionDisabled,
)


def client() -> BitunixFuturesTradingClient:
    return BitunixFuturesTradingClient(api_key="test-key", secret_key="test-secret")


def test_place_order_dry_run_builds_attached_tpsl_body():
    result = client().place_order(
        symbol="BTC/USDT",
        side="buy",
        qty="0.01",
        price="65000",
        tp_price="68000",
        sl_price="63500",
        dry_run=True,
    )

    assert result.submitted is False
    assert result.endpoint == "/api/v1/futures/trade/place_order"
    assert result.body["symbol"] == "BTCUSDT"
    assert result.body["side"] == "BUY"
    assert result.body["tradeSide"] == "OPEN"
    assert result.body["orderType"] == "LIMIT"
    assert result.body["tpPrice"] == "68000"
    assert result.body["slPrice"] == "63500"


def test_reduce_only_close_long_maps_to_bitunix_position_side():
    body = client().build_place_order_body(
        symbol="ETHUSDT",
        side="sell",
        qty="0.2",
        reduce_only=True,
        position_side="long",
    )

    assert body["side"] == "BUY"
    assert body["tradeSide"] == "CLOSE"
    assert body["reduceOnly"] is True


def test_live_submission_requires_env_gate(monkeypatch):
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", raising=False)

    with pytest.raises(BitunixLiveExecutionDisabled):
        client().place_order(symbol="BTCUSDT", side="buy", qty="0.01", dry_run=False)


def test_batch_tpsl_validation_requires_position_and_qty():
    with pytest.raises(ValueError):
        client().place_tp_sl_order(symbol="BTCUSDT", position_id="", tp_price="68000", tp_qty="0.01")

    with pytest.raises(ValueError):
        client().place_tp_sl_order(symbol="BTCUSDT", position_id="123", tp_price="68000")


def test_leverage_change_is_dry_run_by_default():
    result = client().change_leverage(symbol="BTCUSDT", margin_coin="USDT", leverage="5")

    assert result.submitted is False
    assert result.body == {"marginCoin": "USDT", "symbol": "BTCUSDT", "leverage": "5"}
