from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from .approvals import ApprovalQueue
from .config import load_settings
from .engine import TradingEngine
from .execution import PaperExchange
from .repository import SQLiteRepository
from .risk import AccountState, RiskConfig
from .security import (
    InMemoryWebhookReplayStore,
    WebhookReplayError,
    WebhookSignatureError,
    verify_webhook_signature,
)
from .signals import SignalValidationError, normalize_signal


def create_app(
    *,
    exchange: PaperExchange | None = None,
    risk_config: RiskConfig | None = None,
    account_state: AccountState | None = None,
    webhook_secret: str | None = None,
    webhook_clock: Callable[[], float] | None = None,
    webhook_tolerance_seconds: int | None = None,
    repository: SQLiteRepository | None = None,
    require_approval: bool = False,
) -> FastAPI:
    app = FastAPI(title="Auto-Crypto", version="0.1.0")
    engine = TradingEngine(
        exchange=exchange or PaperExchange(),
        risk_config=risk_config or RiskConfig(),
        account_state=account_state or AccountState(),
    )
    secret = webhook_secret if webhook_secret is not None else os.getenv("AUTO_CRYPTO_WEBHOOK_SECRET")
    replay_store = InMemoryWebhookReplayStore()
    approvals = ApprovalQueue()

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "default_mode": "paper",
            "orders": len(engine.exchange.orders),
            "halted": engine.halted,
            "halt_reason": engine.halt_reason,
        }

    @app.get("/control/status")
    def control_status() -> dict[str, Any]:
        return {"halted": engine.halted, "reason": engine.halt_reason}

    @app.post("/control/halt")
    async def halt(request: Request) -> dict[str, Any]:
        payload = await request.json()
        reason = str(payload.get("reason") or "manual halt")
        engine.halt(reason)
        if repository:
            repository.record_audit("trading.halted", {"reason": reason})
        return {"halted": True, "reason": reason}

    @app.post("/control/resume")
    def resume() -> dict[str, Any]:
        engine.resume()
        if repository:
            repository.record_audit("trading.resumed", {})
        return {"halted": False, "reason": ""}

    @app.post("/webhooks/tradingview")
    async def tradingview_webhook(request: Request) -> dict[str, Any]:
        body = await request.body()
        try:
            verify_webhook_signature(
                secret=secret,
                body=body,
                timestamp=request.headers.get("x-auto-crypto-timestamp"),
                signature=request.headers.get("x-auto-crypto-signature"),
                clock=webhook_clock,
                tolerance_seconds=webhook_tolerance_seconds,
                replay_store=replay_store,
            )
        except WebhookSignatureError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except WebhookReplayError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="tradingview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if repository:
            repository.save_signal(signal)
            repository.record_audit("signal.received", {"signal_id": signal.signal_id})
        if require_approval:
            approvals.add(signal)
            if repository:
                repository.record_audit("approval.requested", {"signal_id": signal.signal_id})
            return {"status": "approval_required", "signal_id": signal.signal_id}
        result = engine.process_signal(signal)
        if repository:
            if result.order:
                repository.save_order(result.order)
                repository.record_audit("order.accepted", {"order_id": result.order.order_id})
            elif result.status == "halted":
                repository.record_audit(
                    "order.halted",
                    {"signal_id": signal.signal_id, "reason": result.reason},
                )
            elif result.status == "rejected":
                repository.record_audit(
                    "order.rejected",
                    {"signal_id": signal.signal_id, "reason_codes": result.decision.reason_codes},
                )
        return result.to_dict()

    @app.get("/orders")
    def orders() -> dict[str, Any]:
        if repository:
            return {"orders": repository.list_orders()}
        return {"orders": [order.to_dict() for order in engine.exchange.orders]}

    @app.get("/positions")
    def positions() -> dict[str, Any]:
        return {"positions": engine.exchange.list_positions()}

    @app.get("/approvals")
    def list_approvals() -> dict[str, Any]:
        return {"pending": approvals.list_pending()}

    @app.post("/approvals/{signal_id}/approve")
    def approve_signal(signal_id: str) -> dict[str, Any]:
        signal = approvals.pop(signal_id)
        if signal is None:
            raise HTTPException(status_code=404, detail="pending signal not found")
        result = engine.process_signal(signal)
        if repository:
            if result.order:
                repository.save_order(result.order)
                repository.record_audit("order.accepted", {"order_id": result.order.order_id})
            elif result.status == "rejected":
                repository.record_audit(
                    "order.rejected",
                    {"signal_id": signal.signal_id, "reason_codes": result.decision.reason_codes},
                )
        return result.to_dict()

    @app.post("/approvals/{signal_id}/reject")
    async def reject_signal(signal_id: str, request: Request) -> dict[str, Any]:
        signal = approvals.pop(signal_id)
        if signal is None:
            raise HTTPException(status_code=404, detail="pending signal not found")
        payload = await request.json()
        reason = str(payload.get("reason") or "")
        if repository:
            repository.record_audit(
                "approval.rejected",
                {"signal_id": signal.signal_id, "reason": reason},
            )
        return {"status": "rejected", "signal_id": signal.signal_id}

    @app.get("/signals")
    def signals() -> dict[str, Any]:
        return {"signals": repository.list_signals() if repository else []}

    @app.get("/audit")
    def audit() -> dict[str, Any]:
        return {"events": [event.to_dict() for event in repository.list_audit()] if repository else []}

    return app


def create_app_from_env() -> FastAPI:
    settings = load_settings()
    repository = SQLiteRepository(settings.db_path) if settings.db_path else None
    return create_app(
        risk_config=settings.risk,
        webhook_secret=settings.webhook_secret,
        webhook_tolerance_seconds=settings.webhook_tolerance_seconds,
        repository=repository,
        require_approval=settings.require_approval,
    )


app = create_app()
