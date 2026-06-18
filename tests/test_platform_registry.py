from autocrypto.exchanges.platform_registry import get_platform, platform_rows


EXPECTED_PLATFORM_IDS = {
    "coinbase",
    "kraken",
    "gemini",
    "bitstamp",
    "binanceus",
    "alpaca",
    "robinhood",
    "cryptocom",
    "okx",
    "bybit",
    "kucoin",
    "bitget",
    "gateio",
    "mexc",
    "phemex",
    "bitmex",
    "deribit",
    "bitunix",
}


def test_registry_contains_all_requested_bitcoin_trading_platforms():
    rows = platform_rows(set())

    assert {row["exchange_id"] for row in rows} == EXPECTED_PLATFORM_IDS
    assert rows[0]["exchange_id"] == "coinbase"
    assert get_platform("binance-us").exchange_id == "binanceus"
    assert get_platform("crypto.com").exchange_id == "cryptocom"


def test_deribit_and_bitmex_are_registered_as_derivatives_targets():
    deribit = get_platform("deribit").to_dict(ccxt_exchange_ids={"deribit"})
    bitmex = get_platform("bitmex").to_dict(ccxt_exchange_ids={"bitmex"})

    assert deribit["driver_available"] is True
    assert {"options", "futures", "swap"}.issubset(set(deribit["market_types"]))
    assert bitmex["driver_available"] is True
    assert {"swap", "futures"}.issubset(set(bitmex["market_types"]))


def test_registry_reports_credential_presence_without_values(monkeypatch):
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_KEY", "key-value")
    monkeypatch.setenv("AUTO_CRYPTO_KRAKEN_API_SECRET", "secret-value")

    kraken = get_platform("kraken").to_dict(ccxt_exchange_ids={"kraken"})

    assert kraken["credentials_configured"] is True
    assert all(field["configured"] for field in kraken["credential_fields"])
    assert "key-value" not in str(kraken)
    assert "secret-value" not in str(kraken)
