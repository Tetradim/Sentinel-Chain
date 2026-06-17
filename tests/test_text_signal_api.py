from fastapi.testclient import TestClient

from autocrypto.app import create_app


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

