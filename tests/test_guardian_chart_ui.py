from fastapi.testclient import TestClient

from sentinel_chain.app import create_app


def test_guardian_chart_ui_routes_are_served():
    client = TestClient(create_app())

    health = client.get("/guardian/health")
    ui = client.get("/guardian/ui")
    css = client.get("/guardian/static/sentinel_guardian.css")
    script = client.get("/guardian/static/sentinel_guardian.js")
    unknown = client.get("/guardian/static/not_allowed.js")

    assert health.status_code == 200
    assert health.json()["mode"] == "guardian_decision_support_with_locked_live_gates"
    assert health.json()["live_execution_routes"] is True
    assert "/guardian/ws/candles" in health.json()["streaming_routes"]
    assert ui.status_code == 200
    assert "Sentinel Chain Guardian Chart" in ui.text
    assert "Guardian TP/SL Console" in ui.text
    assert 'id="leverageInput" type="number" value="3" step="1" min="1" max="200"' in ui.text
    assert 'id="ticketLeverageInput" type="number" value="3" min="1" max="200"' in ui.text
    assert 'href="static/sentinel_guardian.css"' in ui.text
    assert 'src="static/sentinel_guardian.js"' in ui.text
    assert css.status_code == 200
    assert "--gold-bright" in css.text
    assert ".app-shell" in css.text
    assert "#chartCanvas" in css.text
    assert script.status_code == 200
    assert "function detectVCP" in script.text
    assert "EDGE_HEATMAP_SAMPLE" in script.text
    assert "data-close-symbol" not in script.text
    assert "data-inspect-position" in script.text
    assert "target.dataset.inspectPosition" in script.text
    assert "change_leverage" in script.text
    assert "futures_risk_config" in script.text
    assert "data-bracket-action=\"amend-stop\"" in script.text
    assert "data-bracket-action=\"amend-trailing\"" in script.text
    assert "data-bracket-action=\"amend-tp\"" in script.text
    assert "data-bracket-action=\"close-protective\"" in script.text
    assert unknown.status_code == 404


def test_guardian_desk_symbol_switch_reloads_symbol_specific_chart():
    client = TestClient(create_app())
    script = client.get("/guardian/static/sentinel_guardian.js").text

    assert "function selectDeskSymbol" in script
    assert 'selectDeskSymbol(btn.dataset.symbol)' in script
    assert 'markCandleSeries(symbol, currentTimeframe(), "demo")' in script
    assert "latestChartPriceFor(payload.symbol)" in script
    assert '$("#symbolInput").value = btn.dataset.symbol' not in script
    assert "payload.price || state.candles.at(-1)?.close" not in script
