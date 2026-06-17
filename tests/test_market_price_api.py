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
        {"symbol": "SOL/USDT", "kind": "take_profit", "price": "106.00000000"}
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
