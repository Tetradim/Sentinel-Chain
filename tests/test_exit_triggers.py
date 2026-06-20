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


def test_paper_exits_track_independent_lots_for_same_symbol():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    first_signal = normalize_signal(
        {
            "signal_id": "first-lot",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
        source="test",
    )
    second_signal = normalize_signal(
        {
            "signal_id": "second-lot",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "200",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "10",
        },
        source="test",
    )
    engine.process_signal(first_signal)
    engine.process_signal(second_signal)

    first_trigger = exchange.update_price("BTC/USDT", Decimal("105"))
    position_after_first = exchange.list_positions()[0]
    second_trigger = exchange.update_price("BTC/USDT", Decimal("110"))
    position_after_second = exchange.list_positions()[0]

    assert first_trigger == [{"symbol": "BTC/USDT", "kind": "take_profit", "price": "105.00000000"}]
    assert position_after_first["quantity"] == "2.00000000"
    assert position_after_first["realized_pnl"] == "5.00000000"
    assert second_trigger == [{"symbol": "BTC/USDT", "kind": "take_profit", "price": "110.00000000"}]
    assert position_after_second["quantity"] == "0.00000000"
    assert position_after_second["realized_pnl"] == "25.00000000"


def test_manual_partial_sell_uses_same_lot_accounting_as_bracket_exits():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    first_signal = normalize_signal(
        {
            "signal_id": "lot-1",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "50",
        },
        source="test",
    )
    second_signal = normalize_signal(
        {
            "signal_id": "lot-2",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "200",
            "price": "200",
            "stop_loss_pct": "2",
            "take_profit_pct": "10",
        },
        source="test",
    )
    manual_sell = normalize_signal(
        {
            "signal_id": "manual-sell",
            "symbol": "BTC/USDT",
            "side": "sell",
            "base_amount": "1",
            "price": "150",
        },
        source="test",
    )

    engine.process_signal(first_signal)
    engine.process_signal(second_signal)
    engine.process_signal(manual_sell)
    after_manual = exchange.list_positions()[0]
    triggered = exchange.update_price("BTC/USDT", Decimal("220"))
    after_exit = exchange.list_positions()[0]

    assert after_manual["quantity"] == "1.00000000"
    assert after_manual["avg_entry"] == "200.00000000"
    assert after_manual["realized_pnl"] == "50.00000000"
    assert triggered == [{"symbol": "BTC/USDT", "kind": "take_profit", "price": "220.00000000"}]
    assert after_exit["quantity"] == "0.00000000"
    assert after_exit["realized_pnl"] == "70.00000000"


def test_trailing_stop_ratcheted_up_then_triggers_on_pullback():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "signal_id": "trailing-entry",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "20",
            "trailing_stop_pct": "5",
        },
        source="test",
    )
    engine.process_signal(signal)

    first = exchange.update_price("BTC/USDT", Decimal("110"))
    trailing_exit = next(exit_order for exit_order in exchange.lots[0].exit_orders if exit_order.kind == "trailing_stop")
    second = exchange.update_price("BTC/USDT", Decimal("104.50"))

    assert first == []
    assert trailing_exit.trigger_price == Decimal("104.50")
    assert second == [{"symbol": "BTC/USDT", "kind": "trailing_stop", "price": "104.50000000"}]
    assert exchange.list_positions()[0]["quantity"] == "0.00000000"
    assert exchange.list_positions()[0]["realized_pnl"] == "4.50000000"


def test_trailing_stop_activation_waits_for_favorable_move_before_arming():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "signal_id": "activated-trail-entry",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "10",
            "take_profit_pct": "30",
            "trailing_stop_pct": "5",
            "trailing_activation_pct": "4",
        },
        source="test",
    )
    engine.process_signal(signal)

    before_activation = exchange.update_price("BTC/USDT", Decimal("96"))
    activation_mark = exchange.update_price("BTC/USDT", Decimal("104"))
    assert exchange.lots[0].trailing_activated is True
    trailing_exit = next(exit_order for exit_order in exchange.lots[0].exit_orders if exit_order.kind == "trailing_stop")
    pullback = exchange.update_price("BTC/USDT", Decimal("98.80"))

    assert before_activation == []
    assert activation_mark == []
    assert trailing_exit.trigger_price == Decimal("98.80")
    assert pullback == [{"symbol": "BTC/USDT", "kind": "trailing_stop", "price": "98.80000000"}]


def test_breakeven_trigger_raises_protective_stops_to_entry():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "signal_id": "breakeven-entry",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "5",
            "take_profit_pct": "20",
            "trailing_stop_pct": "10",
            "breakeven_trigger_pct": "3",
        },
        source="test",
    )
    engine.process_signal(signal)

    first = exchange.update_price("BTC/USDT", Decimal("103"))
    stop_exit = next(exit_order for exit_order in exchange.lots[0].exit_orders if exit_order.kind == "stop_loss")
    trailing_exit = next(exit_order for exit_order in exchange.lots[0].exit_orders if exit_order.kind == "trailing_stop")
    second = exchange.update_price("BTC/USDT", Decimal("100"))

    assert first == []
    assert stop_exit.trigger_price == Decimal("100.00")
    assert trailing_exit.trigger_price == Decimal("100.00")
    assert second == [{"symbol": "BTC/USDT", "kind": "stop_loss", "price": "100.00000000"}]
    assert exchange.list_positions() == []
    assert exchange.orders[-1].side == "sell"
    assert exchange.orders[-1].price == Decimal("100")
