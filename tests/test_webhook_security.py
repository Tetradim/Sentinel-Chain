import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from autocrypto.app import create_app


def test_signed_webhook_rejects_missing_or_bad_signature_then_accepts_valid_signature():
    app = create_app(webhook_secret="top-secret")
    client = TestClient(app)
    payload = {
        "symbol": "BTC/USDT",
        "side": "buy",
        "quote_amount": "25",
        "price": "50000",
        "stop_loss_pct": "2",
    }
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    timestamp = "2000000000"

    missing = client.post(
        "/webhooks/tradingview",
        content=body,
        headers={"content-type": "application/json"},
    )
    assert missing.status_code == 401

    bad = client.post(
        "/webhooks/tradingview",
        content=body,
        headers={
            "content-type": "application/json",
            "x-auto-crypto-timestamp": timestamp,
            "x-auto-crypto-signature": "sha256=bad",
        },
    )
    assert bad.status_code == 401

    digest = hmac.new(b"top-secret", timestamp.encode("utf-8") + b"." + body, hashlib.sha256).hexdigest()
    accepted = client.post(
        "/webhooks/tradingview",
        content=body,
        headers={
            "content-type": "application/json",
            "x-auto-crypto-timestamp": timestamp,
            "x-auto-crypto-signature": f"sha256={digest}",
        },
    )

    assert accepted.status_code == 200
    assert accepted.json()["status"] == "accepted"

