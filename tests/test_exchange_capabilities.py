import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from autocrypto.app import create_app
import autocrypto.exchanges.ccxt_adapter as ccxt_adapter
import autocrypto.app as app_module


def clear_bitunix_env(monkeypatch):
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_API_KEY", raising=False)
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_SECRET_KEY", raising=False)
    monkeypatch.delenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", raising=False)


class FakeExchange:
    has = {
        "spot": True,
        "margin": True,
        "swap": False,
        "future": True,
        "option": False,
        "createOrder": True,
        "cancelOrder": False,
        "fetchBalance": True,
    }

    def __init__(self, credentials):
        self.credentials = credentials


def install_fake_ccxt(monkeypatch):
    monkeypatch.setitem(
        sys.modules,
        "ccxt",
        SimpleNamespace(exchanges=["kraken", "binance"], binance=FakeExchange, kraken=FakeExchange),
    )


def test_ccxt_adapter_lists_exchange_ids_and_reports_capabilities(monkeypatch):
    install_fake_ccxt(monkeypatch)

    assert ccxt_adapter.list_ccxt_exchange_ids() == ["binance", "kraken"]

    adapter = ccxt_adapter.CcxtExchangeAdapter("binance", {"apiKey": "abc"})

    assert adapter.exchange.credentials == {"apiKey": "abc"}
    assert adapter.capabilities().to_dict() == {
        "exchange_id": "binance",
        "spot": True,
        "margin": True,
        "swap": False,
        "future": True,
        "option": False,
        "create_order": True,
        "cancel_order": False,
        "fetch_balance": True,
    }


def test_exchanges_endpoint_returns_paper_and_ccxt_exchange_ids(monkeypatch):
    clear_bitunix_env(monkeypatch)
    install_fake_ccxt(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/exchanges")

    assert response.status_code == 200
    assert response.json() == {
        "ccxt_available": True,
        "exchanges": [
            {
                "exchange_id": "paper",
                "driver": "paper",
                "driver_available": True,
                "credentials_configured": False,
                "live_execution_enabled": False,
            },
            {
                "exchange_id": "bitunix",
                "driver": "bitunix-native",
                "driver_available": True,
                "credentials_configured": False,
                "live_execution_enabled": False,
            },
            {
                "exchange_id": "binance",
                "driver": "ccxt",
                "driver_available": True,
                "credentials_configured": False,
                "live_execution_enabled": False,
            },
            {
                "exchange_id": "kraken",
                "driver": "ccxt",
                "driver_available": True,
                "credentials_configured": False,
                "live_execution_enabled": False,
            },
        ],
    }


def test_exchange_capabilities_endpoint_reports_specific_exchange(monkeypatch):
    install_fake_ccxt(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/exchanges/binance/capabilities")

    assert response.status_code == 200
    assert response.json()["capabilities"] == {
        "exchange_id": "binance",
        "spot": True,
        "margin": True,
        "swap": False,
        "future": True,
        "option": False,
        "create_order": True,
        "cancel_order": False,
        "fetch_balance": True,
    }


def test_exchanges_endpoint_marks_bitunix_credentials(monkeypatch):
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_API_KEY", "configured-key")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_SECRET_KEY", "configured-secret")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_LIVE_ENABLED", "false")
    client = TestClient(create_app())

    bitunix = next(row for row in client.get("/exchanges").json()["exchanges"] if row["exchange_id"] == "bitunix")

    assert bitunix == {
        "exchange_id": "bitunix",
        "driver": "bitunix-native",
        "driver_available": True,
        "credentials_configured": True,
        "live_execution_enabled": False,
    }


def test_bitunix_capabilities_endpoint_reports_native_adapter():
    client = TestClient(create_app())

    response = client.get("/exchanges/bitunix/capabilities")

    assert response.status_code == 200
    assert response.json()["capabilities"] == {
        "exchange_id": "bitunix",
        "spot": True,
        "margin": False,
        "swap": True,
        "future": True,
        "option": False,
        "create_order": True,
        "cancel_order": True,
        "fetch_balance": True,
    }


def test_bitunix_private_account_endpoint_requires_credentials(monkeypatch):
    clear_bitunix_env(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/exchanges/bitunix/futures/account")

    assert response.status_code == 400
    assert "Bitunix API key and secret are required" in response.json()["detail"]


def test_bitunix_public_ticker_endpoint_delegates_to_native_client(monkeypatch):
    def fake_tickers(self, symbols=None):
        return {"code": 0, "data": [{"symbol": symbols}], "msg": "Success"}

    monkeypatch.setattr(app_module.BitunixRestClient, "get_futures_tickers", fake_tickers)
    client = TestClient(create_app())

    response = client.get("/exchanges/bitunix/futures/tickers?symbols=BTCUSDT")

    assert response.status_code == 200
    assert response.json()["data"] == [{"symbol": "BTCUSDT"}]


def test_bitunix_private_account_endpoint_delegates_to_native_client(monkeypatch):
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_API_KEY", "configured-key")
    monkeypatch.setenv("AUTO_CRYPTO_BITUNIX_SECRET_KEY", "configured-secret")

    def fake_account(self, margin_coin="USDT"):
        return {"code": 0, "data": [{"marginCoin": margin_coin}], "msg": "Success"}

    monkeypatch.setattr(app_module.BitunixRestClient, "get_futures_account", fake_account)
    client = TestClient(create_app())

    response = client.get("/exchanges/bitunix/futures/account?margin_coin=USDT")

    assert response.status_code == 200
    assert response.json()["data"] == [{"marginCoin": "USDT"}]
