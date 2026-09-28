from __future__ import annotations

import asyncio
import os
import secrets
from copy import deepcopy
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .approvals import ApprovalQueue
from .api.parsing import (
    batch_backtest_candidate_payload as _batch_backtest_candidate_payload,
    bitunix_kline_query as _bitunix_kline_query,
    candle_payload as _candle_payload,
    decimal_value as _decimal,
    execution_cost_payload as _execution_cost_payload,
    non_negative_decimal as _non_negative_decimal,
    non_negative_int as _non_negative_int,
    optional_datetime as _optional_datetime,
    optional_int as _optional_int,
    optional_positive_decimal as _optional_positive_decimal,
    positive_decimal as _positive_decimal,
    stress_scenario_payload as _stress_scenario_payload,
    truthy as _truthy,
)
from .api.bracket_views import (
    active_brackets_to_dict as _active_brackets_to_dict,
    active_exits_to_dict as _active_exits_to_dict,
    bracket_coverage_to_dict as _bracket_coverage_to_dict,
    bracket_decision_support_to_dict as _bracket_decision_support_to_dict,
    bracket_exit_ladder_to_dict as _bracket_exit_ladder_to_dict,
    bracket_health as _bracket_health,
    bracket_oca_groups as _bracket_oca_groups,
    bracket_preview_impact as _bracket_preview_impact,
    bracket_risk_summary as _bracket_risk_summary,
    bracket_summary as _bracket_summary,
    trailing_preview_snapshot as _trailing_preview_snapshot,
    trailing_snapshot_activated as _trailing_snapshot_activated,
    trailing_snapshot_ratcheted as _trailing_snapshot_ratcheted,
)
from .api.serializers import (
    account_state_to_dict as _account_state_to_dict,
    bracket_plan_to_dict as _bracket_plan_to_dict,
    decimal_to_plain as _decimal_to_plain,
    money as _money,
    risk_config_to_dict as _risk_config_to_dict,
    risk_decision_to_dict as _risk_decision_to_dict,
    signal_preview as _signal_preview,
    signal_to_dict as _signal_to_dict,
    target_reward as _target_reward,
    total_target_reward as _total_target_reward,
    worst_case_loss as _worst_case_loss,
)
from .brackets import (
    exit_order_payload,
    trailing_ratchet_impacts,
)
from .bracket_templates import apply_bracket_template, get_bracket_template, list_bracket_templates
from .bot_event_bus import BotEvent, event_bus
from .chrome_bridge import register_chrome_bridge_routes
from .config import load_settings
from .edge_actions import apply_edge_action
from .engine import TradingEngine
from .exchange_state import (
    adapter_status_for_exchange,
    capabilities_for_exchange,
    exchange_integration_payload,
    exchange_rows,
    platform_state_rows,
)
from .exchanges.bitunix_adapter import (
    BitunixConfigurationError,
    BitunixRequestError,
    BitunixRestClient,
    bitunix_kline_candles,
    bitunix_leverage_bounds,
    load_bitunix_credentials_from_env,
)
from .exchanges.ccxt_adapter import (
    CcxtExchangeAdapter,
    CcxtNotInstalledError,
    ccxt_credentials_from_env,
    ccxt_credentials_status,
    ccxt_live_execution_enabled,
    list_ccxt_exchange_ids,
    normalize_ccxt_exchange_id,
)
from .exchanges.order_planner import plan_bracket_execution
from .execution import PaperExchange, build_exit_orders
from .futures_risk import FuturesRiskConfig, FuturesTradeContext, assess_futures_trade
from .live_execution import (
    LIVE_ORDER_CONFIRMATION,
    bitunix_live_order_preview,
    live_execution_status_payload,
)
from .market_streaming import bitunix_ws_candles, normalize_bitunix_rest_candles
from .intake import SignalIntakeService
from .market_state import MarketStatePolicy, MarketStateSnapshot, evaluate_market_state
from .order_recorder import cooldown_state_key, save_order_with_runtime_state
from .protections import (
    ProtectionRule,
    ProtectionState,
    evaluate_protections,
    protection_rule_from_dict,
    protection_state_from_dict,
)
from .repository import SQLiteRepository
from .risk import AccountState, RiskConfig, RiskDecision, evaluate_signal
from .runtime_controls import (
    RUNTIME_CONFIG_KEY,
    runtime_config as _runtime_config,
    runtime_config_from_payload as _runtime_config_from_payload,
    runtime_control_summary as _runtime_control_summary,
    protection_state as _protection_state,
    save_protection_state as _save_protection_state,
)
from .security import (
    InMemoryWebhookReplayStore,
    WebhookReplayError,
    WebhookSignatureError,
    verify_webhook_signature,
)
from .signals import CryptoSignal, SignalValidationError, normalize_signal, normalize_symbol
from .scalper import (
    PriceBand,
    RebracketRuntimeState,
    ScalperBracketConfig,
    plan_rebracket,
    reentry_cooldown_remaining,
    scalper_signal_payload,
)
from .strategy_presets import apply_strategy_preset, get_strategy_preset, list_strategy_presets
from .text_signals import parse_text_signal
from .trade_decision import RuntimeControlDecision


