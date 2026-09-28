from sentinel_chain.api.bracket_views import active_brackets_to_dict
from sentinel_chain.engine import TradingEngine
from sentinel_chain.execution import PaperExchange
from sentinel_chain.signals import normalize_signal


def test_active_brackets_view_reports_open_risk_summary():
    exchange = PaperExchange()
    engine = TradingEngine(exchange=exchange)
    signal = normalize_signal(
        {
            "signal_id": "view-risk",
            "symbol": "BTC/USDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "5",
            "take_profit_pct": "10",
        },
        source="test",
    )
    engine.process_signal(signal)

    rows = active_brackets_to_dict(exchange.lots)

    assert rows[0]["signal_id"] == "view-risk"
    assert rows[0]["summary"]["worst_case_loss"] == "5.00"
    assert rows[0]["summary"]["first_target_reward"] == "10.00"
