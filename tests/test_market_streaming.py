from sentinel_chain.market_streaming import bitunix_kline_channel, normalize_bitunix_ws_kline_message


def test_bitunix_kline_channel_maps_common_intervals():
    assert bitunix_kline_channel("1m") == "market_kline_1min"
    assert bitunix_kline_channel("15m", price_type="mark") == "mark_kline_15min"


def test_normalize_bitunix_ws_kline_message_returns_candle_event():
    event = normalize_bitunix_ws_kline_message(
        {
            "ch": "market_kline_1min",
            "symbol": "BTCUSDT",
            "ts": 1775541412718,
            "data": {"o": "68581.4", "h": "68590", "l": "68579.5", "c": "68583.4", "b": "5.2395"},
        }
    )

    assert event is not None
    assert event["event"] == "candle"
    assert event["source"] == "bitunix_ws"
    assert event["symbol"] == "BTCUSDT"
    assert event["candle"]["close"] == 68583.4
    assert event["candle"]["time"] == "1775541412718"
