from fastapi.testclient import TestClient

from sentinel_chain.app import create_app


def test_guardian_static_assets_are_browser_loadable():
    client = TestClient(create_app())
    ui = client.get("/guardian/ui")
    assert ui.status_code == 200
    assert "sentinel_guardian.css" in ui.text
    assert "sentinel_guardian.js" in ui.text

    for asset in [
        "sentinel_guardian.css",
        "sentinel_guardian.js",
    ]:
        response = client.get(f"/guardian/static/{asset}")
        assert response.status_code == 200
        assert response.text


def test_guardian_script_contains_required_ui_hooks():
    client = TestClient(create_app())
    script = client.get("/guardian/static/sentinel_guardian.js").text
    required_hooks = [
        "previewLiveOrderFromTicket",
        "submitLiveOrderFromPreview",
        "startCandleStream",
        "startEdgeStream",
        "saveServerDrawings",
        "loadVenueJson",
    ]
    for hook in required_hooks:
        assert hook in script
