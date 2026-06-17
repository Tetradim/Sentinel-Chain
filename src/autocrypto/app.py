from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from .engine import TradingEngine
from .execution import PaperExchange
from .risk import AccountState, RiskConfig
from .security import WebhookSignatureError, verify_webhook_signature
from .signals import SignalValidationError, normalize_signal


def create_app(
    *,
    exchange: PaperExchange | None = None,
    risk_config: RiskConfig | None = None,
    account_state: AccountState | None = None,
    webhook_secret: str | None = None,
) -> FastAPI:
    app = FastAPI(title="Auto-Crypto", version="0.1.0")
    engine = TradingEngine(
        exchange=exchange or PaperExchange(),
        risk_config=risk_config or RiskConfig(),
        account_state=account_state or AccountState(),
    )
    secret = webhook_secret if webhook_secret is not None else os.getenv("AUTO_CRYPTO_WEBHOOK_SECRET")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "default_mode": "paper", "orders": len(engine.exchange.orders)}

    @app.post("/webhooks/tradingview")
    async def tradingview_webhook(request: Request) -> dict[str, Any]:
        body = await request.body()
        try:
            verify_webhook_signature(
                secret=secret,
                body=body,
                timestamp=request.headers.get("x-auto-crypto-timestamp"),
                signature=request.headers.get("x-auto-crypto-signature"),
            )
        except WebhookSignatureError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="tradingview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return engine.process_signal(signal).to_dict()

    @app.get("/orders")
    def orders() -> dict[str, Any]:
        return {"orders": [order.to_dict() for order in engine.exchange.orders]}

    return app


app = create_app()