OPERATOR_SESSION_COOKIE = "auto_crypto_operator_session"
SCALPER_STATE_PREFIX = "scalper:"


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
    app = FastAPI(title="Sentinel Chain", version="0.1.0")
    static_dir = Path(__file__).with_name("static")
    if static_dir.exists():
        app.mount("/ui/static", StaticFiles(directory=static_dir), name="ui-static")

    paper_exchange = exchange
    if paper_exchange is None:
        paper_exchange = PaperExchange()
    if account_state is None:
        account_state = AccountState(
            open_notional=paper_exchange.open_notional(),
            open_risk_amount=paper_exchange.open_risk_amount(),
        )
    engine = TradingEngine(
        exchange=paper_exchange,
        risk_config=risk_config or RiskConfig(),
        account_state=account_state,
    )
    secret = webhook_secret if webhook_secret is not None else os.getenv("AUTO_CRYPTO_WEBHOOK_SECRET")
    operator_session_token = secrets.token_urlsafe(32)
    replay_store = InMemoryWebhookReplayStore()
    guardian_memory: dict[str, Any] = {
        "drawings": {},
        "edge": {},
        "live_previews": {},
        "live_orders": {},
    }
    edge_stream_clients: set[WebSocket] = set()

    def runtime_pre_trade_decision(signal: CryptoSignal) -> RuntimeControlDecision:
        summary = _runtime_control_summary(signal, engine=engine, repository=repository)
        return RuntimeControlDecision(
            reason_codes=list(summary["reason_codes"]),
            approval_required=bool(summary["approval_required"]) and not signal.reduce_only,
            metadata=summary,
        )

    intake = SignalIntakeService(
        engine=engine,
        approvals=ApprovalQueue(),
        repository=repository,
        require_approval=require_approval,
        pre_trade_decision=runtime_pre_trade_decision,
    )

    def signal_preview_with_runtime_controls(signal: CryptoSignal) -> dict[str, Any]:
        preview = _signal_preview(signal, engine, require_approval=require_approval)
        summary = _runtime_control_summary(signal, engine=engine, repository=repository)
        _merge_runtime_controls(preview, summary)
        return preview

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "default_mode": "live",
            "orders": len(engine.exchange.orders),
            "halted": engine.halted,
            "halt_reason": engine.halt_reason,
        }

    @app.get("/", include_in_schema=False)
    @app.get("/ui", include_in_schema=False)
    def ui_index() -> FileResponse:
        index_path = static_dir / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail="operator UI is not installed")
        response = FileResponse(index_path)
        response.set_cookie(
            OPERATOR_SESSION_COOKIE,
            operator_session_token,
            httponly=True,
            max_age=12 * 60 * 60,
            path="/",
            samesite="strict",
            secure=False,
        )
        return response

    @app.get("/guardian/ui", include_in_schema=False)
    def guardian_ui_index() -> FileResponse:
        guardian_path = static_dir / "sentinel_guardian.html"
        if not guardian_path.exists():
            raise HTTPException(status_code=404, detail="guardian UI is not installed")
        response = FileResponse(guardian_path)
        response.set_cookie(
            OPERATOR_SESSION_COOKIE,
            operator_session_token,
            httponly=True,
            max_age=12 * 60 * 60,
            path="/",
            samesite="strict",
            secure=False,
        )
        return response

    @app.get("/ui/state")
    def ui_state() -> dict[str, Any]:
        orders_payload = _live_runtime_records(
            repository.list_orders() if repository else [order.to_dict() for order in engine.exchange.orders]
        )
        return {
            "health": {
                "status": "ok",
                "default_mode": "live",
                "orders": len(engine.exchange.orders),
                "halted": engine.halted,
                "halt_reason": engine.halt_reason,
            },
            "control": {"halted": engine.halted, "reason": engine.halt_reason},
            "execution": {
                "require_approval": require_approval,
                "submit_intent": "queue_for_approval" if require_approval else "live_route_required",
            },
            "risk": _risk_config_to_dict(engine.risk_config),
            "account": _account_state_to_dict(engine.account_state),
            "orders": orders_payload,
            "positions": engine.exchange.list_positions(),
            "signals": _live_runtime_records(repository.list_signals() if repository else []),
            "approvals": intake.list_approvals(),
            "audit": _live_runtime_records([event.to_dict() for event in repository.list_audit()] if repository else []),
            "active_exits": [],
            "runtime": _runtime_config(repository),
            "protections": _protection_state(repository).to_dict(),
            "live": live_execution_status_payload(),
            "guardian": {
                "drawings_persisted": repository is not None,
                "edge_streaming": True,
                "candle_websocket": "/guardian/ws/candles",
            },
        }

    @app.get("/control/status")
    def control_status() -> dict[str, Any]:
        return {"halted": engine.halted, "reason": engine.halt_reason}

    def verify_signed_request(request: Request, body: bytes) -> None:
        try:
            verify_webhook_signature(
                secret=secret,
                body=body,
                timestamp=request.headers.get("x-sentinel-chain-timestamp"),
                signature=request.headers.get("x-sentinel-chain-signature"),
                clock=webhook_clock,
                tolerance_seconds=webhook_tolerance_seconds,
                replay_store=replay_store,
            )
        except WebhookSignatureError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except WebhookReplayError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    def _same_origin_operator_request(request: Request) -> bool:
        host = (request.headers.get("host") or "").lower()
        for header in ("origin", "referer"):
            raw_value = request.headers.get(header)
            if not raw_value:
                continue
            return (urlparse(raw_value).netloc or "").lower() == host
        return True

    def verify_operator_session_request(request: Request) -> bool:
        session_cookie = request.cookies.get(OPERATOR_SESSION_COOKIE)
        if not session_cookie or not secrets.compare_digest(session_cookie, operator_session_token):
            return False
        if not _same_origin_operator_request(request):
            raise HTTPException(status_code=403, detail="operator session origin mismatch")
        return True

    async def verify_signed_operator_request(request: Request) -> None:
        if verify_operator_session_request(request):
            return
        if not secret:
            raise HTTPException(status_code=401, detail="operator session or webhook secret is required")
        body = await request.body()
        verify_signed_request(request, body)

    async def verify_private_exchange_request(request: Request) -> None:
        if verify_operator_session_request(request):
            return
        if not secret:
            raise HTTPException(status_code=401, detail="operator session is required for private exchange data")
        body = await request.body()
        verify_signed_request(request, body)

    def _ws_operator_session_valid(websocket: WebSocket) -> bool:
        session_cookie = websocket.cookies.get(OPERATOR_SESSION_COOKIE)
        if not session_cookie or not secrets.compare_digest(session_cookie, operator_session_token):
            return False
        host = (websocket.headers.get("host") or "").lower()
        origin = websocket.headers.get("origin")
        if origin and (urlparse(origin).netloc or "").lower() != host:
            return False
        return True

    def _guardian_key(prefix: str, *parts: str) -> str:
        cleaned = [str(part).strip().replace("/", "_").replace(" ", "_") for part in parts if str(part).strip()]
        return ":".join(["guardian", prefix, *cleaned])

    def _guardian_symbol(value: Any, default: str = "BTCUSDT") -> str:
        raw = str(value or default).strip().upper().replace("/", "").replace("-", "").replace("_", "")
        if not raw:
            raise ValueError("symbol is required")
        if len(raw) > 32 or not raw.replace(".", "").isalnum():
            raise ValueError(f"invalid guardian symbol: {value}")
        return raw

    def _runtime_get(key: str) -> dict[str, Any] | None:
        if repository:
            return repository.get_runtime_state(key)
        bucket = guardian_memory.setdefault("runtime", {})
        value = bucket.get(key)
        return dict(value) if isinstance(value, dict) else None

    def _runtime_set(key: str, value: dict[str, Any]) -> None:
        if repository:
            repository.set_runtime_state(key, value)
        else:
            guardian_memory.setdefault("runtime", {})[key] = value

    def _runtime_delete(key: str) -> None:
        if repository:
            repository.delete_runtime_state(key)
        else:
            guardian_memory.setdefault("runtime", {}).pop(key, None)

    def _runtime_list(prefix: str) -> dict[str, dict[str, Any]]:
        if repository:
            return repository.list_runtime_state(prefix)
        return {
            key: value
            for key, value in guardian_memory.setdefault("runtime", {}).items()
            if key.startswith(prefix) and isinstance(value, dict)
        }

    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _drawing_payload(symbol: str) -> dict[str, Any]:
        normalized = _guardian_symbol(symbol)
        key = _guardian_key("drawings", normalized)
        value = _runtime_get(key)
        if value is None:
            value = guardian_memory["drawings"].get(normalized) or {
                "symbol": normalized,
                "drawings": [],
                "updated_at": None,
                "count": 0,
            }
        return value

    def _validate_drawings(payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, list):
            raise ValueError("drawings must be a list")
        if len(payload) > 500:
            raise ValueError("drawings list is limited to 500 entries")
        drawings: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("each drawing must be an object")
            drawing_type = str(item.get("type") or "").strip()
            if drawing_type not in {"line", "trend", "hline", "horizontal", "zone", "risk_reward", "note"}:
                raise ValueError(f"unsupported drawing type: {drawing_type or 'missing'}")
            drawings.append({str(key): value for key, value in item.items()})
        return drawings

    def _edge_snapshot_payload(payload: dict[str, Any]) -> dict[str, Any]:
        symbol = _guardian_symbol(payload.get("symbol") or payload.get("ticker") or "EDGE")
        mode = str(payload.get("mode") or payload.get("kind") or "EDGE").strip().upper()[:32] or "EDGE"
        snapshot = {
            **payload,
            "symbol": symbol,
            "mode": mode,
            "received_at": _now_iso(),
        }
        return snapshot

    async def _broadcast_edge_snapshot(snapshot: dict[str, Any]) -> None:
        stale: list[WebSocket] = []
        for client in list(edge_stream_clients):
            try:
                await client.send_json({"event": "edge_snapshot", "snapshot": snapshot})
            except Exception:
                stale.append(client)
        for client in stale:
            edge_stream_clients.discard(client)

    def _live_preview_key(preview_id: str) -> str:
        return _guardian_key("live_preview", preview_id)

    def _live_order_key(client_id: str) -> str:
        return _guardian_key("live_order", client_id)

    def _normalize_live_signal_payload(payload: dict[str, Any], *, source: str) -> CryptoSignal:
        raw_signal = payload.get("signal") if isinstance(payload.get("signal"), dict) else payload
        if not isinstance(raw_signal, dict):
            raise SignalValidationError("signal payload must be an object")
        raw_signal = dict(raw_signal)
        raw_signal.setdefault("exchange", "bitunix")
        raw_signal.setdefault("market_type", "futures")
        return normalize_signal(raw_signal, source=source)

    def _live_preview_payload(signal: CryptoSignal) -> dict[str, Any]:
        engine.account_state.open_notional = engine.exchange.open_notional()
        engine.account_state.symbol_open_notional = engine.exchange.symbol_open_notional(signal.symbol)
        engine.account_state.open_risk_amount = engine.exchange.open_risk_amount()
        decision = evaluate_signal(signal, engine.risk_config, engine.account_state)
        runtime_summary = _runtime_control_summary(signal, engine=engine, repository=repository)
        runtime_blocked = bool(runtime_summary.get("reason_codes")) and not bool(runtime_summary.get("approval_required"))
        preview = bitunix_live_order_preview(
            signal,
            decision,
            engine_halted=engine.halted,
            runtime_blocked=runtime_blocked,
        )
        signal_preview = _signal_preview(signal, engine, require_approval=require_approval)
        _merge_runtime_controls(signal_preview, runtime_summary)
        return {
            "preview": preview.to_dict(),
            "risk": {
                "approved": decision.approved,
                "reason_codes": list(decision.reason_codes),
                "order_notional": str(decision.order_notional) if decision.order_notional is not None else None,
            },
            "runtime_controls": runtime_summary,
            "paper_preview": signal_preview,
            "signal": _signal_to_dict(signal),
            "raw_signal": dict(signal.raw_payload),
            "live_status": live_execution_status_payload(),
        }

    def _ccxt_preview_key(preview_id: str) -> str:
        return _guardian_key("ccxt_preview", preview_id)

    def _ccxt_order_key(exchange_id: str, client_id: str) -> str:
        return _guardian_key("ccxt_order", exchange_id, client_id)

    def _ccxt_exchange(exchange_id: str, *, authenticated: bool = False) -> CcxtExchangeAdapter:
        normalized = normalize_ccxt_exchange_id(exchange_id)
        credentials = ccxt_credentials_from_env(normalized) if authenticated else None
        return CcxtExchangeAdapter(normalized, credentials)

    def _normalize_ccxt_signal_payload(exchange_id: str, payload: dict[str, Any], *, source: str) -> CryptoSignal:
        raw_signal = payload.get("signal") if isinstance(payload.get("signal"), dict) else payload
        if not isinstance(raw_signal, dict):
            raise SignalValidationError("signal payload must be an object")
        raw_signal = dict(raw_signal)
        raw_signal.setdefault("exchange", normalize_ccxt_exchange_id(exchange_id))
        raw_signal.setdefault("market_type", payload.get("market_type") or "spot")
        return normalize_signal(raw_signal, source=source)

    def _ccxt_quantity_from_signal(signal: CryptoSignal, decision: RiskDecision) -> Decimal | None:
        if signal.base_amount is not None:
            return signal.base_amount
        notional = decision.order_notional or signal.quote_amount
        if notional is None or signal.price is None or signal.price <= 0:
            return None
        return (notional / signal.price).quantize(Decimal("0.00000001"))

    def _ccxt_order_preview_payload(exchange_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = normalize_ccxt_exchange_id(exchange_id)
        signal = _normalize_ccxt_signal_payload(normalized, payload, source=f"ccxt-{normalized}-preview")
        engine.account_state.open_notional = engine.exchange.open_notional()
        engine.account_state.symbol_open_notional = engine.exchange.symbol_open_notional(signal.symbol)
        engine.account_state.open_risk_amount = engine.exchange.open_risk_amount()
        decision = evaluate_signal(signal, engine.risk_config, engine.account_state)
        runtime_summary = _runtime_control_summary(signal, engine=engine, repository=repository)
        runtime_blocked = bool(runtime_summary.get("reason_codes")) and not bool(runtime_summary.get("approval_required"))
        reasons: list[str] = []
        warnings: list[str] = []
        if engine.halted:
            reasons.append("engine_halted")
        if runtime_blocked:
            reasons.append("runtime_controls_blocked")
        if not decision.approved:
            reasons.extend(str(code) for code in decision.reason_codes or ["risk_rejected"])
        credential_status = ccxt_credentials_status(normalized)
        if not credential_status["ccxt_configured"]:
            reasons.append("ccxt_credentials_missing")
        if not ccxt_live_execution_enabled(normalized):
            reasons.append("ccxt_live_execution_disabled")
        try:
            capabilities = _ccxt_exchange(normalized).capabilities()
            if not capabilities.create_order:
                reasons.append("ccxt_create_order_not_supported")
        except (CcxtNotInstalledError, ValueError) as exc:
            capabilities = None
            reasons.append(str(exc))
        quantity = _ccxt_quantity_from_signal(signal, decision)
        if quantity is None or quantity <= 0:
            reasons.append("positive_base_quantity_required")
        exit_orders = build_exit_orders(signal)
        if exit_orders:
            warnings.append("bracket_exits_require_exchange_specific_manager")
            reasons.append("bracket_exits_not_generic_ccxt_live_safe")
        order_type = str(payload.get("order_type") or payload.get("type") or ("limit" if signal.price is not None else "market")).lower()
        if order_type not in {"market", "limit"}:
            reasons.append("unsupported_ccxt_order_type")
        params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
        if signal.reduce_only:
            params = {**params, "reduceOnly": True}
        order_payload = {
            "exchange_id": normalized,
            "symbol": signal.symbol,
            "type": order_type,
            "side": signal.side,
            "amount": _decimal_to_plain(quantity) if quantity is not None else None,
            "price": _decimal_to_plain(signal.price) if signal.price is not None else None,
            "params": params,
        }
        return {
            "exchange_id": normalized,
            "preview": {
                "exchange_id": normalized,
                "live_order_safe": not reasons and quantity is not None and capabilities is not None,
                "reason_codes": list(dict.fromkeys(reasons)),
                "warnings": list(dict.fromkeys(warnings)),
                "order_payload": order_payload,
                "confirmation_phrase": LIVE_ORDER_CONFIRMATION,
            },
            "risk": {
                "approved": decision.approved,
                "reason_codes": list(decision.reason_codes),
                "order_notional": str(decision.order_notional) if decision.order_notional is not None else None,
            },
            "runtime_controls": runtime_summary,
            "credential_status": credential_status,
            "capabilities": capabilities.to_dict() if capabilities is not None else None,
            "signal": _signal_to_dict(signal),
        }

    @app.get("/guardian/drawings")
    def guardian_drawings(symbol: str = "BTCUSDT") -> dict[str, Any]:
        try:
            return _drawing_payload(symbol)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/guardian/drawings")
    async def save_guardian_drawings(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            symbol = _guardian_symbol(payload.get("symbol") or payload.get("ticker") or "BTCUSDT")
            drawings = _validate_drawings(payload.get("drawings"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        record = {
            "symbol": symbol,
            "drawings": drawings,
            "updated_at": _now_iso(),
            "count": len(drawings),
        }
        guardian_memory["drawings"][symbol] = record
        _runtime_set(_guardian_key("drawings", symbol), record)
        if repository:
            repository.record_audit("guardian.drawings_saved", {"symbol": symbol, "count": len(drawings)})
        return record

    @app.delete("/guardian/drawings")
    async def delete_guardian_drawings(request: Request, symbol: str = "BTCUSDT") -> dict[str, Any]:
        await verify_signed_operator_request(request)
        try:
            normalized = _guardian_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        guardian_memory["drawings"].pop(normalized, None)
        _runtime_delete(_guardian_key("drawings", normalized))
        if repository:
            repository.record_audit("guardian.drawings_deleted", {"symbol": normalized})
        return {"symbol": normalized, "drawings": [], "deleted": True}

    @app.get("/guardian/edge/latest")
    def guardian_edge_latest(symbol: str | None = None, mode: str | None = None) -> dict[str, Any]:
        prefix = _guardian_key("edge")
        snapshots = list(_runtime_list(prefix).values())
        if not snapshots:
            snapshots = list(guardian_memory["edge"].values())
        if symbol:
            try:
                normalized = _guardian_symbol(symbol)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            snapshots = [snap for snap in snapshots if snap.get("symbol") == normalized]
        if mode:
            wanted = mode.upper()
            snapshots = [snap for snap in snapshots if str(snap.get("mode") or "").upper() == wanted]
        snapshots.sort(key=lambda snap: str(snap.get("received_at") or snap.get("exported_at") or ""), reverse=True)
        return {"snapshots": snapshots, "count": len(snapshots), "stream": "/guardian/ws/edge"}

    @app.post("/guardian/edge/snapshot")
    async def guardian_edge_snapshot(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="edge snapshot must be an object")
        try:
            snapshot = _edge_snapshot_payload(payload)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        key = _guardian_key("edge", str(snapshot["symbol"]), str(snapshot["mode"]))
        guardian_memory["edge"][key] = snapshot
        _runtime_set(key, snapshot)
        if repository:
            repository.record_audit(
                "guardian.edge_snapshot",
                {
                    "symbol": snapshot.get("symbol"),
                    "mode": snapshot.get("mode"),
                    "risk_score": snapshot.get("risk_score"),
                    "regime": snapshot.get("regime"),
                },
            )
        await _broadcast_edge_snapshot(snapshot)
        return {"status": "accepted", "snapshot": snapshot, "clients": len(edge_stream_clients)}

    @app.websocket("/guardian/ws/edge")
    async def guardian_edge_stream(websocket: WebSocket) -> None:
        if not _ws_operator_session_valid(websocket):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        edge_stream_clients.add(websocket)
        try:
            await websocket.send_json({"event": "connected", "stream": "edge", "snapshots": guardian_edge_latest()})
            while True:
                try:
                    message = await asyncio.wait_for(websocket.receive_json(), timeout=30)
                except asyncio.TimeoutError:
                    await websocket.send_json({"event": "heartbeat", "stream": "edge", "time": _now_iso()})
                    continue
                if isinstance(message, dict) and message.get("op") == "publish" and isinstance(message.get("snapshot"), dict):
                    snapshot = _edge_snapshot_payload(message["snapshot"])
                    key = _guardian_key("edge", str(snapshot["symbol"]), str(snapshot["mode"]))
                    guardian_memory["edge"][key] = snapshot
                    _runtime_set(key, snapshot)
                    await _broadcast_edge_snapshot(snapshot)
        except WebSocketDisconnect:
            pass
        finally:
            edge_stream_clients.discard(websocket)

    @app.websocket("/guardian/ws/candles")
    async def guardian_candle_stream(
        websocket: WebSocket,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        transport: str = "rest_poll",
        price_type: str = "market",
        limit: int = 120,
    ) -> None:
        if not _ws_operator_session_valid(websocket):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            normalized_symbol = normalize_symbol(symbol).replace("/", "")
        except SignalValidationError as exc:
            await websocket.send_json({"event": "error", "detail": str(exc)})
            await websocket.close(code=1008)
            return
        interval = str(interval or "1m")
        limit = max(1, min(int(limit or 120), 500))
        await websocket.send_json(
            {
                "event": "connected",
                "stream": "candles",
                "source": "bitunix",
                "symbol": normalized_symbol,
                "interval": interval,
                "transport": transport,
            }
        )

        async def send_rest_snapshot() -> None:
            payload = await asyncio.to_thread(
                BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_klines,
                normalized_symbol,
                interval,
                limit=limit,
            )
            candles = normalize_bitunix_rest_candles(bitunix_kline_candles(payload))
            await websocket.send_json(
                {
                    "event": "snapshot",
                    "source": "bitunix_rest",
                    "symbol": normalized_symbol,
                    "interval": interval,
                    "candles": candles,
                }
            )

        try:
            await send_rest_snapshot()
        except Exception as exc:
            await websocket.send_json({"event": "warning", "source": "bitunix_rest", "detail": str(exc)})

        try:
            if str(transport).lower() in {"bitunix_ws", "ws", "websocket"}:
                try:
                    async for event in bitunix_ws_candles(
                        symbol=normalized_symbol,
                        interval=interval,
                        price_type=price_type,
                    ):
                        await websocket.send_json(event)
                except Exception as exc:
                    await websocket.send_json(
                        {
                            "event": "warning",
                            "source": "bitunix_ws",
                            "detail": f"upstream websocket unavailable; falling back to REST polling: {exc}",
                        }
                    )
            poll_seconds = max(2, int(os.getenv("AUTO_CRYPTO_CANDLE_STREAM_POLL_SECONDS", "5") or "5"))
            while True:
                await asyncio.sleep(poll_seconds)
                try:
                    await send_rest_snapshot()
                except Exception as exc:
                    await websocket.send_json({"event": "warning", "source": "bitunix_rest", "detail": str(exc)})
        except WebSocketDisconnect:
            return

    @app.get("/guardian/live/status")
    def guardian_live_status() -> dict[str, Any]:
        return live_execution_status_payload()

    @app.post("/guardian/live/preview")
    async def guardian_live_preview(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            signal = _normalize_live_signal_payload(payload, source="guardian-live-preview")
            preview = _live_preview_payload(signal)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        preview_id = secrets.token_urlsafe(12)
        record = {
            "preview_id": preview_id,
            "created_at": _now_iso(),
            "used": False,
            **preview,
        }
        guardian_memory["live_previews"][preview_id] = record
        _runtime_set(_live_preview_key(preview_id), record)
        if repository:
            repository.record_audit(
                "guardian.live_preview",
                {
                    "preview_id": preview_id,
                    "signal_id": preview["signal"].get("signal_id"),
                    "symbol": preview["signal"].get("symbol"),
                    "safe": preview["preview"].get("live_order_safe"),
                    "reasons": preview["preview"].get("reason_codes"),
                },
            )
        return record

    @app.post("/guardian/live/submit")
    async def guardian_live_submit(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        preview_id = str(payload.get("preview_id") or "").strip()
        confirmation = str(payload.get("confirmation") or payload.get("confirm") or "").strip()
        if confirmation != LIVE_ORDER_CONFIRMATION:
            raise HTTPException(status_code=400, detail=f"confirmation must equal {LIVE_ORDER_CONFIRMATION!r}")
        if not preview_id:
            raise HTTPException(status_code=400, detail="preview_id is required")
        record = _runtime_get(_live_preview_key(preview_id)) or guardian_memory["live_previews"].get(preview_id)
        if not record:
            raise HTTPException(status_code=404, detail="live preview ticket not found")
        if record.get("used"):
            raise HTTPException(status_code=409, detail="live preview ticket has already been used")
        try:
            signal = normalize_signal(dict(record.get("raw_signal") or record["signal"]), source="guardian-live-submit")
            fresh = _live_preview_payload(signal)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not fresh["preview"].get("live_order_safe"):
            raise HTTPException(status_code=409, detail={"message": "live order is not safe to submit", "preview": fresh["preview"]})
        order_payload = fresh["preview"].get("order_payload")
        if not isinstance(order_payload, dict):
            raise HTTPException(status_code=409, detail="live order payload is missing")
        try:
            bitunix_client = BitunixRestClient(credentials=load_bitunix_credentials_from_env())
            leverage_setting = fresh["preview"].get("leverage_setting")
            leverage_response = None
            if isinstance(leverage_setting, dict) and order_payload.get("tradeSide") == "OPEN":
                leverage_response = bitunix_client.change_futures_leverage(
                    str(leverage_setting["symbol"]),
                    int(leverage_setting["leverage"]),
                    str(leverage_setting.get("marginCoin") or "USDT"),
                )
            response = bitunix_client.place_futures_order(order_payload)
        except BitunixConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        client_id = str(order_payload.get("clientId") or preview_id)
        submitted = {
            "status": "submitted",
            "preview_id": preview_id,
            "submitted_at": _now_iso(),
            "signal": fresh["signal"],
            "leverage_setting": fresh["preview"].get("leverage_setting"),
            "leverage_response": leverage_response,
            "order_payload": order_payload,
            "exchange_response": response,
        }
        record["used"] = True
        record["used_at"] = submitted["submitted_at"]
        _runtime_set(_live_preview_key(preview_id), record)
        guardian_memory["live_orders"][client_id] = submitted
        _runtime_set(_live_order_key(client_id), submitted)
        if repository:
            repository.record_audit(
                "guardian.live_order_submitted",
                {
                    "preview_id": preview_id,
                    "client_id": client_id,
                    "symbol": order_payload.get("symbol"),
                    "side": order_payload.get("side"),
                    "leverage": (fresh["preview"].get("leverage_setting") or {}).get("leverage")
                    if isinstance(fresh["preview"].get("leverage_setting"), dict)
                    else None,
                    "order_type": order_payload.get("orderType"),
                    "exchange_response": response,
                },
            )
        return submitted

    @app.post("/exchanges/bitunix/futures/order/preview")
    async def bitunix_futures_order_preview(request: Request) -> dict[str, Any]:
        return await guardian_live_preview(request)

    @app.post("/exchanges/bitunix/futures/order")
    async def bitunix_futures_order_submit(request: Request) -> dict[str, Any]:
        return await guardian_live_submit(request)

    @app.post("/exchanges/bitunix/futures/orders/cancel")
    async def bitunix_futures_order_cancel(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        confirmation = str(payload.get("confirmation") or payload.get("confirm") or "").strip()
        if confirmation != LIVE_ORDER_CONFIRMATION:
            raise HTTPException(status_code=400, detail=f"confirmation must equal {LIVE_ORDER_CONFIRMATION!r}")
        if not live_execution_status_payload()["bitunix"]["live_execution_enabled"]:
            raise HTTPException(status_code=409, detail="Bitunix live execution is not enabled")
        try:
            symbol = _guardian_symbol(payload.get("symbol") or payload.get("ticker") or "")
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        order_list = payload.get("orderList") or payload.get("orders")
        if not isinstance(order_list, list) or not order_list:
            order_id = payload.get("orderId") or payload.get("order_id")
            client_id = payload.get("clientId") or payload.get("client_id")
            if not order_id and not client_id:
                raise HTTPException(status_code=400, detail="orderId or clientId is required")
            item: dict[str, Any] = {}
            if order_id:
                item["orderId"] = str(order_id)
            if client_id:
                item["clientId"] = str(client_id)
            order_list = [item]
        try:
            response = BitunixRestClient(credentials=load_bitunix_credentials_from_env()).cancel_futures_orders(
                symbol,
                order_list,
            )
        except BitunixConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        if repository:
            repository.record_audit("guardian.live_order_cancel", {"symbol": symbol, "orders": order_list, "response": response})
        return {"status": "submitted", "symbol": symbol, "orders": order_list, "exchange_response": response}

    @app.post("/bus/events")
    async def publish_bus_event(event: BotEvent, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        accepted = event_bus.publish(event)
        result: dict[str, Any] | None = None
        if event.event_type == "edge.action":
            result = apply_edge_action(event=accepted, engine=engine, repository=repository)
        return {
            "status": "accepted",
            "event": accepted.model_dump(mode="json"),
            "result": result,
        }

    @app.get("/bus/events")
    def recent_bus_events(limit: int = 100, event_type: str | None = None) -> dict[str, Any]:
        return {"events": event_bus.recent(limit=limit, event_type=event_type)}

    register_chrome_bridge_routes(app)

    @app.post("/bus/edge-actions")
    async def publish_edge_action(payload: dict[str, Any], request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        event = event_bus.publish(
            BotEvent(
                event_type="edge.action",
                source_bot="sentinel-edge",
                correlation_id=str(payload.get("idempotency_key") or ""),
                dedupe_key=str(payload.get("idempotency_key") or ""),
                target_bots=["sentinel-chain"],
                payload={"contract_version": "edge.action.v1", **payload},
            )
        )
        result = apply_edge_action(event=event, engine=engine, repository=repository)
        return {"status": "accepted", "event": event.model_dump(mode="json"), "result": result}

    @app.post("/control/halt")
    async def halt(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        reason = str(payload.get("reason") or "manual halt")
        engine.halt(reason)
        if repository:
            repository.record_audit("trading.halted", {"reason": reason})
        return {"halted": True, "reason": reason}

    @app.post("/control/resume")
    async def resume(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        engine.resume()
        if repository:
            repository.record_audit("trading.resumed", {})
        return {"halted": False, "reason": ""}

    @app.get("/runtime/config")
    def runtime_config() -> dict[str, Any]:
        return {"config": _runtime_config(repository)}

    @app.post("/runtime/config")
    async def update_runtime_config(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            config = _runtime_config_from_payload(payload, existing=_runtime_config(repository))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if repository:
            repository.set_runtime_state(RUNTIME_CONFIG_KEY, config)
            repository.record_audit("runtime.config_updated", config)
        return {"config": config}

    @app.get("/protections")
    def protections() -> dict[str, Any]:
        state = _protection_state(repository)
        return {"state": state.to_dict(), "active_rules": [rule.to_dict() for rule in state.active_rules()]}

    @app.post("/protections/rules")
    async def set_protection_rule(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        payload.setdefault("created_at", datetime.now(timezone.utc).isoformat())
        try:
            rule = protection_rule_from_dict(payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        state = _protection_state(repository).with_rule(rule)
        if repository:
            _save_protection_state(repository, state)
            repository.record_audit("protection.rule_set", {"rule": rule.to_dict()})
        return {"rule": rule.to_dict(), "state": state.to_dict()}

    @app.delete("/protections/rules/{rule_id}")
    async def delete_protection_rule(rule_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        state = _protection_state(repository).without_rule(rule_id)
        if repository:
            _save_protection_state(repository, state)
            repository.record_audit("protection.rule_deleted", {"rule_id": rule_id})
        return {"state": state.to_dict()}

    @app.post("/protections/preview")
    async def protection_preview(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            signal_payload = payload.get("signal") if isinstance(payload.get("signal"), dict) else payload
            signal = normalize_signal(signal_payload, source="operator-protection-preview")
            state = (
                protection_state_from_dict(payload.get("protections"))
                if isinstance(payload.get("protections"), dict)
                else _protection_state(repository)
            )
            decision = evaluate_protections(signal, state)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"signal": _signal_to_dict(signal), "protections": decision.to_dict()}

    @app.post("/webhooks/tradingview")
    async def tradingview_webhook(request: Request) -> dict[str, Any]:
        body = await request.body()
        verify_signed_request(request, body)

        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="tradingview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return intake.handle(signal)

    @app.post("/webhooks/text-alert")
    async def text_alert_webhook(request: Request) -> dict[str, Any]:
        body = await request.body()
        verify_signed_request(request, body)
        payload = await request.json()
        try:
            signal = parse_text_signal(str(payload.get("message") or ""), source="text-alert")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return intake.handle(signal)

    @app.get("/orders")
    def orders() -> dict[str, Any]:
        if repository:
            return {"orders": repository.list_orders()}
        return {"orders": [order.to_dict() for order in engine.exchange.orders]}

    @app.get("/positions")
    def positions() -> dict[str, Any]:
        return {"positions": engine.exchange.list_positions()}

    @app.get("/exchanges")
    def exchanges() -> dict[str, Any]:
        try:
            ccxt_exchange_ids = list_ccxt_exchange_ids()
        except CcxtNotInstalledError:
            return {"ccxt_available": False, "exchanges": exchange_rows(())}

        return {"ccxt_available": True, "exchanges": exchange_rows(ccxt_exchange_ids)}

    @app.get("/exchanges/platforms")
    def exchange_platforms() -> dict[str, Any]:
        try:
            ccxt_exchange_ids = set(list_ccxt_exchange_ids())
        except CcxtNotInstalledError:
            return {"ccxt_available": False, "platforms": platform_state_rows(None)}
        return {"ccxt_available": True, "platforms": platform_state_rows(ccxt_exchange_ids)}

    @app.get("/exchanges/ccxt/catalog")
    def ccxt_catalog() -> dict[str, Any]:
        try:
            exchange_ids = list_ccxt_exchange_ids()
        except CcxtNotInstalledError as exc:
            return {"ccxt_available": False, "error": str(exc), "exchanges": []}
        return {
            "ccxt_available": True,
            "count": len(exchange_ids),
            "exchanges": [
                {
                    "exchange_id": exchange_id,
                    "credential_status": ccxt_credentials_status(exchange_id),
                }
                for exchange_id in exchange_ids
            ],
        }

    @app.get("/exchanges/{exchange_id}/ccxt/status")
    def ccxt_exchange_status(exchange_id: str) -> dict[str, Any]:
        normalized = normalize_ccxt_exchange_id(exchange_id)
        try:
            capabilities = _ccxt_exchange(normalized).capabilities().to_dict()
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "exchange_id": normalized,
            "driver": "ccxt",
            "credential_status": ccxt_credentials_status(normalized),
            "capabilities": capabilities,
            "live_execution_model": {
                "default": "locked",
                "requires_operator_session": True,
                "requires_preview_ticket": True,
                "requires_manual_confirmation": LIVE_ORDER_CONFIRMATION,
                "requires_global_readiness": True,
            },
        }

    @app.get("/exchanges/{exchange_id}/ccxt/ticker")
    async def ccxt_ticker(exchange_id: str, symbol: str) -> dict[str, Any]:
        try:
            payload = await asyncio.to_thread(_ccxt_exchange(exchange_id).fetch_ticker, symbol)
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - third-party exchange errors vary by ccxt version.
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"exchange_id": normalize_ccxt_exchange_id(exchange_id), "ticker": payload}

    @app.get("/exchanges/{exchange_id}/ccxt/tickers")
    async def ccxt_tickers(exchange_id: str, symbols: str | None = None) -> dict[str, Any]:
        wanted = [item.strip() for item in str(symbols or "").split(",") if item.strip()] or None
        try:
            payload = await asyncio.to_thread(_ccxt_exchange(exchange_id).fetch_tickers, wanted)
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - third-party exchange errors vary by ccxt version.
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"exchange_id": normalize_ccxt_exchange_id(exchange_id), "tickers": payload}

    @app.get("/exchanges/{exchange_id}/ccxt/balance")
    async def ccxt_balance(exchange_id: str, request: Request) -> dict[str, Any]:
        await verify_private_exchange_request(request)
        status = ccxt_credentials_status(exchange_id)
        if not status["ccxt_configured"]:
            raise HTTPException(status_code=400, detail=f"CCXT credentials are not configured for {normalize_ccxt_exchange_id(exchange_id)}")
        try:
            payload = await asyncio.to_thread(_ccxt_exchange(exchange_id, authenticated=True).fetch_balance)
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - third-party exchange errors vary by ccxt version.
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"exchange_id": normalize_ccxt_exchange_id(exchange_id), "balance": payload}

    @app.post("/exchanges/{exchange_id}/ccxt/order/preview")
    async def ccxt_order_preview(exchange_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="order preview payload must be an object")
        try:
            preview = _ccxt_order_preview_payload(exchange_id, payload)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        preview_id = secrets.token_urlsafe(12)
        record = {
            "preview_id": preview_id,
            "created_at": _now_iso(),
            "used": False,
            **preview,
        }
        guardian_memory.setdefault("ccxt_previews", {})[preview_id] = record
        _runtime_set(_ccxt_preview_key(preview_id), record)
        if repository:
            repository.record_audit(
                "ccxt.live_preview",
                {
                    "preview_id": preview_id,
                    "exchange_id": preview["exchange_id"],
                    "symbol": preview["signal"].get("symbol"),
                    "safe": preview["preview"].get("live_order_safe"),
                    "reasons": preview["preview"].get("reason_codes"),
                },
            )
        return record

    @app.post("/exchanges/{exchange_id}/ccxt/order")
    async def ccxt_order_submit(exchange_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        preview_id = str(payload.get("preview_id") or "").strip()
        confirmation = str(payload.get("confirmation") or payload.get("confirm") or "").strip()
        if confirmation != LIVE_ORDER_CONFIRMATION:
            raise HTTPException(status_code=400, detail=f"confirmation must equal {LIVE_ORDER_CONFIRMATION!r}")
        if not preview_id:
            raise HTTPException(status_code=400, detail="preview_id is required")
        record = _runtime_get(_ccxt_preview_key(preview_id)) or guardian_memory.setdefault("ccxt_previews", {}).get(preview_id)
        if not record:
            raise HTTPException(status_code=404, detail="CCXT live preview ticket not found")
        if record.get("used"):
            raise HTTPException(status_code=409, detail="CCXT live preview ticket has already been used")
        normalized = normalize_ccxt_exchange_id(exchange_id)
        if record.get("exchange_id") != normalized:
            raise HTTPException(status_code=409, detail="preview exchange does not match submit exchange")
        try:
            fresh = _ccxt_order_preview_payload(normalized, {"signal": record["signal"], "params": record["preview"]["order_payload"].get("params") or {}})
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if not fresh["preview"].get("live_order_safe"):
            raise HTTPException(status_code=409, detail={"message": "CCXT live order is not safe to submit", "preview": fresh["preview"]})
        order_payload = fresh["preview"].get("order_payload")
        if not isinstance(order_payload, dict):
            raise HTTPException(status_code=409, detail="CCXT order payload is missing")
        try:
            response = await asyncio.to_thread(
                _ccxt_exchange(normalized, authenticated=True).create_order,
                order_payload["symbol"],
                order_payload["type"],
                order_payload["side"],
                order_payload["amount"],
                order_payload.get("price"),
                order_payload.get("params") or {},
            )
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - third-party exchange errors vary by ccxt version.
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        submitted = {
            "status": "submitted",
            "preview_id": preview_id,
            "exchange_id": normalized,
            "submitted_at": _now_iso(),
            "signal": fresh["signal"],
            "order_payload": order_payload,
            "exchange_response": response,
        }
        record["used"] = True
        record["used_at"] = submitted["submitted_at"]
        _runtime_set(_ccxt_preview_key(preview_id), record)
        client_id = str(response.get("clientOrderId") or response.get("clientId") or response.get("id") or preview_id)
        guardian_memory.setdefault("ccxt_orders", {})[client_id] = submitted
        _runtime_set(_ccxt_order_key(normalized, client_id), submitted)
        if repository:
            repository.record_audit(
                "ccxt.live_order_submitted",
                {
                    "preview_id": preview_id,
                    "exchange_id": normalized,
                    "symbol": order_payload.get("symbol"),
                    "side": order_payload.get("side"),
                    "order_type": order_payload.get("type"),
                    "exchange_response": response,
                },
            )
        return submitted

    @app.post("/exchanges/{exchange_id}/ccxt/order/cancel")
    async def ccxt_order_cancel(exchange_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        confirmation = str(payload.get("confirmation") or payload.get("confirm") or "").strip()
        if confirmation != LIVE_ORDER_CONFIRMATION:
            raise HTTPException(status_code=400, detail=f"confirmation must equal {LIVE_ORDER_CONFIRMATION!r}")
        normalized = normalize_ccxt_exchange_id(exchange_id)
        if not ccxt_live_execution_enabled(normalized):
            raise HTTPException(status_code=409, detail=f"CCXT live execution is not enabled for {normalized}")
        if not ccxt_credentials_status(normalized)["ccxt_configured"]:
            raise HTTPException(status_code=400, detail=f"CCXT credentials are not configured for {normalized}")
        order_id = str(payload.get("order_id") or payload.get("orderId") or "").strip()
        symbol = str(payload.get("symbol") or "").strip() or None
        params = payload.get("params") if isinstance(payload.get("params"), dict) else {}
        if not order_id:
            raise HTTPException(status_code=400, detail="order_id is required")
        try:
            response = await asyncio.to_thread(_ccxt_exchange(normalized, authenticated=True).cancel_order, order_id, symbol, params)
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:  # pragma: no cover - third-party exchange errors vary by ccxt version.
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        if repository:
            repository.record_audit("ccxt.live_order_cancel", {"exchange_id": normalized, "order_id": order_id, "symbol": symbol, "response": response})
        return {"status": "submitted", "exchange_id": normalized, "order_id": order_id, "symbol": symbol, "exchange_response": response}

    @app.get("/exchanges/{exchange_id}/capabilities")
    def exchange_capabilities(exchange_id: str) -> dict[str, Any]:
        try:
            capabilities = capabilities_for_exchange(exchange_id)
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"capabilities": capabilities.to_dict()}

    @app.get("/exchanges/{exchange_id}/adapter-status")
    def exchange_adapter_status(exchange_id: str) -> dict[str, Any]:
        try:
            status = adapter_status_for_exchange(
                exchange_id,
                engine.exchange,
                equity=engine.account_state.equity,
            )
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {"adapter": status.to_dict()}

    @app.get("/exchanges/{exchange_id}/integration")
    def exchange_integration(exchange_id: str) -> dict[str, Any]:
        try:
            ccxt_exchange_ids = set(list_ccxt_exchange_ids())
        except CcxtNotInstalledError:
            ccxt_exchange_ids = None
        try:
            return exchange_integration_payload(exchange_id, ccxt_exchange_ids)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @app.get("/exchanges/bitunix/futures/tickers")
    def bitunix_futures_tickers(symbols: str | None = None) -> dict[str, Any]:
        try:
            return BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_tickers(symbols)
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/exchanges/bitunix/futures/trading-pairs")
    def bitunix_futures_trading_pairs(symbols: str | None = None) -> dict[str, Any]:
        try:
            payload = BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_trading_pairs(symbols)
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        rows = payload.get("data") if isinstance(payload, dict) else []
        if isinstance(rows, dict):
            rows = [rows]
        wanted = [str(item.get("symbol") or "").replace("/", "").upper() for item in rows if isinstance(item, dict)]
        if symbols:
            wanted = [part.strip().replace("/", "").upper() for part in symbols.split(",") if part.strip()]
        return {
            "source": "bitunix",
            "raw": payload,
            "leverage_bounds": {
                symbol: bitunix_leverage_bounds(payload, symbol)
                for symbol in wanted
                if bitunix_leverage_bounds(payload, symbol) is not None
            },
        }

    @app.get("/exchanges/bitunix/futures/klines")
    def bitunix_futures_klines(
        symbol: str,
        interval: str,
        start_time: int | None = None,
        end_time: int | None = None,
        limit: int | None = None,
        price_type: str | None = None,
    ) -> dict[str, Any]:
        try:
            payload = BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_klines(
                symbol,
                interval,
                start_time=start_time,
                end_time=end_time,
                limit=limit,
                price_type=price_type,
            )
            return {"source": "bitunix", "raw": payload, "candles": bitunix_kline_candles(payload)}
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/exchanges/bitunix/futures/account")
    async def bitunix_futures_account(request: Request, margin_coin: str = "USDT") -> dict[str, Any]:
        await verify_private_exchange_request(request)
        try:
            return BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_account(margin_coin)
        except BitunixConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    @app.get("/exchanges/bitunix/futures/leverage")
    async def bitunix_futures_leverage(request: Request, symbol: str, margin_coin: str = "USDT") -> dict[str, Any]:
        await verify_private_exchange_request(request)
        try:
            return BitunixRestClient(credentials=load_bitunix_credentials_from_env()).get_futures_leverage_margin_mode(
                symbol,
                margin_coin,
            )
        except BitunixConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except BitunixRequestError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    async def _market_price_payload(request: Request) -> tuple[str, Decimal, bool]:
        payload = await request.json()
        try:
            symbol = normalize_symbol(payload.get("symbol"))
            price = _positive_decimal(payload.get("price"))
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        include_order_metadata = str(payload.get("include_order_metadata") or "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return symbol, price, include_order_metadata

    @app.post("/market/price/preview")
    async def market_price_preview(request: Request) -> dict[str, Any]:
        symbol, price, _include_order_metadata = await _market_price_payload(request)
        live_lots = deepcopy(engine.exchange.lots)
        preview_exchange = engine.exchange.preview_price_exchange(symbol, price)
        return {
            "symbol": symbol,
            "price": str(price),
            "would_trigger": engine.exchange.preview_price(symbol, price),
            "trailing_ratchets": trailing_ratchet_impacts(live_lots, preview_exchange.lots),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, mark_price=price),
            "preview_active_exits": _active_exits_to_dict(preview_exchange.lots, mark_price=price),
            "positions": engine.exchange.list_positions(),
            "preview_positions": preview_exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/scalper/rebracket/preview")
    async def scalper_rebracket_preview(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            _symbol, decision, suggested_signal, _state_payload = _scalper_rebracket_payload(
                payload,
                repository=None,
            )
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {
            "decision": decision.to_dict(),
            "suggested_signal": suggested_signal,
            "source": "sentinel_pulse_scalper",
        }

    @app.get("/scalper/state/{symbol:path}")
    def scalper_state(symbol: str) -> dict[str, Any]:
        try:
            normalized_symbol = normalize_symbol(symbol)
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        state = _scalper_state(repository, normalized_symbol)
        if state is None:
            return {"symbol": normalized_symbol, "configured": False}
        return {"symbol": normalized_symbol, "configured": True, **state}

    @app.post("/scalper/rebracket/apply")
    async def scalper_rebracket_apply(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            symbol, decision, suggested_signal, state_payload = _scalper_rebracket_payload(
                payload,
                repository=repository,
            )
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if decision.should_rebracket and decision.new_band is not None and repository:
            repository.set_runtime_state(_scalper_state_key(symbol), state_payload)
            repository.record_audit(
                "scalper.rebracket_applied",
                {"symbol": symbol, "decision": decision.to_dict()},
            )
        return {
            "decision": decision.to_dict(),
            "suggested_signal": suggested_signal,
            "state": state_payload if decision.should_rebracket else _scalper_state(repository, symbol),
            "mutates_exchange_orders": False,
        }

    @app.post("/scalper/rebracket/revert")
    async def scalper_rebracket_revert(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            symbol = normalize_symbol(payload.get("symbol") or payload.get("ticker") or payload.get("pair"))
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        state = _scalper_state(repository, symbol)
        if state is None:
            raise HTTPException(status_code=404, detail="scalper state not found")
        previous_band = state.get("previous_band")
        current_band = state.get("band")
        if not isinstance(previous_band, dict) or not isinstance(current_band, dict):
            raise HTTPException(status_code=409, detail="previous scalper band is not available")
        reverted = {
            **state,
            "band": previous_band,
            "previous_band": current_band,
            "reverted_at": datetime.now(timezone.utc).isoformat(),
        }
        if repository:
            repository.set_runtime_state(_scalper_state_key(symbol), reverted)
            repository.record_audit("scalper.rebracket_reverted", {"symbol": symbol, "band": previous_band})
        return {"symbol": symbol, "band": previous_band, "state": reverted, "mutates_exchange_orders": False}

    @app.post("/futures/risk/preview")
    async def futures_risk_preview(request: Request) -> dict[str, Any]:
        payload = await request.json()
        config_payload = payload.get("config") if isinstance(payload.get("config"), dict) else {}
        defaults = FuturesRiskConfig()

        def config_value(*names: str) -> Any:
            for name in names:
                if name in config_payload:
                    return config_payload[name]
                if name in payload:
                    return payload[name]
            return None

        try:
            symbol = normalize_symbol(payload.get("symbol") or payload.get("ticker") or payload.get("pair"))
            context = FuturesTradeContext(
                symbol=symbol,
                side=str(payload.get("side") or ""),
                entry_price=_positive_decimal(payload.get("entry_price") or payload.get("price")),
                stop_loss_price=_positive_decimal(payload.get("stop_loss_price") or payload.get("stop_price")),
                notional=_positive_decimal(payload.get("notional") or payload.get("quote_amount")),
                leverage=_positive_decimal(payload.get("leverage")),
                maintenance_margin_pct=_decimal(
                    payload.get("maintenance_margin_pct"),
                    default=Decimal("0.5"),
                ),
                funding_rate_bps=_decimal(payload.get("funding_rate_bps"), default=Decimal("0")),
                minutes_to_funding=_optional_int(payload.get("minutes_to_funding")),
            )
            config = FuturesRiskConfig(
                max_leverage=_decimal(config_value("max_leverage"), default=defaults.max_leverage),
                min_liquidation_buffer_pct=_decimal(
                    config_value("min_liquidation_buffer_pct"),
                    default=defaults.min_liquidation_buffer_pct,
                ),
                max_adverse_funding_rate_bps=_decimal(
                    config_value("max_adverse_funding_rate_bps", "max_funding_rate_bps"),
                    default=defaults.max_adverse_funding_rate_bps,
                ),
                funding_window_minutes=_optional_int(config_value("funding_window_minutes"))
                or defaults.funding_window_minutes,
            )
            result = assess_futures_trade(context, config)
        except (SignalValidationError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return {"symbol": symbol, **result.to_dict()}

    @app.post("/market/state/preview")
    async def market_state_preview(request: Request) -> dict[str, Any]:
        payload = await request.json()
        policy_payload = payload.get("policy") if isinstance(payload.get("policy"), dict) else {}
        defaults = MarketStatePolicy()

        def policy_value(*names: str) -> Any:
            for name in names:
                if name in policy_payload:
                    return policy_payload[name]
                if name in payload:
                    return payload[name]
            return None

        try:
            snapshot = MarketStateSnapshot(
                volatility_pct=_decimal(payload.get("volatility_pct"), default=Decimal("0")),
                spread_bps=_decimal(payload.get("spread_bps"), default=Decimal("0")),
                depth_notional=_decimal(payload.get("depth_notional"), default=Decimal("0")),
                funding_rate_bps=_decimal(payload.get("funding_rate_bps"), default=Decimal("0")),
                minutes_to_funding=_optional_int(payload.get("minutes_to_funding")),
                liquidation_buffer_pct=_optional_positive_decimal(payload.get("liquidation_buffer_pct")),
                data_stale_seconds=_optional_int(payload.get("data_stale_seconds")) or 0,
                exchange_status=str(payload.get("exchange_status") or "ok"),
            )
            policy = MarketStatePolicy(
                max_normal_volatility_pct=_decimal(
                    policy_value("max_normal_volatility_pct"),
                    default=defaults.max_normal_volatility_pct,
                ),
                max_spread_bps=_decimal(policy_value("max_spread_bps"), default=defaults.max_spread_bps),
                min_depth_notional=_decimal(
                    policy_value("min_depth_notional"),
                    default=defaults.min_depth_notional,
                ),
                funding_window_minutes=_optional_int(policy_value("funding_window_minutes"))
                or defaults.funding_window_minutes,
                min_liquidation_buffer_pct=_decimal(
                    policy_value("min_liquidation_buffer_pct"),
                    default=defaults.min_liquidation_buffer_pct,
                ),
                data_stale_after_seconds=_optional_int(policy_value("data_stale_after_seconds"))
                or defaults.data_stale_after_seconds,
            )
            state = evaluate_market_state(snapshot, policy)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        return state.to_dict()

    @app.post("/market/price")
    async def market_price(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        symbol, price, include_order_metadata = await _market_price_payload(request)
        order_offset = len(engine.exchange.orders)
        before_lots = deepcopy(engine.exchange.lots)
        update = engine.mark_price(symbol, price)
        triggered = (
            _triggered_with_order_metadata(update.triggered, engine.exchange.orders[order_offset:])
            if include_order_metadata
            else update.triggered
        )
        if repository:
            for order in engine.exchange.orders[order_offset:]:
                save_order_with_runtime_state(repository, order)
            if update.triggered:
                repository.record_audit(
                    "exit.triggered",
                    {"symbol": symbol, "price": str(price), "triggered": triggered},
                )
        return {
            "symbol": symbol,
            "price": str(price),
            "triggered": triggered,
            "trailing_ratchets": trailing_ratchet_impacts(before_lots, engine.exchange.lots),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, mark_price=price),
            "realized_pnl_delta": str(update.realized_pnl_delta),
            "daily_pnl": str(update.daily_pnl),
            "consecutive_losses": update.consecutive_losses,
            "open_notional": str(update.open_notional),
            "positions": engine.exchange.list_positions(),
        }

    @app.get("/brackets")
    def list_brackets() -> dict[str, Any]:
        return {"brackets": _active_brackets_to_dict(engine.exchange.lots)}

    @app.get("/brackets/risk-summary")
    def bracket_risk_summary() -> dict[str, Any]:
        return {"summary": _bracket_risk_summary(engine.exchange.lots)}

    @app.get("/brackets/health")
    def bracket_health() -> dict[str, Any]:
        return {"health": _bracket_health(engine.exchange.lots)}

    @app.get("/brackets/coverage")
    def bracket_coverage() -> dict[str, Any]:
        active_lots = [
            lot
            for lot in engine.exchange.lots
            if lot.remaining_quantity > 0 and lot.exit_orders
        ]
        return {
            "bracket_count": len(active_lots),
            "coverage": [_bracket_coverage_to_dict(lot) for lot in active_lots],
        }

    @app.get("/brackets/oca-groups")
    def bracket_oca_groups() -> dict[str, Any]:
        return _bracket_oca_groups(engine.exchange.lots)

    @app.get("/brackets/{signal_id}")
    def bracket_status(signal_id: str) -> dict[str, Any]:
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        exits = _active_exits_to_dict(lots, signal_id=signal_id)
        if not exits:
            raise HTTPException(status_code=404, detail="active bracket not found")
        return {"signal_id": signal_id, "summary": _bracket_summary(lots[0]), "active_exits": exits}

    @app.get("/brackets/{signal_id}/exit-ladder")
    def bracket_exit_ladder(signal_id: str, mark_price: str | None = None) -> dict[str, Any]:
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")
        parsed_mark_price: Decimal | None = None
        if mark_price not in (None, ""):
            try:
                parsed_mark_price = _positive_decimal(mark_price)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "signal_id": signal_id,
            "symbol": lots[0].symbol,
            "direction": lots[0].direction,
            "mark_price": str(parsed_mark_price) if parsed_mark_price is not None else None,
            "ladders": [_bracket_exit_ladder_to_dict(lot, mark_price=parsed_mark_price) for lot in lots],
        }

    @app.get("/brackets/{signal_id}/decision-support")
    def bracket_decision_support(signal_id: str, mark_price: str | None = None) -> dict[str, Any]:
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")
        parsed_mark_price: Decimal | None = None
        if mark_price not in (None, ""):
            try:
                parsed_mark_price = _positive_decimal(mark_price)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {
            "signal_id": signal_id,
            "symbol": lots[0].symbol,
            "direction": lots[0].direction,
            "mark_price": str(parsed_mark_price) if parsed_mark_price is not None else None,
            "mutates_state": False,
            "summaries": [_bracket_decision_support_to_dict(lot, mark_price=parsed_mark_price) for lot in lots],
        }

    @app.post("/brackets/{signal_id}/preview")
    async def bracket_preview(signal_id: str, request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            price = _positive_decimal(payload.get("price"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")
        symbol = lots[0].symbol
        would_trigger = engine.exchange.preview_bracket(signal_id, price)
        preview_exchange = engine.exchange.preview_bracket_exchange(signal_id, price)
        return {
            "signal_id": signal_id,
            "symbol": symbol,
            "price": str(price),
            "would_trigger": would_trigger,
            "impact": _bracket_preview_impact(
                lots,
                preview_exchange=preview_exchange,
                signal_id=signal_id,
                would_trigger=would_trigger,
            ),
            "active_exits": _active_exits_to_dict(lots, signal_id=signal_id, mark_price=price),
            "preview_active_exits": _active_exits_to_dict(
                preview_exchange.lots if preview_exchange is not None else [],
                signal_id=signal_id,
                mark_price=price,
            ),
            "preview_positions": preview_exchange.list_positions() if preview_exchange is not None else [],
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/preview-path")
    async def bracket_preview_path(signal_id: str, request: Request) -> dict[str, Any]:
        payload = await request.json()
        marks_payload = payload.get("prices") or payload.get("marks") or []
        if not isinstance(marks_payload, list) or not marks_payload:
            raise HTTPException(status_code=400, detail="prices or marks must be a non-empty list")
        try:
            prices = [_positive_decimal(price) for price in marks_payload]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")

        symbol = lots[0].symbol
        preview_exchange = deepcopy(engine.exchange)
        preview_exchange.lots = [
            lot for lot in preview_exchange.lots if lot.signal_id == signal_id or lot.symbol != symbol
        ]
        marks: list[dict[str, Any]] = []
        for index, price in enumerate(prices, start=1):
            triggered = preview_exchange.update_price(symbol, price)
            marks.append(
                {
                    "index": index,
                    "price": str(price),
                    "would_trigger": triggered,
                    "preview_active_exits": _active_exits_to_dict(
                        preview_exchange.lots,
                        signal_id=signal_id,
                        mark_price=price,
                    ),
                    "preview_positions": preview_exchange.list_positions(),
                }
            )

        return {
            "signal_id": signal_id,
            "symbol": symbol,
            "mutates_state": False,
            "prices": [str(price) for price in prices],
            "active_exits": _active_exits_to_dict(lots, signal_id=signal_id),
            "marks": marks,
            "final_preview_positions": preview_exchange.list_positions(),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/preview-candle")
    async def bracket_preview_candle(signal_id: str, request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            open_price = _optional_positive_decimal(payload.get("open") or payload.get("open_price"))
            high = _positive_decimal(payload.get("high"))
            low = _positive_decimal(payload.get("low"))
            close = _positive_decimal(payload.get("close"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if high < low:
            raise HTTPException(status_code=400, detail="high must be greater than or equal to low")
        if open_price is not None and (open_price < low or open_price > high):
            raise HTTPException(status_code=400, detail="open must be inside the high/low range")
        if close < low or close > high:
            raise HTTPException(status_code=400, detail="close must be inside the high/low range")
        intrabar_policy = str(payload.get("intrabar_policy") or payload.get("policy") or "conservative_adverse_first")
        if intrabar_policy not in {"conservative_adverse_first", "favorable_first"}:
            raise HTTPException(status_code=400, detail="unsupported intrabar_policy")

        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")
        if any(lot.direction != lots[0].direction for lot in lots):
            raise HTTPException(status_code=409, detail="bracket contains mixed directions")

        symbol = lots[0].symbol
        direction = lots[0].direction
        marks_to_preview = _candle_preview_marks(
            direction=direction,
            high=high,
            low=low,
            close=close,
            open_price=open_price,
            intrabar_policy=intrabar_policy,
        )
        ambiguity = _candle_ambiguity(lots, high=high, low=low)
        preview = _simulate_bracket_mark_sequence(
            engine.exchange,
            signal_id=signal_id,
            symbol=symbol,
            marks_to_preview=marks_to_preview,
        )
        compare_policies = _truthy(payload.get("compare_policies") or payload.get("compare_intrabar_policies"))
        policy_comparison = None
        if compare_policies:
            policy_comparison = _candle_policy_comparison(
                engine.exchange,
                signal_id=signal_id,
                symbol=symbol,
                direction=direction,
                high=high,
                low=low,
                close=close,
                open_price=open_price,
            )

        return {
            "signal_id": signal_id,
            "symbol": symbol,
            "mutates_state": False,
            "intrabar_policy": intrabar_policy,
            "supported_intrabar_policies": ["conservative_adverse_first", "favorable_first"],
            "ambiguous_intrabar": ambiguity["ambiguous"],
            "ambiguity": ambiguity,
            "direction": direction,
            "open": str(open_price) if open_price is not None else None,
            "high": str(high),
            "low": str(low),
            "close": str(close),
            "prices": [str(price) for _, price in marks_to_preview],
            "active_exits": _active_exits_to_dict(lots, signal_id=signal_id),
            "marks": preview["marks"],
            "outcome": preview["outcome"],
            "policy_comparison": policy_comparison,
            "final_preview_positions": preview["final_preview_positions"],
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/trailing-stop/preview-path")
    async def bracket_trailing_stop_preview_path(signal_id: str, request: Request) -> dict[str, Any]:
        payload = await request.json()
        marks_payload = payload.get("prices") or payload.get("marks") or []
        if not isinstance(marks_payload, list) or not marks_payload:
            raise HTTPException(status_code=400, detail="prices or marks must be a non-empty list")
        try:
            prices = [_positive_decimal(price) for price in marks_payload]
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        if not lots:
            raise HTTPException(status_code=404, detail="active bracket not found")
        if not any(exit_order.kind == "trailing_stop" for lot in lots for exit_order in lot.exit_orders):
            raise HTTPException(status_code=404, detail="active trailing stop not found")

        symbol = lots[0].symbol
        preview_exchange = deepcopy(engine.exchange)
        preview_exchange.lots = [
            lot for lot in preview_exchange.lots if lot.signal_id == signal_id or lot.symbol != symbol
        ]
        steps: list[dict[str, Any]] = []
        for index, price in enumerate(prices, start=1):
            before = _trailing_preview_snapshot(preview_exchange.lots, signal_id=signal_id, mark_price=price)
            triggered = preview_exchange.update_price(symbol, price)
            after = _trailing_preview_snapshot(preview_exchange.lots, signal_id=signal_id, mark_price=price)
            steps.append(
                {
                    "index": index,
                    "price": str(price),
                    "would_trigger": triggered,
                    "before": before,
                    "after": after,
                    "ratcheted": _trailing_snapshot_ratcheted(before, after),
                    "activated": _trailing_snapshot_activated(before, after),
                }
            )

        return {
            "signal_id": signal_id,
            "symbol": symbol,
            "mutates_state": False,
            "prices": [str(price) for price in prices],
            "active_trailing": _trailing_preview_snapshot(lots, signal_id=signal_id, mark_price=None),
            "steps": steps,
            "final_preview_trailing": _trailing_preview_snapshot(
                preview_exchange.lots,
                signal_id=signal_id,
                mark_price=prices[-1],
            ),
            "positions": engine.exchange.list_positions(),
            "preview_positions": preview_exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/stop")
    async def amend_bracket_stop(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            trigger_price = _positive_decimal(payload.get("trigger_price") or payload.get("stop_loss_price"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reason = str(payload.get("reason") or "manual protective stop amend")
        order = engine.exchange.amend_bracket_stop(signal_id, trigger_price, reason=reason)
        if order is None:
            raise HTTPException(status_code=409, detail="active bracket not found or stop would loosen risk")
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.stop_amended",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "trigger_price": str(trigger_price),
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/trailing-stop")
    async def amend_bracket_trailing_stop(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            trigger_price = _positive_decimal(payload.get("trigger_price") or payload.get("trailing_stop_price"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reason = str(payload.get("reason") or "manual trailing stop amend")
        order = engine.exchange.amend_bracket_trailing_stop(signal_id, trigger_price, reason=reason)
        if order is None:
            raise HTTPException(status_code=409, detail="active trailing stop not found or amendment would loosen risk")
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.trailing_stop_amended",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "trigger_price": str(trigger_price),
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/trailing-stop/mark")
    async def tighten_bracket_trailing_stop_to_mark(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            mark_price = _positive_decimal(payload.get("mark_price") or payload.get("price"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reason = str(payload.get("reason") or "manual trailing stop tighten from mark")
        order = engine.exchange.tighten_bracket_trailing_stop_to_mark(signal_id, mark_price, reason=reason)
        if order is None:
            raise HTTPException(
                status_code=409,
                detail="active trailing stop not found, mark is not favorable, or amendment would loosen risk",
            )
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.trailing_stop_mark_amended",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "mark_price": str(mark_price),
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "mark_price": str(mark_price),
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id, mark_price=mark_price),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/take-profit")
    async def amend_bracket_take_profit(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            trigger_price = _positive_decimal(payload.get("trigger_price") or payload.get("take_profit_price"))
            target_index = _non_negative_int(payload.get("target_index"), default=0)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reason = str(payload.get("reason") or "manual take-profit amend")
        order = engine.exchange.amend_bracket_take_profit(
            signal_id,
            trigger_price,
            target_index=target_index,
            reason=reason,
        )
        if order is None:
            raise HTTPException(
                status_code=409,
                detail="active take-profit target not found or amendment would reduce projected reward",
            )
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.take_profit_amended",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "trigger_price": str(trigger_price),
                    "target_index": target_index,
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/breakeven")
    async def move_bracket_to_breakeven(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        reason = str(payload.get("reason") or "manual move protective exits to breakeven")
        order = engine.exchange.move_bracket_to_breakeven(signal_id, reason=reason)
        if order is None:
            raise HTTPException(
                status_code=409,
                detail="active bracket not found, no protective exit found, or breakeven would loosen risk",
            )
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.breakeven_amended",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "entry_price": str(order.price),
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/lock-profit")
    async def lock_bracket_profit(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            lock_profit_pct = _positive_decimal(payload.get("lock_profit_pct") or payload.get("profit_lock_pct"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        reason = str(payload.get("reason") or "manual lock protective exits into profit")
        order = engine.exchange.lock_bracket_profit(signal_id, lock_profit_pct, reason=reason)
        if order is None:
            raise HTTPException(
                status_code=409,
                detail="active bracket not found, no protective exit found, or profit lock would loosen risk",
            )
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.profit_locked",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "lock_profit_pct": str(lock_profit_pct),
                    "lock_price": str(order.price),
                    "exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.exit_orders
                    ],
                },
            )
        return {
            "status": "amended",
            "signal_id": signal_id,
            "lock_profit_pct": str(lock_profit_pct),
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots, signal_id=signal_id),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/cancel")
    async def cancel_bracket(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        reason = str(payload.get("reason") or "manual bracket cancel")
        order = engine.exchange.cancel_bracket(signal_id, reason=reason)
        if order is None:
            raise HTTPException(status_code=404, detail="active bracket not found")
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.canceled",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "canceled_exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.canceled_exit_orders
                    ],
                },
            )
        return {
            "status": "canceled",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/close")
    async def close_bracket(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            price = _positive_decimal(payload.get("price") or payload.get("mark_price"))
            close_pct = _optional_positive_decimal(payload.get("close_pct"))
            base_amount = _optional_positive_decimal(payload.get("base_amount") or payload.get("quantity") or payload.get("qty"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if close_pct is not None and close_pct > 100:
            raise HTTPException(status_code=400, detail="close_pct cannot exceed 100")
        if close_pct is not None and base_amount is not None:
            raise HTTPException(status_code=400, detail="send close_pct or base_amount, not both")
        reason = str(payload.get("reason") or "manual paper bracket close")
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        realized_before = _position_realized_pnl(engine.exchange, lots[0].symbol) if lots else Decimal("0")
        order = engine.exchange.close_bracket(
            signal_id,
            price,
            close_pct=close_pct,
            base_amount=base_amount,
            reason=reason,
        )
        if order is None:
            raise HTTPException(status_code=404, detail="active bracket not found")
        realized_pnl_delta = _position_realized_pnl(engine.exchange, order.symbol) - realized_before
        if realized_pnl_delta:
            engine.account_state.daily_pnl += realized_pnl_delta
            if realized_pnl_delta < 0:
                engine.account_state.consecutive_losses += 1
            elif realized_pnl_delta > 0:
                engine.account_state.consecutive_losses = 0
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.closed",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "price": str(price),
                    "close_pct": str(close_pct) if close_pct is not None else None,
                    "base_amount": str(base_amount) if base_amount is not None else None,
                    "realized_pnl_delta": str(realized_pnl_delta),
                    "canceled_exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.canceled_exit_orders
                    ],
                },
            )
        return {
            "status": "closed",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots),
            "realized_pnl_delta": str(realized_pnl_delta),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.post("/brackets/{signal_id}/close-protective")
    async def close_bracket_at_protective_exit(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            close_pct = _optional_positive_decimal(payload.get("close_pct"))
            base_amount = _optional_positive_decimal(payload.get("base_amount") or payload.get("quantity") or payload.get("qty"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        if close_pct is not None and close_pct > 100:
            raise HTTPException(status_code=400, detail="close_pct cannot exceed 100")
        if close_pct is not None and base_amount is not None:
            raise HTTPException(status_code=400, detail="send close_pct or base_amount, not both")
        reason = str(payload.get("reason") or "manual paper bracket protective close")
        lots = [
            lot
            for lot in engine.exchange.lots
            if lot.signal_id == signal_id and lot.remaining_quantity > 0 and lot.exit_orders
        ]
        realized_before = _position_realized_pnl(engine.exchange, lots[0].symbol) if lots else Decimal("0")
        order = engine.exchange.close_bracket_at_protective_exit(
            signal_id,
            close_pct=close_pct,
            base_amount=base_amount,
            reason=reason,
        )
        if order is None:
            raise HTTPException(status_code=404, detail="active bracket with protective exit not found")
        realized_pnl_delta = _position_realized_pnl(engine.exchange, order.symbol) - realized_before
        if realized_pnl_delta:
            engine.account_state.daily_pnl += realized_pnl_delta
            if realized_pnl_delta < 0:
                engine.account_state.consecutive_losses += 1
            elif realized_pnl_delta > 0:
                engine.account_state.consecutive_losses = 0
        engine.account_state.open_notional = engine.exchange.open_notional()
        if repository:
            save_order_with_runtime_state(repository, order)
            repository.record_audit(
                "bracket.protective_closed",
                {
                    "signal_id": signal_id,
                    "reason": reason,
                    "price": str(order.price),
                    "close_pct": str(close_pct) if close_pct is not None else None,
                    "base_amount": str(base_amount) if base_amount is not None else None,
                    "realized_pnl_delta": str(realized_pnl_delta),
                    "canceled_exit_orders": [
                        {
                            "kind": exit_order.kind,
                            "trigger_price": str(exit_order.trigger_price),
                            "close_pct": str(exit_order.close_pct),
                            "oca_group": exit_order.oca_group,
                            "status": exit_order.status,
                        }
                        for exit_order in order.canceled_exit_orders
                    ],
                },
            )
        return {
            "status": "closed",
            "signal_id": signal_id,
            "order": order.to_dict(),
            "active_exits": _active_exits_to_dict(engine.exchange.lots),
            "realized_pnl_delta": str(realized_pnl_delta),
            "positions": engine.exchange.list_positions(),
            "account": _account_state_to_dict(engine.account_state),
        }

    @app.get("/approvals")
    def list_approvals() -> dict[str, Any]:
        return {"pending": intake.list_approvals()}

    @app.post("/approvals/{signal_id}/approve")
    async def approve_signal(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        result = intake.approve(signal_id)
        if result is None:
            raise HTTPException(status_code=404, detail="pending signal not found")
        return result

    @app.post("/approvals/{signal_id}/reject")
    async def reject_signal(signal_id: str, request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        reason = str(payload.get("reason") or "")
        result = intake.reject(signal_id, reason)
        if result is None:
            raise HTTPException(status_code=404, detail="pending signal not found")
        return result

    @app.get("/signals")
    def signals() -> dict[str, Any]:
        return {"signals": repository.list_signals() if repository else []}

    @app.get("/bracket-templates")
    def bracket_templates() -> dict[str, Any]:
        return {
            "templates": list_bracket_templates(),
            "paper_only": True,
            "live_submission_enabled": False,
        }

    @app.get("/bracket-templates/{template_name}")
    def bracket_template(template_name: str) -> dict[str, Any]:
        try:
            template = get_bracket_template(template_name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "template": template.to_dict(),
            "paper_only": True,
            "live_submission_enabled": False,
        }

    @app.get("/strategy-presets")
    def strategy_presets() -> dict[str, Any]:
        return {
            "presets": list_strategy_presets(),
            "paper_only": True,
            "live_submission_enabled": False,
            "submit_endpoint": None,
        }

    @app.get("/strategy-presets/{preset_name}")
    def strategy_preset(preset_name: str) -> dict[str, Any]:
        try:
            preset = get_strategy_preset(preset_name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return {
            "preset": preset.to_dict(),
            "paper_only": True,
            "live_submission_enabled": False,
            "submit_endpoint": None,
        }

    @app.post("/signals/parse-text")
    async def parse_text(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            signal = parse_text_signal(str(payload.get("message") or ""), source="api")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"signal": _signal_to_dict(signal)}

    @app.post("/signals/preview-text")
    async def preview_text(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            signal = parse_text_signal(str(payload.get("message") or ""), source="operator-preview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return signal_preview_with_runtime_controls(signal)

    @app.post("/signals/submit-text")
    async def submit_text(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            signal = parse_text_signal(str(payload.get("message") or ""), source="operator-ui")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return intake.handle(signal)

    @app.post("/signals/submit")
    async def submit_signal(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="operator-ui")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return intake.handle(signal)

    @app.post("/signals/preview")
    async def preview_signal(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="operator-preview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return signal_preview_with_runtime_controls(signal)

    @app.post("/signals/preview-template")
    async def preview_template_signal(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            templated_payload = _templated_signal_payload(payload)
            signal = normalize_signal(templated_payload, source="operator-template-preview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        preview = signal_preview_with_runtime_controls(signal)
        preview["template"] = get_bracket_template(str(templated_payload["bracket_template"])).to_dict()
        preview["merged_signal_payload"] = templated_payload
        preview["paper_only"] = True
        return preview

    @app.post("/signals/preview-strategy")
    async def preview_strategy_signal(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            preset_payload = _strategy_signal_payload(payload)
            signal = normalize_signal(preset_payload, source="operator-strategy-preview")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        preview = signal_preview_with_runtime_controls(signal)
        preview["strategy_preset"] = get_strategy_preset(str(preset_payload["strategy_preset"])).to_dict()
        bracket_template_name = preset_payload.get("bracket_template")
        if bracket_template_name:
            preview["template"] = get_bracket_template(str(bracket_template_name)).to_dict()
        preview["merged_signal_payload"] = preset_payload
        preview["paper_only"] = True
        preview["live_submission_enabled"] = False
        return preview

    @app.post("/signals/submit-template")
    async def submit_template_signal(request: Request) -> dict[str, Any]:
        await verify_signed_operator_request(request)
        payload = await request.json()
        try:
            templated_payload = _templated_signal_payload(payload)
            signal = normalize_signal(templated_payload, source="operator-template")
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        result = intake.handle(signal)
        result["template"] = get_bracket_template(str(templated_payload["bracket_template"])).to_dict()
        result["broker_routed_only"] = True
        return result

    @app.post("/signals/exchange-plan")
    async def signal_exchange_plan(request: Request) -> dict[str, Any]:
        payload = await request.json()
        try:
            signal = normalize_signal(payload, source="operator-plan")
            capabilities = capabilities_for_exchange(signal.exchange)
        except SignalValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except CcxtNotInstalledError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except BitunixConfigurationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        plan = plan_bracket_execution(signal, capabilities)
        return {"signal": _signal_to_dict(signal), "capabilities": capabilities.to_dict(), "plan": plan.to_dict()}

    @app.post("/backtest/signal")
    async def backtest_signal(request: Request) -> dict[str, Any]:
        raise HTTPException(status_code=410, detail="Chain local backtests have been removed from runtime.")

    @app.post("/backtest/bitunix-klines")
    async def backtest_bitunix_klines(request: Request) -> dict[str, Any]:
        raise HTTPException(status_code=410, detail="Chain local backtests have been removed from runtime.")

    @app.post("/backtest/batch")
    async def backtest_batch(request: Request) -> dict[str, Any]:
        raise HTTPException(status_code=410, detail="Chain local backtests have been removed from runtime.")

    @app.post("/backtest/stress")
    async def backtest_stress(request: Request) -> dict[str, Any]:
        raise HTTPException(status_code=410, detail="Chain local backtests have been removed from runtime.")

    @app.get("/audit")
    def audit() -> dict[str, Any]:
        return {"events": [event.to_dict() for event in repository.list_audit()] if repository else []}

    # >>> Sentinel Chain Guardian Scanner add-on >>>
    try:
        from sentinel_chain.scanner.scanner_routes import register_scanner_routes
        register_scanner_routes(app)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Sentinel scanner routes were not registered: %s", exc)
    # <<< Sentinel Chain Guardian Scanner add-on <<<

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


def _live_runtime_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if not _record_references_removed_paper_mode(record)]


def _record_references_removed_paper_mode(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if key_text in {"mode", "exchange", "default_mode"} and str(item).strip().lower() == "paper":
                return True
            if key_text in {"order_id", "signal_id", "strategy_id"} and _paper_identifier(item):
                return True
            if _record_references_removed_paper_mode(item):
                return True
        return False
    if isinstance(value, list):
        return any(_record_references_removed_paper_mode(item) for item in value)
    return False


def _paper_identifier(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text.startswith("paper-") or "-paper-" in text or text.endswith("-paper")


def _merge_runtime_controls(preview: dict[str, Any], summary: dict[str, Any]) -> None:
    preview["protections"] = summary["protections"]
    preview["reentry_cooldown"] = summary["reentry_cooldown"]
    if summary["market_state"] is not None:
        preview["market_state"] = summary["market_state"]
    if summary["futures_risk"] is not None:
        preview["futures_risk"] = summary["futures_risk"]
    preview["advisory_risk"] = summary["advisory_risk"]

    reason_codes = list(summary["reason_codes"])
    if reason_codes:
        existing = list(preview["risk"]["reason_codes"])
        _extend_unique(existing, reason_codes)
        preview["risk"]["reason_codes"] = existing
        preview["risk"]["approved"] = False
        preview["execution"]["next_status"] = "rejected"
        preview["execution"]["would_place_order"] = False
        return

    if summary["approval_required"]:
        preview["execution"]["next_status"] = "approval_required"
        preview["execution"]["approval_required"] = True
        preview["execution"]["would_place_order"] = False


def _scalper_state_key(symbol: str) -> str:
    return f"{SCALPER_STATE_PREFIX}{symbol}"


def _scalper_state(repository: SQLiteRepository | None, symbol: str) -> dict[str, Any] | None:
    if repository is None:
        return None
    return repository.get_runtime_state(_scalper_state_key(symbol))


def _scalper_rebracket_payload(
    payload: dict[str, Any],
    *,
    repository: SQLiteRepository | None,
) -> tuple[str, Any, dict[str, Any] | None, dict[str, Any]]:
    symbol = normalize_symbol(payload.get("symbol") or payload.get("ticker") or payload.get("pair"))
    existing = _scalper_state(repository, symbol) or {}
    band_payload = existing.get("band") if isinstance(existing.get("band"), dict) else {}
    band = PriceBand(
        lower=_positive_decimal(payload.get("lower_price") or payload.get("buy_target") or band_payload.get("lower")),
        upper=_positive_decimal(payload.get("upper_price") or payload.get("sell_target") or band_payload.get("upper")),
    )
    config = _scalper_config_from_payload(payload, default_spread=band.width)
    recent_source = payload.get("recent_prices", existing.get("recent_prices", []))
    recent_prices = tuple(_positive_decimal(value) for value in recent_source if value is not None)
    decision = plan_rebracket(
        symbol=symbol,
        price=_positive_decimal(payload.get("price") or payload.get("mark_price")),
        band=band,
        config=config,
        state=RebracketRuntimeState(
            recent_prices=recent_prices,
            last_rebracket_at=_optional_datetime(existing.get("last_rebracket_at")),
        ),
        now=_optional_datetime(payload.get("now")),
        position_open=_truthy(payload.get("position_open")),
    )
    side = str(payload.get("side") or "buy")
    suggested_signal = (
        scalper_signal_payload(
            symbol,
            side,
            decision.new_band,
            quote_amount=_optional_positive_decimal(payload.get("quote_amount")),
            base_amount=_optional_positive_decimal(payload.get("base_amount") or payload.get("quantity")),
            risk_amount=_optional_positive_decimal(payload.get("risk_amount")),
            risk_pct=_optional_positive_decimal(payload.get("risk_pct")),
            stop_distance=_optional_positive_decimal(payload.get("stop_distance") or payload.get("stop_loss_distance")),
            exchange=str(payload.get("exchange") or payload.get("venue") or "").strip().lower(),
            market_type=str(payload.get("market_type") or "swap").strip().lower(),
        )
        if decision.new_band is not None
        else None
    )
    persisted_band = decision.new_band or band
    state_payload = {
        "symbol": symbol,
        "band": persisted_band.to_dict(),
        "previous_band": decision.previous_band.to_dict(),
        "recent_prices": [_decimal_to_plain(price) for price in decision.recent_prices],
        "last_rebracket_at": decision.decided_at.isoformat() if decision.decided_at else None,
        "config": _scalper_config_to_dict(config),
    }
    return symbol, decision, suggested_signal, state_payload


def _scalper_config_from_payload(payload: dict[str, Any], *, default_spread: Decimal) -> ScalperBracketConfig:
    config_payload = payload.get("config") if isinstance(payload.get("config"), dict) else {}

    def config_value(*names: str) -> Any:
        for name in names:
            if name in config_payload:
                return config_payload[name]
            if name in payload:
                return payload[name]
        return None

    return ScalperBracketConfig(
        threshold=_decimal(config_value("threshold", "rebracket_threshold"), default=ScalperBracketConfig.threshold),
        min_drift=_decimal(config_value("min_drift", "rebracket_min_drift"), default=ScalperBracketConfig.min_drift),
        spread=_decimal(config_value("spread", "rebracket_spread"), default=default_spread),
        buffer=_decimal(config_value("buffer", "rebracket_buffer"), default=ScalperBracketConfig.buffer),
        cooldown_seconds=_optional_int(config_value("cooldown_seconds", "rebracket_cooldown")) or 0,
        lookback=_optional_int(config_value("lookback", "rebracket_lookback")) or ScalperBracketConfig.lookback,
        price_increment=_decimal(
            config_value("price_increment", "tick_size"),
            default=ScalperBracketConfig.price_increment,
        ),
    )


def _scalper_config_to_dict(config: ScalperBracketConfig) -> dict[str, Any]:
    return {
        "threshold": _decimal_to_plain(config.threshold),
        "min_drift": _decimal_to_plain(config.min_drift),
        "spread": _decimal_to_plain(config.spread),
        "buffer": _decimal_to_plain(config.buffer),
        "cooldown_seconds": config.cooldown_seconds,
        "lookback": config.lookback,
        "price_increment": _decimal_to_plain(config.price_increment),
    }


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _extend_unique(values: list[str], additions: list[str]) -> None:
    for value in additions:
        _append_unique(values, value)


def _batch_result_rank_row(result: dict[str, Any]) -> dict[str, Any]:
    metrics = result.get("report_metrics", {})
    risk = result.get("risk_summary", {})
    return {
        "name": result.get("name"),
        "symbol": result.get("symbol"),
        "status": result.get("status"),
        "final_total_pnl": result.get("final_total_pnl"),
        "final_daily_pnl": result.get("final_daily_pnl"),
        "total_return_pct": metrics.get("total_return_pct"),
        "win_rate_pct": metrics.get("win_rate_pct"),
        "profit_factor": metrics.get("profit_factor"),
        "max_drawdown": risk.get("max_drawdown"),
        "total_triggers": result.get("total_triggers"),
    }


def _templated_signal_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    template_name = str(payload.get("template") or payload.get("template_name") or "").strip()
    if not template_name:
        raise ValueError("template is required")
    signal_payload = payload.get("signal")
    if signal_payload is None:
        signal_payload = {
            key: value
            for key, value in payload.items()
            if key not in {"template", "template_name", "overrides", "template_overrides"}
        }
    overrides = payload.get("overrides") or payload.get("template_overrides")
    return apply_bracket_template(signal_payload, template_name, overrides=overrides)


def _strategy_signal_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    preset_name = str(payload.get("strategy") or payload.get("strategy_preset") or payload.get("preset") or "").strip()
    if not preset_name:
        raise ValueError("strategy preset is required")
    signal_payload = payload.get("signal")
    if signal_payload is None:
        signal_payload = {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "strategy",
                "strategy_preset",
                "preset",
                "overrides",
                "strategy_overrides",
                "template",
                "template_name",
                "bracket_template",
                "template_overrides",
            }
        }
    overrides = payload.get("overrides") or payload.get("strategy_overrides")
    preset_payload = apply_strategy_preset(signal_payload, preset_name, overrides=overrides)
    template_name = (
        payload.get("template")
        or payload.get("template_name")
        or payload.get("bracket_template")
        or get_strategy_preset(preset_name).suggested_bracket_template
    )
    return apply_bracket_template(
        preset_payload,
        str(template_name),
        overrides=payload.get("template_overrides"),
    )


def _triggered_with_order_metadata(triggered: list[dict], orders: list[Any]) -> list[dict]:
    enriched: list[dict] = []
    order_index = 0
    for item in triggered:
        payload = dict(item)
        while order_index < len(orders):
            order = orders[order_index]
            order_index += 1
            if order.exit_kind != item.get("kind"):
                continue
            if order.exit_orders:
                exit_order = order.exit_orders[0]
                payload["oca_group"] = exit_order.oca_group
                payload["trigger_price"] = str(exit_order.trigger_price)
                payload["trigger_gap"] = _decimal_to_plain(_trigger_gap(item, exit_order))
            if order.canceled_exit_orders:
                payload["canceled_exit_orders"] = [
                    exit_order_payload(exit_order) for exit_order in order.canceled_exit_orders
                ]
            break
        enriched.append(payload)
    return enriched


def _trigger_gap(triggered: dict, exit_order: Any) -> Decimal:
    fill_price = Decimal(str(triggered["price"]))
    if exit_order.kind in {"stop_loss", "trailing_stop"}:
        if fill_price <= exit_order.trigger_price:
            return exit_order.trigger_price - fill_price
        return fill_price - exit_order.trigger_price
    if exit_order.kind == "take_profit":
        if fill_price >= exit_order.trigger_price:
            return fill_price - exit_order.trigger_price
        return exit_order.trigger_price - fill_price
    return abs(fill_price - exit_order.trigger_price)


def _position_realized_pnl(exchange: PaperExchange, symbol: str) -> Decimal:
    position = exchange.positions.get(symbol)
    return position.realized_pnl if position else Decimal("0")


def _candle_preview_marks(
    *,
    direction: str,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    open_price: Decimal | None,
    intrabar_policy: str,
) -> list[tuple[str, Decimal]]:
    adverse = low if direction == "long" else high
    favorable = high if direction == "long" else low
    if intrabar_policy == "favorable_first":
        phases = [("favorable", favorable), ("adverse", adverse), ("close", close)]
    else:
        phases = [("adverse", adverse), ("favorable", favorable), ("close", close)]
    if open_price is None:
        return phases
    return [("open", open_price), *phases]


def _simulate_bracket_mark_sequence(
    base_exchange: PaperExchange,
    *,
    signal_id: str,
    symbol: str,
    marks_to_preview: list[tuple[str, Decimal]],
) -> dict[str, Any]:
    preview_exchange = deepcopy(base_exchange)
    preview_exchange.lots = [
        lot for lot in preview_exchange.lots if lot.signal_id == signal_id or lot.symbol != symbol
    ]
    marks: list[dict[str, Any]] = []
    triggered_rows: list[dict[str, Any]] = []
    for phase, price in marks_to_preview:
        triggered = preview_exchange.update_price(symbol, price)
        for row in triggered:
            triggered_rows.append({"phase": phase, **row})
        marks.append(
            {
                "phase": phase,
                "price": str(price),
                "would_trigger": triggered,
                "preview_active_exits": _active_exits_to_dict(
                    preview_exchange.lots,
                    signal_id=signal_id,
                    mark_price=price,
                ),
                "preview_positions": preview_exchange.list_positions(),
            }
        )
    positions = preview_exchange.list_positions()
    final_position = next((position for position in positions if position["symbol"] == symbol), None)
    remaining_quantity = sum(
        (
            lot.remaining_quantity
            for lot in preview_exchange.lots
            if lot.signal_id == signal_id and lot.symbol == symbol and lot.remaining_quantity > 0
        ),
        Decimal("0"),
    )
    first_trigger = triggered_rows[0] if triggered_rows else None
    return {
        "marks": marks,
        "final_preview_positions": positions,
        "outcome": {
            "trigger_count": len(triggered_rows),
            "triggered_kinds": [row["kind"] for row in triggered_rows],
            "first_trigger_phase": first_trigger["phase"] if first_trigger else None,
            "first_trigger_kind": first_trigger["kind"] if first_trigger else None,
            "bracket_closed": remaining_quantity == 0,
            "remaining_quantity": _decimal_to_plain(remaining_quantity),
            "final_position_quantity": final_position["quantity"] if final_position else "0.00000000",
            "final_realized_pnl": final_position["realized_pnl"] if final_position else "0.00000000",
        },
    }


def _candle_policy_comparison(
    base_exchange: PaperExchange,
    *,
    signal_id: str,
    symbol: str,
    direction: str,
    high: Decimal,
    low: Decimal,
    close: Decimal,
    open_price: Decimal | None,
) -> dict[str, Any]:
    outcomes: dict[str, Any] = {}
    for policy in ("conservative_adverse_first", "favorable_first"):
        marks_to_preview = _candle_preview_marks(
            direction=direction,
            high=high,
            low=low,
            close=close,
            open_price=open_price,
            intrabar_policy=policy,
        )
        preview = _simulate_bracket_mark_sequence(
            base_exchange,
            signal_id=signal_id,
            symbol=symbol,
            marks_to_preview=marks_to_preview,
        )
        outcomes[policy] = {
            "prices": [str(price) for _, price in marks_to_preview],
            "phases": [phase for phase, _ in marks_to_preview],
            "outcome": preview["outcome"],
        }
    conservative_pnl = Decimal(outcomes["conservative_adverse_first"]["outcome"]["final_realized_pnl"])
    favorable_pnl = Decimal(outcomes["favorable_first"]["outcome"]["final_realized_pnl"])
    return {
        "policies": outcomes,
        "outcome_diverged": outcomes["conservative_adverse_first"]["outcome"] != outcomes["favorable_first"]["outcome"],
        "pnl_range": {
            "low": _decimal_to_plain(min(conservative_pnl, favorable_pnl)),
            "high": _decimal_to_plain(max(conservative_pnl, favorable_pnl)),
            "spread": _decimal_to_plain(abs(favorable_pnl - conservative_pnl)),
        },
    }


def _candle_ambiguity(lots: list[Any], *, high: Decimal, low: Decimal) -> dict[str, Any]:
    rows = [_lot_candle_ambiguity(lot, high=high, low=low) for lot in lots]
    protective_touched = sum(row["protective_touched"] for row in rows)
    profit_touched = sum(row["profit_touched"] for row in rows)
    ambiguous_lots = [row for row in rows if row["ambiguous"]]
    return {
        "ambiguous": bool(ambiguous_lots),
        "policy_note": "candle range contains both protective and profit exits; compare policies before trusting a single-fill outcome"
        if ambiguous_lots
        else None,
        "protective_touched_count": protective_touched,
        "profit_touched_count": profit_touched,
        "lots": rows,
    }


def _lot_candle_ambiguity(lot: Any, *, high: Decimal, low: Decimal) -> dict[str, Any]:
    protective: list[dict[str, str]] = []
    profit: list[dict[str, str]] = []
    for exit_order in lot.exit_orders:
        if exit_order.status not in {"open", "waiting"}:
            continue
        touched = _exit_touched_by_candle(lot, exit_order, high=high, low=low)
        if not touched:
            continue
        row = {"kind": exit_order.kind, "trigger_price": str(exit_order.trigger_price)}
        if exit_order.kind in {"stop_loss", "trailing_stop", "time_exit"}:
            protective.append(row)
        elif exit_order.kind == "take_profit":
            profit.append(row)
    return {
        "signal_id": lot.signal_id,
        "symbol": lot.symbol,
        "direction": lot.direction,
        "protective_touched": len(protective),
        "profit_touched": len(profit),
        "ambiguous": bool(protective and profit),
        "protective_exits": protective,
        "profit_exits": profit,
    }


def _exit_touched_by_candle(lot: Any, exit_order: Any, *, high: Decimal, low: Decimal) -> bool:
    if exit_order.kind == "time_exit":
        return False
    if lot.direction == "long":
        if exit_order.kind in {"stop_loss", "trailing_stop"}:
            return low <= exit_order.trigger_price
        if exit_order.kind == "take_profit":
            return high >= exit_order.trigger_price
        return False
    if exit_order.kind in {"stop_loss", "trailing_stop"}:
        return high >= exit_order.trigger_price
    if exit_order.kind == "take_profit":
        return low <= exit_order.trigger_price
    return False


# BEGIN SENTINEL CHAIN WAR ROOM ADDON ROUTES
try:
    from sentinel_chain.charting.routes import register_war_room_routes as _sc_register_war_room_routes
except Exception as _sc_war_room_exc:  # pragma: no cover - defensive startup logging only.
    import logging as _sc_war_room_logging
    _sc_war_room_logging.getLogger(__name__).warning("Sentinel Chain War Room routes were not registered: %s", _sc_war_room_exc)
else:
    def _sc_wire_war_room_routes(_sc_app):
        try:
            return _sc_register_war_room_routes(_sc_app)
        except Exception as _sc_route_exc:  # pragma: no cover - defensive startup logging only.
            import logging as _sc_war_room_logging
            _sc_war_room_logging.getLogger(__name__).exception("Failed to register Sentinel Chain War Room routes: %s", _sc_route_exc)
            return _sc_app

    if "create_app_from_env" in globals() and not getattr(create_app_from_env, "_sc_war_room_wrapped", False):
        _sc_original_create_app_from_env_war = create_app_from_env

        def create_app_from_env(*args, **kwargs):
            return _sc_wire_war_room_routes(_sc_original_create_app_from_env_war(*args, **kwargs))

        create_app_from_env._sc_war_room_wrapped = True

    if "create_app" in globals() and not getattr(create_app, "_sc_war_room_wrapped", False):
        _sc_original_create_app_war = create_app

        def create_app(*args, **kwargs):
            return _sc_wire_war_room_routes(_sc_original_create_app_war(*args, **kwargs))

        create_app._sc_war_room_wrapped = True

    if "app" in globals():
        app = _sc_wire_war_room_routes(app)
# END SENTINEL CHAIN WAR ROOM ADDON ROUTES

# BEGIN SENTINEL CHAIN GUARDIAN CHART ROUTES
try:
    from sentinel_chain.sentinel_guardian_routes import (
        register_guardian_chart_routes as _sc_register_guardian_chart_routes,
    )
except Exception as _sc_guardian_exc:  # pragma: no cover - defensive startup logging only.
    import logging as _sc_guardian_logging

    _sc_guardian_logging.getLogger(__name__).warning(
        "Sentinel Chain Guardian chart routes were not registered: %s",
        _sc_guardian_exc,
    )
else:
    def _sc_wire_guardian_chart_routes(_sc_app):
        try:
            return _sc_register_guardian_chart_routes(_sc_app)
        except Exception as _sc_route_exc:  # pragma: no cover - defensive startup logging only.
            import logging as _sc_guardian_logging

            _sc_guardian_logging.getLogger(__name__).exception(
                "Failed to register Sentinel Chain Guardian chart routes: %s",
                _sc_route_exc,
            )
            return _sc_app

    if "create_app_from_env" in globals() and not getattr(create_app_from_env, "_sc_guardian_chart_wrapped", False):
        _sc_original_create_app_from_env_guardian = create_app_from_env

        def create_app_from_env(*args, **kwargs):
            return _sc_wire_guardian_chart_routes(_sc_original_create_app_from_env_guardian(*args, **kwargs))

        create_app_from_env._sc_guardian_chart_wrapped = True

    if "create_app" in globals() and not getattr(create_app, "_sc_guardian_chart_wrapped", False):
        _sc_original_create_app_guardian = create_app

        def create_app(*args, **kwargs):
            return _sc_wire_guardian_chart_routes(_sc_original_create_app_guardian(*args, **kwargs))

        create_app._sc_guardian_chart_wrapped = True

    if "app" in globals():
        app = _sc_wire_guardian_chart_routes(app)
# END SENTINEL CHAIN GUARDIAN CHART ROUTES
