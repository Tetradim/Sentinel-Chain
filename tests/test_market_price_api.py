from decimal import Decimal

from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.repository import SQLiteRepository
from autocrypto.risk import RiskConfig


def test_market_price_endpoint_triggers_paper_exit_and_audit_event(tmp_path):
    repo = SQLiteRepository(tmp_path / "market.sqlite3")
    app = create_app(repository=repo)
    client = TestClient(app)
    client.post(
        "/webhooks/tradingview",
        json={
            "symbol": "SOLUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
    )

    response = client.post("/market/price", json={"symbol": "SOLUSDT", "price": "106"})

    assert response.status_code == 200
    assert response.json()["triggered"] == [
        {"symbol": "SOL/USDT", "kind": "take_profit", "price": "106.00000000", "quantity": "1.00000000"}
    ]
    audit_types = [event["event_type"] for event in client.get("/audit").json()["events"]]
    assert audit_types[-1] == "exit.triggered"


def test_market_price_exit_reduces_open_notional_for_future_risk(tmp_path):
    repo = SQLiteRepository(tmp_path / "market_risk.sqlite3")
    app = create_app(
        repository=repo,
        risk_config=RiskConfig(max_order_notional=Decimal("500"), max_open_notional=Decimal("150")),
    )
    client = TestClient(app)
    client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "market-risk-entry",
            "symbol": "SOLUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
    )
    client.post("/market/price", json={"symbol": "SOLUSDT", "price": "106"})

    next_order = client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "market-risk-next",
            "symbol": "ETHUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "3000",
            "stop_loss_pct": "2",
        },
    )

    assert next_order.json()["status"] == "accepted"


def test_market_price_stop_loss_updates_daily_pnl_and_loss_streak(tmp_path):
    repo = SQLiteRepository(tmp_path / "market_loss_streak.sqlite3")
    app = create_app(
        repository=repo,
        risk_config=RiskConfig(max_order_notional=Decimal("500"), max_consecutive_losses=1),
    )
    client = TestClient(app)
    entry = client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "loss-streak-entry",
            "symbol": "BTCUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "4",
        },
    )
    exit_response = client.post("/market/price", json={"symbol": "BTCUSDT", "price": "97"})
    next_signal = client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "loss-streak-next",
            "symbol": "ETHUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "4",
        },
    )

    assert entry.status_code == 200
    assert exit_response.status_code == 200
    exit_body = exit_response.json()
    assert exit_body["realized_pnl_delta"] == "-3"
    assert exit_body["daily_pnl"] == "-3"
    assert exit_body["consecutive_losses"] == 1
    assert next_signal.json()["status"] == "rejected"
    assert "consecutive_loss_limit_exceeded" in next_signal.json()["risk"]["reason_codes"]


def test_market_price_preview_reports_trigger_without_mutating_paper_state(tmp_path):
    repo = SQLiteRepository(tmp_path / "market_preview.sqlite3")
    app = create_app(repository=repo)
    client = TestClient(app)
    client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "preview-entry",
            "symbol": "BTCUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "3",
            "take_profit_pct": "5",
        },
    )

    preview = client.post("/market/price/preview", json={"symbol": "BTCUSDT", "price": "105"})
    state_after_preview = client.get("/ui/state").json()

    assert preview.status_code == 200
    assert preview.json()["would_trigger"] == [
        {"symbol": "BTC/USDT", "kind": "take_profit", "price": "105.00000000", "quantity": "1.00000000"}
    ]
    assert state_after_preview["positions"][0]["quantity"] == "1.00000000"
    assert len(state_after_preview["orders"]) == 1
    assert state_after_preview["active_exits"]
