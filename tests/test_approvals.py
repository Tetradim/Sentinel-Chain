from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.repository import SQLiteRepository


def test_approval_required_mode_queues_signal_until_operator_approves(tmp_path):
    repo = SQLiteRepository(tmp_path / "approvals.sqlite3")
    app = create_app(repository=repo, require_approval=True)
    client = TestClient(app)

    response = client.post(
        "/webhooks/tradingview",
        json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "quote_amount": "40",
            "price": "50000",
            "stop_loss_pct": "2",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approval_required"
    assert client.get("/orders").json()["orders"] == []
    assert client.get("/approvals").json()["pending"][0]["signal_id"] == body["signal_id"]

    approved = client.post(f"/approvals/{body['signal_id']}/approve")

    assert approved.status_code == 200
    assert approved.json()["status"] == "accepted"
    assert client.get("/orders").json()["orders"][0]["symbol"] == "BTC/USDT"
    audit_types = [event["event_type"] for event in client.get("/audit").json()["events"]]
    assert audit_types == ["signal.received", "approval.requested", "order.accepted"]


def test_operator_can_reject_pending_signal(tmp_path):
    repo = SQLiteRepository(tmp_path / "reject.sqlite3")
    app = create_app(repository=repo, require_approval=True)
    client = TestClient(app)
    response = client.post(
        "/webhooks/tradingview",
        json={
            "symbol": "ETHUSDT",
            "side": "buy",
            "quote_amount": "40",
            "price": "3000",
            "stop_loss_pct": "2",
        },
    )
    signal_id = response.json()["signal_id"]

    rejected = client.post(f"/approvals/{signal_id}/reject", json={"reason": "bad setup"})

    assert rejected.status_code == 200
    assert rejected.json() == {"status": "rejected", "signal_id": signal_id}
    assert client.get("/orders").json()["orders"] == []
    assert client.get("/approvals").json()["pending"] == []
    audit_types = [event["event_type"] for event in client.get("/audit").json()["events"]]
    assert audit_types == ["signal.received", "approval.requested", "approval.rejected"]

