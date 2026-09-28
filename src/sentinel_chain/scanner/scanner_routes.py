"""FastAPI routes for Sentinel Chain Scanner."""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import APIRouter, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .scanner_engine import ScannerEngine, build_chart_review_payload, build_guardian_plan_payload, build_trade_intent_payload
from .scanner_models import HitPromotionRequest, SaveRuleRequest, ScannerRunRequest, model_dump_compat
from .scanner_rules import preset_rules
from .scanner_store import ScannerStore


router = APIRouter(prefix="/scanner", tags=["scanner"])
_store: Optional[ScannerStore] = None
_engine: Optional[ScannerEngine] = None


def get_store() -> ScannerStore:
    global _store
    if _store is None:
        _store = ScannerStore()
    return _store


def get_engine() -> ScannerEngine:
    global _engine
    if _engine is None:
        _engine = ScannerEngine(get_store())
    return _engine


@router.get("/features")
def scanner_features() -> Dict[str, Any]:
    return {
        "name": "Sentinel Chain Guardian Scanner",
        "role": "signal discovery layer above Guardian/signals/live-preview",
        "live_ready": True,
        "direct_broker_orders": False,
        "supported_sources": ["guardian", "bitunix", "ccxt", "war-room", "manual-candles"],
        "actions": ["open_chart", "trade_intent", "build_bracket", "guardian_plan", "signal_preview", "guardian_live_preview", "submit_through_existing_signal_routes"],
        "condition_fields": [
            "price_change_pct",
            "volume_ratio",
            "atr_pct",
            "range_compression",
            "contraction_count",
            "vcp_score",
            "breakout_above_resistance",
            "support_break",
            "rejection_at_resistance",
            "rejection_at_support",
            "ema_stack_bullish",
            "ema_stack_bearish",
            "trend_pullback_long",
            "trend_pullback_short",
            "rsi",
            "macd_hist",
            "macd_bullish",
            "macd_bearish",
            "bb_width_pct",
            "adx",
            "support_distance_pct",
            "resistance_distance_pct",
            "spread_pct",
            "bid_ask_imbalance",
            "funding_rate",
            "open_interest_change_pct",
        ],
        "operators": [">", ">=", "<", "<=", "==", "!=", "between", "outside", "crosses_above", "crosses_below", "near", "not_near", "truthy", "falsy"],
    }


@router.get("/presets")
def get_presets() -> Dict[str, Any]:
    rules = [model_dump_compat(rule) for rule in preset_rules()]
    return {"presets": rules}


@router.get("/rules")
def list_rules(enabled_only: bool = False) -> Dict[str, Any]:
    rules = [model_dump_compat(rule) for rule in get_store().list_rules(enabled_only=enabled_only)]
    return {"rules": rules}


@router.post("/rules")
def save_rule(request: SaveRuleRequest) -> Dict[str, Any]:
    rule = get_store().save_rule(request.rule)
    return {"ok": True, "rule": model_dump_compat(rule)}


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: str) -> Dict[str, Any]:
    return {"ok": get_store().delete_rule(rule_id), "rule_id": rule_id}


@router.post("/run")
def run_scanner(request: ScannerRunRequest) -> Dict[str, Any]:
    response = get_engine().run(request)
    return model_dump_compat(response)


@router.get("/hits")
def list_hits(
    limit: int = Query(100, ge=1, le=1000),
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    symbol: Optional[str] = None,
) -> Dict[str, Any]:
    hits = [model_dump_compat(hit) for hit in get_store().list_hits(limit=limit, min_score=min_score, symbol=symbol)]
    return {"hits": hits}


@router.get("/hits/{hit_id}")
def get_hit(hit_id: str) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    return {"hit": model_dump_compat(hit)}


@router.post("/hits/{hit_id}/intent")
def hit_intent(hit_id: str, request: HitPromotionRequest = HitPromotionRequest(mode="ticket")) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    get_store().update_hit_status(hit_id, "reviewed")
    overrides = _promotion_overrides(request)
    intent = build_trade_intent_payload(hit, account_id=request.account_id, overrides=overrides)
    return {"ok": True, "mode": "intent", "hit_id": hit_id, "intent": intent, "next_routes": _next_routes(hit_id)}


@router.post("/hits/{hit_id}/chart")
def hit_chart(hit_id: str) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    get_store().update_hit_status(hit_id, "reviewed")
    return {"ok": True, "mode": "chart", "chart_payload": build_chart_review_payload(hit), "next_routes": _next_routes(hit_id)}


@router.post("/hits/{hit_id}/ticket")
def hit_ticket(hit_id: str, request: HitPromotionRequest = HitPromotionRequest(mode="ticket")) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    get_store().update_hit_status(hit_id, "promoted")
    overrides = _promotion_overrides(request)
    payload = build_guardian_plan_payload(hit, account_id=request.account_id, overrides=overrides)
    return {
        "ok": True,
        "mode": "ticket",
        "hit_id": hit_id,
        "ticket": payload.get("ticket"),
        "why": payload.get("why"),
        "warnings": payload.get("warnings"),
        "next_routes": _next_routes(hit_id),
    }


