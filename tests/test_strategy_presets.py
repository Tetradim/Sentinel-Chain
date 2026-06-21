from fastapi.testclient import TestClient

from autocrypto.app import create_app
from autocrypto.strategy_presets import apply_strategy_preset, list_strategy_presets


def test_strategy_preset_catalog_is_preview_only():
    app = create_app()
    client = TestClient(app)

    response = client.get("/strategy-presets")

    assert response.status_code == 200
    body = response.json()
    assert body["paper_only"] is True
    assert body["live_submission_enabled"] is False
    assert body["submit_endpoint"] is None
    assert {preset["name"] for preset in body["presets"]} >= {
        "momentum_breakout",
        "dip_reclaim",
        "range_reversion_short",
    }
    momentum = next(preset for preset in body["presets"] if preset["name"] == "momentum_breakout")
    assert momentum["suggested_bracket_template"] == "activation_trailer"
    assert "signal_defaults" in momentum
    assert "entry_logic" in momentum


def test_apply_strategy_preset_keeps_signal_fields_and_applies_overrides():
    payload = apply_strategy_preset(
        {
            "symbol": "BTCUSDT",
            "quote_amount": "100",
            "side": "sell",
        },
        "momentum_breakout",
        overrides={"strategy_id": "custom-breakout"},
    )

    assert payload["side"] == "sell"
    assert payload["market_type"] == "swap"
    assert payload["strategy_id"] == "custom-breakout"
    assert payload["strategy_preset"] == "momentum_breakout"


def test_preview_strategy_composes_suggested_bracket_template_without_order():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/signals/preview-strategy",
        json={
            "strategy": "momentum_breakout",
            "signal": {
                "symbol": "BTCUSDT",
                "quote_amount": "100",
                "price": "100",
            },
        },
    )
    positions_after = client.get("/positions").json()["positions"]

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_preset"]["name"] == "momentum_breakout"
    assert body["template"]["name"] == "activation_trailer"
    assert body["paper_only"] is True
    assert body["live_submission_enabled"] is False
    assert body["signal"]["strategy_id"] == "momentum_breakout"
    assert body["signal"]["stop_loss_pct"] == "4"
    assert body["signal"]["trailing_activation_pct"] == "2"
    assert body["execution"]["would_place_order"] is True
    assert positions_after == []


def test_preview_strategy_allows_explicit_bracket_template_and_overrides():
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/signals/preview-strategy",
        json={
            "strategy": "dip_reclaim",
            "template": "fixed_bracket",
            "signal": {
                "symbol": "ETHUSDT",
                "quote_amount": "100",
                "price": "100",
            },
            "template_overrides": {
                "stop_loss_pct": "5",
                "take_profit_pct": "100",
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy_preset"]["name"] == "dip_reclaim"
    assert body["template"]["name"] == "fixed_bracket"
    assert body["signal"]["stop_loss_pct"] == "5"
    assert body["signal"]["take_profit_pct"] == "100"


def test_unknown_strategy_preset_is_rejected():
    assert "momentum_breakout" in {preset["name"] for preset in list_strategy_presets()}

    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/signals/preview-strategy",
        json={
            "strategy": "does-not-exist",
            "signal": {
                "symbol": "BTCUSDT",
                "quote_amount": "100",
                "price": "100",
            },
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "unknown strategy preset: does-not-exist"
