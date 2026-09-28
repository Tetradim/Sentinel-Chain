from fastapi.testclient import TestClient

from sentinel_chain.app import create_app
from sentinel_chain.charting.automap import analyze_market_structure, backtest_auto_strategy, generate_demo_candles


def test_demo_analyzer_returns_overlay_and_plan():
    candles = generate_demo_candles("BTCUSDT", "15m", 260, seed=42)
    result = analyze_market_structure(candles, symbol="BTCUSDT", timeframe="15m")
    assert result["ok"] is True
    assert result["bar_count"] == 260
    assert result["overlays"]["support_resistance"]
    assert "trade_plans" in result["signals"]
    assert result["signals"]["trade_plans"]["long"]["stop_loss"] < result["signals"]["trade_plans"]["long"]["entry"]
    assert result["signals"]["trade_plans"]["short"]["stop_loss"] > result["signals"]["trade_plans"]["short"]["entry"]


def test_backtest_returns_metrics():
    candles = generate_demo_candles("ETHUSDT", "1h", 220, seed=7)
    result = backtest_auto_strategy(candles, symbol="ETHUSDT", timeframe="1h")
    assert result["ok"] is True
    assert "metrics" in result
    assert result["metrics"]["starting_equity"] == 10000.0
    assert isinstance(result["equity_curve"], list)


def test_too_few_candles_is_safe_error():
    candles = generate_demo_candles("SOLUSDT", "15m", 10, seed=1)[:10]
    result = analyze_market_structure(candles)
    assert result["ok"] is False
    assert "At least 30" in result["error"]


def test_war_room_ticket_signal_can_preview_through_standard_signal_api():
    client = TestClient(create_app())
    candles = generate_demo_candles("BTCUSDT", "15m", 120, seed=11)

    ticket = client.post(
        "/war-room/ticket",
        json={
            "symbol": "BTCUSDT",
            "timeframe": "15m",
            "venue": "paper",
            "market_type": "swap",
            "side": "long",
            "account_equity": 10000,
            "risk_pct": 1,
            "leverage": 2,
            "candles": candles,
        },
    )

    assert ticket.status_code == 200
    signal = ticket.json()["signal"]
    assert "stop_loss_price" in signal
    assert "bracket" not in signal

    preview = client.post("/signals/preview", json=signal)

    assert preview.status_code == 200
    assert preview.json()["signal"]["strategy_id"].startswith("war_room_")
