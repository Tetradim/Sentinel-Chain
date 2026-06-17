from __future__ import annotations

import hashlib
import hmac


class WebhookSignatureError(ValueError):
    """Raised when a signed webhook request cannot be authenticated."""


def verify_webhook_signature(
    *,
    secret: str | None,
    body: bytes,
    timestamp: str | None,
    signature: str | None,
) -> None:
    """Verify an Auto-Crypto HMAC signature.

    Signature format: sha256=<hex digest>
    Signed payload: <timestamp>.<raw request body>
    """

    if not secret:
        return
    if not timestamp or not signature:
        raise WebhookSignatureError("missing webhook signature headers")
    if not signature.startswith("sha256="):
        raise WebhookSignatureError("invalid webhook signature format")

    expected = hmac.new(
        secret.encode("utf-8"),
        timestamp.encode("utf-8") + b"." + body,
        hashlib.sha256,
    ).hexdigest()
    supplied = signature.removeprefix("sha256=")
    if not hmac.compare_digest(expected, supplied):
        raise WebhookSignatureError("invalid webhook signature")

