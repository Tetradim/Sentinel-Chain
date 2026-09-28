from decimal import Decimal

from fastapi.testclient import TestClient

from sentinel_chain.app import create_app
from sentinel_chain.risk import RiskConfig


def _operator_client(app=None) -> TestClient:
    client = TestClient(app or create_app())
    response = client.get("/guardian/ui")
    assert response.status_code == 200
    return client


def test_guardian_drawing_storage_round_trip():
    client = _operator_client()

    payload = {
        "symbol": "BTCUSDT",
        "drawings": [{"type": "hline", "price": 60000, "label": "Risk line"}],
    }

    saved = client.post("/guardian/drawings", json=payload)
    assert saved.status_code == 200, saved.text
    assert saved.json()["symbol"] == "BTCUSDT"
    assert saved.json()["count"] == 1

    loaded = client.get("/guardian/drawings?symbol=BTCUSDT")
    assert loaded.status_code == 200
    assert loaded.json()["drawings"][0]["type"] == "hline"

    deleted = client.delete("/guardian/drawings?symbol=BTCUSDT")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True


def test_guardian_edge_snapshot_round_trip_accepts_gex_style_payload():
    client = _operator_client()

    snapshot = {
        "symbol": "SPY",
        "mode": "GEX",
        "current_price": 745.7,
        "support": 745.3695,
        "resistance": 746.0305,
        "risk_score": 68,
        "regime": "Range / Neutral",
    }

    saved = client.post("/guardian/edge/snapshot", json=snapshot)
    assert saved.status_code == 200, saved.text
    assert saved.json()["snapshot"]["symbol"] == "SPY"

    latest = client.get("/guardian/edge/latest?symbol=SPY&mode=GEX")
    assert latest.status_code == 200
    assert latest.json()["count"] == 1
    assert latest.json()["snapshots"][0]["risk_score"] == 68


def test_guardian_live_status_and_preview_stay_locked_by_default(monkeypatch):
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_API_KEY", raising=False)
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_SECRET_KEY", raising=False)
    monkeypatch.delenv("AUTO_CRYPTO_LIVE_TRADING_CONFIRMATION", raising=False)
    monkeypatch.setenv("AUTO_CRYPTO_REQUIRE_APPROVAL", "false")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", "false")

    app = create_app(
        risk_config=RiskConfig(
            allowed_exchanges={"paper", "bitunix"},
            max_order_notional=Decimal("1000"),
            max_leverage=Decimal("5"),
            require_stop_loss=True,
        )
    )
    client = _operator_client(app)

    status = client.get("/guardian/live/status")
    assert status.status_code == 200
    assert status.json()["bitunix"]["live_execution_enabled"] is False
    assert status.json()["safety_model"]["default"] == "locked"

    signal = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "exchange": "bitunix",
        "market_type": "futures",
        "quote_amount": "100",
        "price": "60000",
        "stop_loss_price": "59000",
        "take_profit_targets": [{"trigger_price": "62000", "close_pct": "100"}],
        "leverage": "1",
    }
    preview = client.post("/guardian/live/preview", json={"signal": signal})
    assert preview.status_code == 200, preview.text
    preview_json = preview.json()
    assert preview_json["preview"]["live_order_safe"] is False
    assert "bitunix_live_execution_disabled" in preview_json["preview"]["reason_codes"]
    assert "bitunix_credentials_missing" in preview_json["preview"]["reason_codes"]


def test_guardian_live_submit_changes_bitunix_leverage_before_order(monkeypatch):
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_API_KEY", "key")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_SECRET_KEY", "secret")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", "true")
    monkeypatch.setenv("AUTO_CRYPTO_REQUIRE_APPROVAL", "true")
    monkeypatch.setenv("AUTO_CRYPTO_WEBHOOK_SECRET", "x" * 32)
    monkeypatch.setenv("AUTO_CRYPTO_LIVE_TRADING_CONFIRMATION", "ENABLE LIVE CRYPTO TRADING")

    class FakeBitunixClient:
        calls = []

        def __init__(self, **_kwargs):
            pass

        def change_futures_leverage(self, symbol, leverage, margin_coin="USDT"):
            self.calls.append(("change_leverage", symbol, leverage, margin_coin))
            return {"code": 0, "data": [{"marginCoin": margin_coin, "leverage": leverage, "symbol": symbol}], "msg": "Success"}

        def place_futures_order(self, payload):
            self.calls.append(("place_order", dict(payload)))
            return {"code": 0, "data": {"orderId": "live-1", "clientId": payload["clientId"]}, "msg": "Success"}

    monkeypatch.setattr("sentinel_chain.app.BitunixRestClient", FakeBitunixClient)

    app = create_app(
        risk_config=RiskConfig(
            allowed_exchanges={"paper", "bitunix"},
            max_order_notional=Decimal("1000"),
            max_leverage=Decimal("200"),
            require_stop_loss=True,
        )
    )
    client = _operator_client(app)
    signal = {
        "symbol": "BTCUSDT",
        "side": "buy",
        "exchange": "bitunix",
        "market_type": "futures",
        "quote_amount": "100",
        "price": "60000",
        "stop_loss_price": "59000",
        "take_profit_targets": [{"trigger_price": "62000", "close_pct": "100"}],
        "leverage": "25",
        "futures_risk_config": {"max_leverage": "200", "min_liquidation_buffer_pct": "0"},
    }

    preview = client.post("/guardian/live/preview", json={"signal": signal})
    assert preview.status_code == 200, preview.text
    preview_json = preview.json()
    assert preview_json["preview"]["live_order_safe"] is True
    assert preview_json["preview"]["leverage_setting"] == {
        "endpoint": "/api/v1/futures/account/change_leverage",
        "marginCoin": "USDT",
        "symbol": "BTCUSDT",
        "leverage": 25,
    }

    submitted = client.post(
        "/guardian/live/submit",
        json={"preview_id": preview_json["preview_id"], "confirmation": "PLACE LIVE ORDER"},
    )

    assert submitted.status_code == 200, submitted.text
    assert FakeBitunixClient.calls[0] == ("change_leverage", "BTCUSDT", 25, "USDT")
    assert FakeBitunixClient.calls[1][0] == "place_order"
    assert submitted.json()["leverage_response"]["data"][0]["leverage"] == 25
