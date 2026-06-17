from decimal import Decimal

from autocrypto.engine import TradingEngine
from autocrypto.execution import PaperExchange
from autocrypto.signals import normalize_signal


def test_paper_take_profit_trigger_closes_position_and_records_exit_order():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
        source="test",
    )
    engine.process_signal(signal)

    triggered = exchange.update_price("BTC/USDT", Decimal("105"))

    assert triggered == [{"symbol": "BTC/USDT", "kind": "take_profit", "price": "105.00000000"}]
    assert exchange.list_positions()[0]["quantity"] == "0.00000000"
    assert exchange.list_positions()[0]["realized_pnl"] == "5.00000000"
    assert exchange.orders[-1].side == "sell"


def test_paper_stop_loss_trigger_closes_position_once():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "symbol": "ETH/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
        source="test",
    )
    engine.process_signal(signal)

    first = exchange.update_price("ETH/USDT", Decimal("97"))
    second = exchange.update_price("ETH/USDT", Decimal("96"))

    assert first == [{"symbol": "ETH/USDT", "kind": "stop_loss", "price": "97.00000000"}]
    assert second == []
    assert exchange.list_positions()[0]["realized_pnl"] == "-3.00000000"
