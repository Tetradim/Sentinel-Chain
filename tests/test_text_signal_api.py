from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.repository import SQLiteRepository


def test_parse_text_endpoint_returns_normalized_signal_without_ordering():
    app = create_app()
    client = TestClient(app)

    response = client.post("/signals/parse-text", json={"message": "BUY SOLUSDT $50 @ 150 SL 3% TP 8%"})

    assert response.status_code == 200
    body = response.json()["signal"]
    assert body["symbol"] == "SOL/USDT"
    assert body["side"] == "buy"
    assert body["quote_amount"] == "50"
    assert client.get("/orders").json()["orders"] == []


def test_text_alert_webhook_executes_parsed_message(tmp_path):
    repo = SQLiteRepository(tmp_path / "text_alert.sqlite3")
    app = create_app(repository=repo)
    client = TestClient(app)

    response = client.post("/webhooks/text-alert", json={"message": "BUY SOLUSDT $50 @ 150 SL 3% TP 8%"})

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"
    assert client.get("/orders").json()["orders"][0]["symbol"] == "SOL/USDT"
    audit_types = [event["event_type"] for event in client.get("/audit").json()["events"]]
    assert audit_types == ["signal.received", "order.accepted"]


def test_text_alert_webhook_queues_when_approval_required(tmp_path):
    repo = SQLiteRepository(tmp_path / "text_approval.sqlite3")
    app = create_app(repository=repo, require_approval=True)
    client = TestClient(app)

    response = client.post("/webhooks/text-alert", json={"message": "BUY BTCUSDT $75 @ 50000 SL 2%"})

    assert response.status_code == 200
    assert response.json()["status"] == "approval_required"
    assert client.get("/orders").json()["orders"] == []
    assert client.get("/approvals").json()["pending"][0]["symbol"] == "BTC/USDT"


def test_text_alert_webhook_rejects_unparseable_message():
    app = create_app()
    client = TestClient(app)

    response = client.post("/webhooks/text-alert", json={"message": "BTC might run soon"})

    assert response.status_code == 400
    assert client.get("/orders").json()["orders"] == []


def test_text_alert_webhook_requires_signature_when_secret_is_configured():
    app = create_app(webhook_secret="top-secret")
    client = TestClient(app)

    response = client.post("/webhooks/text-alert", json={"message": "BUY BTCUSDT $75 @ 50000 SL 2%"})

    assert response.status_code == 401
    assert client.get("/orders").json()["orders"] == []
