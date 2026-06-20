from decimal import Decimal

from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.repository import SQLiteRepository
from autocrypto.risk import RiskConfig


def test_app_records_signal_order_and_audit_history(tmp_path):
    repo = SQLiteRepository(tmp_path / "app.sqlite3")
    app = create_app(repository=repo)
    client = TestClient(app)

    response = client.post(
        "/webhooks/tradingview",
        json={
            "symbol": "ETHUSDT",
            "side": "buy",
            "quote_amount": "30",
            "price": "3000",
            "stop_loss_pct": "2",
            "take_profit_pct": "4",
        },
    )

    assert response.status_code == 200
    assert client.get("/signals").json()["signals"][0]["symbol"] == "ETH/USDT"
    order = client.get("/orders").json()["orders"][0]
    assert order["symbol"] == "ETH/USDT"
    assert order["created_at"]
    audit_types = [event["event_type"] for event in client.get("/audit").json()["events"]]
    assert audit_types == ["signal.received", "order.accepted"]


def test_app_rejects_duplicate_signal_after_restart_with_same_repository(tmp_path):
    db_path = tmp_path / "restart.sqlite3"
    first_client = TestClient(create_app(repository=SQLiteRepository(db_path)))
    payload = {
        "signal_id": "restart-duplicate",
        "symbol": "ETHUSDT",
        "side": "buy",
        "quote_amount": "30",
        "price": "3000",
        "stop_loss_pct": "2",
        "take_profit_pct": "4",
    }

    first = first_client.post("/webhooks/tradingview", json=payload)
    second_client = TestClient(create_app(repository=SQLiteRepository(db_path)))
    second = second_client.post("/webhooks/tradingview", json=payload)

    repo = SQLiteRepository(db_path)
    assert first.status_code == 200
    assert first.json()["status"] == "accepted"
    assert second.status_code == 200
    assert second.json()["status"] == "duplicate"
    assert len(repo.list_orders()) == 1
    assert [event.event_type for event in repo.list_audit()] == [
        "signal.received",
        "order.accepted",
        "signal.duplicate",
    ]


def test_app_rehydrates_paper_positions_and_brackets_from_order_history(tmp_path):
    db_path = tmp_path / "rehydrate.sqlite3"
    first_client = TestClient(create_app(repository=SQLiteRepository(db_path)))
    first_client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "rehydrate-entry",
            "symbol": "SOLUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "2",
            "take_profit_pct": "5",
        },
    )

    second_client = TestClient(create_app(repository=SQLiteRepository(db_path)))

    assert second_client.get("/positions").json()["positions"][0]["quantity"] == "1.00000000"
    triggered = second_client.post("/market/price", json={"symbol": "SOLUSDT", "price": "105"})

    assert triggered.json()["triggered"] == [
        {"symbol": "SOL/USDT", "kind": "take_profit", "price": "105.00000000", "quantity": "1.00000000"}
    ]
    assert SQLiteRepository(db_path).list_orders()[-1]["side"] == "sell"


def test_app_rehydrates_open_notional_for_risk_after_restart(tmp_path):
    db_path = tmp_path / "rehydrate_risk.sqlite3"
    risk = RiskConfig(max_order_notional=Decimal("500"), max_open_notional=Decimal("150"))
    first_client = TestClient(create_app(repository=SQLiteRepository(db_path), risk_config=risk))
    first_client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "first-risk-rehydrate",
            "symbol": "BTCUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "50000",
            "stop_loss_pct": "2",
        },
    )
    second_client = TestClient(create_app(repository=SQLiteRepository(db_path), risk_config=risk))

    response = second_client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "second-risk-rehydrate",
            "symbol": "ETHUSDT",
            "side": "buy",
            "quote_amount": "75",
            "price": "3000",
            "stop_loss_pct": "2",
        },
    )

    assert response.json()["status"] == "rejected"
    assert "max_open_notional_exceeded" in response.json()["risk"]["reason_codes"]


def test_app_lists_and_amends_bracket_stop_with_audit(tmp_path):
    repo = SQLiteRepository(tmp_path / "bracket_amend.sqlite3")
    client = TestClient(create_app(repository=repo))
    client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "api-stop-amend",
            "symbol": "SOLUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "5",
            "take_profit_pct": "10",
        },
    )

    listed = client.get("/brackets").json()["brackets"]
    amended = client.post(
        "/brackets/api-stop-amend/stop",
        json={"trigger_price": "99", "reason": "trail manual support"},
    )
    loosened = client.post("/brackets/api-stop-amend/stop", json={"trigger_price": "94"})

    assert listed[0]["signal_id"] == "api-stop-amend"
    assert amended.status_code == 200
    assert amended.json()["status"] == "amended"
    assert amended.json()["active_exits"][0]["trigger_price"] == "99.00"
    assert loosened.status_code == 409
    assert repo.list_orders()[-1]["exit_kind"] == "bracket_stop_amend"
    assert repo.list_audit()[-1].event_type == "bracket.stop_amended"


def test_app_replays_bracket_stop_amendment_after_restart(tmp_path):
    db_path = tmp_path / "bracket_amend_replay.sqlite3"
    first_client = TestClient(create_app(repository=SQLiteRepository(db_path)))
    first_client.post(
        "/webhooks/tradingview",
        json={
            "signal_id": "replay-stop-amend",
            "symbol": "SOLUSDT",
            "side": "buy",
            "quote_amount": "100",
            "price": "100",
            "stop_loss_pct": "5",
            "take_profit_pct": "10",
        },
    )
    first_client.post("/brackets/replay-stop-amend/stop", json={"trigger_price": "99"})

    second_client = TestClient(create_app(repository=SQLiteRepository(db_path)))
    bracket = second_client.get("/brackets/replay-stop-amend").json()
    triggered = second_client.post("/market/price", json={"symbol": "SOLUSDT", "price": "99"})

    assert bracket["active_exits"][0]["trigger_price"] == "99.00"
    assert triggered.json()["triggered"] == [
        {"symbol": "SOL/USDT", "kind": "stop_loss", "price": "99.00000000", "quantity": "1.00000000"}
    ]
