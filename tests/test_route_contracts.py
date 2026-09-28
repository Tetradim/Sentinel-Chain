from fastapi.testclient import TestClient

from sentinel_chain.app import create_app


def test_core_route_contracts_survive_refactors():
    client = TestClient(create_app())
    expected = [
        ("GET", "/health"),
        ("GET", "/ui/state"),
        ("GET", "/guardian/health"),
        ("GET", "/guardian/ui"),
        ("GET", "/war-room/features"),
        ("GET", "/exchanges"),
        ("GET", "/exchanges/platforms"),
        ("GET", "/exchanges/ccxt/catalog"),
        ("GET", "/brackets"),
        ("GET", "/brackets/risk-summary"),
        ("GET", "/signals"),
        ("GET", "/approvals"),
        ("GET", "/audit"),
    ]
    for method, path in expected:
        response = client.request(method, path)
        assert response.status_code == 200, (method, path, response.text)


def test_mutating_routes_keep_expected_validation_behavior():
    client = TestClient(create_app())
    preview = client.post(
        "/signals/preview",
        json={
            "symbol": "BTCUSDT",
            "side": "buy",
            "exchange": "paper",
            "market_type": "swap",
            "quote_amount": "25",
            "price": "65000",
            "stop_loss_price": "64000",
        },
    )
    assert preview.status_code == 200
    body = preview.json()
    assert "risk" in body
    assert "approved" in body["risk"]
    assert "execution" in body
