import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from sentinel_chain.app import create_app
from sentinel_chain.risk import RiskConfig


class FakeCcxtExchange:
    has = {
        "spot": True,
        "margin": True,
        "swap": True,
        "future": True,
        "option": False,
        "createOrder": True,
        "cancelOrder": True,
        "fetchBalance": True,
    }

    def __init__(self, credentials=None):
        self.credentials = credentials or {}

    def fetch_ticker(self, symbol):
        return {"symbol": symbol, "last": 60000}

    def fetch_tickers(self, symbols=None):
        symbols = symbols or ["BTC/USDT", "ETH/USDT"]
        return {symbol: {"symbol": symbol, "last": 1} for symbol in symbols}

    def fetch_balance(self):
        return {"USDT": {"total": 1000, "free": 900}}

    def create_order(self, symbol, order_type, side, amount, price=None, params=None):
        return {
            "id": "fake-live-order",
            "symbol": symbol,
            "type": order_type,
            "side": side,
            "amount": amount,
            "price": price,
            "params": params or {},
        }

    def cancel_order(self, order_id, symbol=None, params=None):
        return {"id": order_id, "symbol": symbol, "status": "canceled", "params": params or {}}


def install_fake_ccxt(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "ccxt",
        SimpleNamespace(exchanges=["kraken", "okx"], kraken=FakeCcxtExchange, okx=FakeCcxtExchange),
    )


def operator_client(app=None):
    client = TestClient(app or create_app())
    assert client.get("/guardian/ui").status_code == 200
    return client


def test_ccxt_catalog_and_public_ticker_use_generic_adapter(monkeypatch):
    install_fake_ccxt(monkeypatch)
    client = TestClient(create_app())

    catalog = client.get("/exchanges/ccxt/catalog")
    ticker = client.get("/exchanges/kraken/ccxt/ticker?symbol=BTC/USDT")

    assert catalog.status_code == 200
    assert catalog.json()["count"] == 2
    assert [row["exchange_id"] for row in catalog.json()["exchanges"]] == ["kraken", "okx"]
    assert ticker.status_code == 200
    assert ticker.json()["ticker"]["last"] == 60000


def test_ccxt_private_balance_requires_operator_session(monkeypatch):
    install_fake_ccxt(monkeypatch)
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_KEY", "key")
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_SECRET", "secret")
    client = TestClient(create_app())

    response = client.get("/exchanges/kraken/ccxt/balance")

    assert response.status_code == 401


def test_ccxt_private_balance_uses_redacted_env_credentials(monkeypatch):
    install_fake_ccxt(monkeypatch)
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_KEY", "key-value-123")
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_SECRET", "secret-value-456")
    client = operator_client()

    response = client.get("/exchanges/kraken/ccxt/balance")
    status = client.get("/exchanges/kraken/ccxt/status")

    assert response.status_code == 200
    assert response.json()["balance"]["USDT"]["free"] == 900
    assert status.json()["credential_status"]["configured"] is True
    assert "key-value-123" not in str(status.json())
    assert "secret-value-456" not in str(status.json())


def test_ccxt_order_preview_is_locked_by_default(monkeypatch):
    install_fake_ccxt(monkeypatch)
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_KEY", "key")
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_SECRET", "secret")
    client = operator_client(create_app(risk_config=RiskConfig(allowed_exchanges={"paper", "kraken"})))

    response = client.post(
        "/exchanges/kraken/ccxt/order/preview",
        json={
            "signal": {
                "symbol": "BTC/USDT",
                "side": "buy",
                "exchange": "kraken",
                "market_type": "spot",
                "quote_amount": "100",
                "price": "60000",
                "stop_loss_price": "59000",
            }
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["preview"]["live_order_safe"] is False
    assert "ccxt_live_execution_disabled" in body["preview"]["reason_codes"]
    assert "bracket_exits_not_generic_ccxt_live_safe" in body["preview"]["reason_codes"]


def test_ccxt_live_submit_stays_blocked_without_safe_preview(monkeypatch):
    install_fake_ccxt(monkeypatch)
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_KEY", "key")
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_SECRET", "secret")
    client = operator_client(create_app(risk_config=RiskConfig(allowed_exchanges={"paper", "kraken"})))
    preview = client.post(
        "/exchanges/kraken/ccxt/order/preview",
        json={
            "signal": {
                "symbol": "BTC/USDT",
                "side": "buy",
                "exchange": "kraken",
                "market_type": "spot",
                "quote_amount": "100",
                "price": "60000",
                "stop_loss_price": "59000",
            }
        },
    ).json()

    submitted = client.post(
        "/exchanges/kraken/ccxt/order",
        json={"preview_id": preview["preview_id"], "confirmation": "PLACE LIVE ORDER"},
    )

    assert submitted.status_code == 409
    assert submitted.json()["detail"]["message"] == "CCXT live order is not safe to submit"
