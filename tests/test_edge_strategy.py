from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import sentinel_chain.edge_strategy as edge_strategy
from sentinel_chain.bot_event_bus import BotEvent, EventBusStore, register_event_listener
from sentinel_chain.edge_strategy import EdgeAuthorizationStore
from sentinel_chain.signals import CryptoSignal


def _signal(*, reduce_only: bool = False) -> CryptoSignal:
    return CryptoSignal(
        signal_id="chain-test-1",
        source="test",
        symbol="BTCUSDT",
        side="sell" if reduce_only else "buy",
        quote_amount=Decimal("500"),
        price=Decimal("100"),
        stop_loss_price=Decimal("98"),
        take_profit_price=Decimal("104"),
        reduce_only=reduce_only,
        strategy_id="momentum_breakout",
        raw_payload={"confidence": 0.85, "regime": "trending_up"},
    )


def _authorization():
    now = datetime.now(timezone.utc)
    return {
        "contract_version": "edge.strategy.authorization.v1",
        "authorized": True,
        "symbol": "BTCUSDT",
        "target_bot": "sentinel-chain",
        "target_notional": 500.0,
        "trade_card": {
            "card_id": "edge-card:chain",
            "strategy_id": "edge-strategy:chain",
            "thesis_id": "edge-thesis:chain",
            "position_id": "edge-position:chain",
            "symbol": "BTCUSDT",
            "target_bot": "sentinel-chain",
            "direction": "long",
            "state": "armed",
            "target_notional": 500.0,
            "expires_at": (now + timedelta(minutes=10)).isoformat(),
            "updated_at": now.isoformat(),
            "metadata": {"stop_owner": {"position_id": "edge-position:chain", "inherit_on_reentry": False}},
        },
    }


def test_automatically_requests_and_caches_edge_authorization(monkeypatch, tmp_path):
    store = EdgeAuthorizationStore(tmp_path / "auth.json")
    monkeypatch.setattr(edge_strategy, "authorizations", store)
    monkeypatch.setattr(edge_strategy, "_edge_request", lambda path, payload: {"authorization": _authorization()})
    monkeypatch.setenv("CHAIN_REQUIRE_EDGE_AUTHORIZATION", "true")

    assert edge_strategy.ensure_authorized(_signal()) == []
    assert store.latest_for_symbol("BTCUSDT")["trade_card"]["card_id"] == "edge-card:chain"


def test_reduce_only_exit_does_not_depend_on_edge(monkeypatch):
    monkeypatch.setenv("CHAIN_REQUIRE_EDGE_AUTHORIZATION", "true")
    monkeypatch.setattr(edge_strategy, "_edge_request", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("offline")))

    assert edge_strategy.ensure_authorized(_signal(reduce_only=True)) == []


def test_rejects_expired_or_wrong_bot_authorization(tmp_path):
    store = EdgeAuthorizationStore(tmp_path / "auth.json")
    authorization = _authorization()
    authorization["target_bot"] = "sentinel-iron"

    reasons = store.validation_reasons(
        authorization,
        symbol="BTCUSDT",
        side="buy",
        requested_notional=Decimal("500"),
    )

    assert "edge_authorization_wrong_bot" in reasons


def test_event_listener_receives_targeted_authorization(monkeypatch, tmp_path):
    store = EdgeAuthorizationStore(tmp_path / "auth.json")
    monkeypatch.setattr(edge_strategy, "authorizations", store)
    bus = EventBusStore(tmp_path / "events")
    register_event_listener(edge_strategy.receive_authorization_event)

    bus.publish(
        BotEvent(
            event_type="edge.strategy.authorization",
            source_bot="sentinel-edge",
            target_bots=["sentinel-chain"],
            payload=_authorization(),
        )
    )

    assert store.latest_for_symbol("BTCUSDT") is not None
