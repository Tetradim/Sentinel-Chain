from decimal import Decimal

from autocrypto.engine import TradingEngine
from autocrypto.execution import PaperExchange
from autocrypto.idempotency import InMemoryIdempotencyStore
from autocrypto.risk import AccountState, RiskConfig
from autocrypto.signals import normalize_signal


def test_engine_executes_approved_signal_in_paper_with_bracket_exits():
    exchange = PaperExchange()
    engine = TradingEngine(
        exchange=exchange,
        risk_config=RiskConfig(max_order_notional=Decimal("500")),
        account_state=AccountState(equity=Decimal("10000")),
        idempotency=InMemoryIdempotencyStore(),
    )
    signal = normalize_signal(
        {
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "200",
            "price": "50000",
            "stop_loss_pct": "2",
            "take_profit_pct": "4",
            "strategy_id": "breakout",
        },
        source="test",
    )

    result = engine.process_signal(signal)

    assert result.status == "accepted"
    assert result.order is not None
    assert result.order.mode == "paper"
    assert result.order.symbol == "BTC/USDT"
    assert result.order.notional == Decimal("200")
    assert [exit_order.kind for exit_order in result.order.exit_orders] == ["stop_loss", "take_profit"]
    assert result.order.exit_orders[0].trigger_price == Decimal("49000.00")
    assert result.order.exit_orders[1].trigger_price == Decimal("52000.00")


def test_engine_blocks_duplicate_signal_before_second_order():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange, risk_config=RiskConfig(), idempotency=InMemoryIdempotencyStore())
    signal = normalize_signal(
        {
            "symbol": "ETH/USDT",
            "side": "buy",
            "quote_amount": "50",
            "price": "3000",
            "stop_loss_pct": "2",
        },
        source="test",
    )

    first = engine.process_signal(signal)
    second = engine.process_signal(signal)

    assert first.status == "accepted"
    assert second.status == "duplicate"
    assert len(exchange.orders) == 1

