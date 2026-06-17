from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.repository import SQLiteRepository


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