@router.post("/hits/{hit_id}/guardian-plan")
def hit_guardian_plan(hit_id: str, request: HitPromotionRequest = HitPromotionRequest(mode="guardian_plan")) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    get_store().update_hit_status(hit_id, "promoted")
    payload = build_guardian_plan_payload(hit, account_id=request.account_id, overrides=_promotion_overrides(request))
    payload["route_intent"] = "guardian_plan"
    return {"ok": True, "guardian_plan": payload, "next_routes": _next_routes(hit_id)}


@router.post("/hits/{hit_id}/signal-preview")
def hit_signal_preview(hit_id: str, request: HitPromotionRequest = HitPromotionRequest(mode="signal_preview")) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    payload = build_guardian_plan_payload(hit, account_id=request.account_id, overrides=_promotion_overrides(request))
    payload["route_intent"] = "signal_preview"
    # The scanner returns the exact payload to send to existing /signals/preview.
    return {"ok": True, "target_route": "/signals/preview", "payload": payload, "next_routes": _next_routes(hit_id)}


@router.post("/hits/{hit_id}/live-preview")
def hit_live_preview(hit_id: str, request: HitPromotionRequest = HitPromotionRequest(mode="live_preview")) -> Dict[str, Any]:
    hit = get_store().get_hit(hit_id)
    if hit is None:
        raise HTTPException(status_code=404, detail="scan hit not found")
    payload = build_guardian_plan_payload(hit, account_id=request.account_id, overrides=_promotion_overrides(request))
    payload["route_intent"] = "guardian_live_preview"
    payload["live_preview_only"] = True
    return {
        "ok": True,
        "target_route": "/guardian/live/preview",
        "payload": payload,
        "note": "No exchange order was sent by /scanner. Submit only through Guardian/signals after their live gates and risk checks pass.",
        "next_routes": _next_routes(hit_id),
    }


@router.websocket("/ws/hits")
async def hits_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        params = websocket.query_params
        min_score = float(params.get("min_score", 0.0))
        limit = int(params.get("limit", 50))
        last_ids = set()
        while True:
            hits = get_store().list_hits(limit=limit, min_score=min_score)
            payload = [model_dump_compat(hit) for hit in hits if hit.id not in last_ids]
            if payload:
                last_ids.update(hit["id"] for hit in payload)
                await websocket.send_json({"type": "scanner_hits", "hits": payload})
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        return
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass


def _promotion_overrides(request: HitPromotionRequest) -> Dict[str, Any]:
    overrides: Dict[str, Any] = {}
    for field in ("risk_fraction", "quantity", "leverage", "margin_mode", "order_type", "live_ready", "notes"):
        value = getattr(request, field, None)
        if value is not None:
            overrides[field] = value
    return overrides


def _next_routes(hit_id: str) -> Dict[str, str]:
    return {
        "scanner_hit": f"/scanner/hits/{hit_id}",
        "intent": f"/scanner/hits/{hit_id}/intent",
        "chart_payload": f"/scanner/hits/{hit_id}/chart",
        "ticket": f"/scanner/hits/{hit_id}/ticket",
        "guardian_plan": f"/scanner/hits/{hit_id}/guardian-plan",
        "signal_preview": f"/scanner/hits/{hit_id}/signal-preview",
        "guardian_live_preview": f"/scanner/hits/{hit_id}/live-preview",
        "chart": "/war-room/ui",
    }


def _static_root() -> Path:
    return Path(__file__).resolve().parents[1] / "static" / "scanner"


@router.get("/ui", response_class=HTMLResponse)
def scanner_ui() -> Any:
    html = _static_root() / "scanner.html"
    if html.exists():
        return FileResponse(str(html), media_type="text/html")
    return HTMLResponse(
        """
        <html><body style='font-family: sans-serif; background:#090d12; color:#e8eef7'>
        <h1>Sentinel Chain Scanner</h1>
        <p>Scanner UI files were not installed. API is available under /scanner/*.</p>
        </body></html>
        """
    )


def register_scanner_routes(app: FastAPI, store_path: Optional[str] = None) -> None:
    """Register scanner routes and static assets with a FastAPI app."""
    global _store, _engine
    if store_path:
        _store = ScannerStore(store_path)
        _engine = ScannerEngine(_store)
    else:
        _store = _store or ScannerStore()
        _engine = _engine or ScannerEngine(_store)

    # Avoid duplicate route registration when create_app is called repeatedly in tests.
    existing = {getattr(route, "path", "") for route in getattr(app, "routes", [])}
    if "/scanner/features" not in existing:
        app.include_router(router)

    static_root = _static_root()
    if static_root.exists() and "/scanner/static" not in existing:
        try:
            app.mount("/scanner/static", StaticFiles(directory=str(static_root)), name="scanner_static")
        except RuntimeError:
            # Static mount may already exist under this name in reload/test contexts.
            pass
