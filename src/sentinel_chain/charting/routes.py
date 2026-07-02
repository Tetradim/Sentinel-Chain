"""FastAPI routes for the Sentinel Chain Trading War Room UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from .automap import analyze_market_structure, backtest_auto_strategy, generate_demo_candles, playbook_catalog

STATIC_DIR = Path(__file__).resolve().parents[1] / "static"


class CandlePayload(BaseModel):
    time: Any = None
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class AnalyzePayload(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    candles: List[CandlePayload] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


class BacktestPayload(AnalyzePayload):
    pass


class TicketPayload(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "15m"
    venue: str = "paper"
    market_type: str = "swap"
    side: Optional[str] = None
    account_equity: float = 10000.0
    risk_pct: float = 1.0
    leverage: float = 1.0
    candles: List[CandlePayload] = Field(default_factory=list)
    settings: Dict[str, Any] = Field(default_factory=dict)


def _static_file(name: str) -> Path:
    allowed = {"war_room.html", "war_room.css", "war_room.js", "futures.html", "futures.css", "futures.js"}
    if name not in allowed:
        raise HTTPException(status_code=404, detail="Unknown War Room asset")
    path = STATIC_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Missing static asset: {name}")
    return path


router = APIRouter(prefix="/war-room", tags=["sentinel-war-room"])


@router.get("/ui", response_class=HTMLResponse)
def trading_war_room_ui() -> HTMLResponse:
    path = _static_file("war_room.html")
    return HTMLResponse(path.read_text(encoding="utf-8"))


@router.get("/static/{asset_name}")
def trading_war_room_static(asset_name: str) -> FileResponse:
    path = _static_file(asset_name)
    media_type = "text/css" if path.suffix == ".css" else "application/javascript" if path.suffix == ".js" else "text/html"
    return FileResponse(path, media_type=media_type)


@router.get("/features")
def trading_war_room_features() -> dict[str, Any]:
    return {
        "ok": True,
        "name": "Sentinel Chain Trading War Room",
        "routes": {
            "ui": "/war-room/ui",
            "demo": "/war-room/demo?symbol=BTCUSDT&timeframe=15m&bars=260",
            "analyze": "POST /war-room/analyze",
            "backtest": "POST /war-room/backtest",
            "ticket": "POST /war-room/ticket",
        },
        "feature_flags": {
            "auto_support_resistance": True,
            "inflection_pivots": True,
            "trendline_hough_scoring": True,
            "volume_profile": True,
            "poc_vah_val": True,
            "fibonacci_map": True,
            "fvg_imbalance_zones": True,
            "order_blocks": True,
            "candlestick_patterns": True,
            "chart_patterns": True,
            "rsi_macd_divergence": True,
            "bos_choch_structure": True,
            "bracket_plan": True,
            "futures_ticket_preview": True,
            "dom_ladder_projection": True,
            "paper_submit_payload_builder": True,
        },
        "playbooks": playbook_catalog(),
    }


@router.get("/demo")
def trading_war_room_demo(
    symbol: str = Query("BTCUSDT"),
    timeframe: str = Query("15m"),
    bars: int = Query(260, ge=60, le=1200),
    seed: Optional[int] = Query(None),
) -> dict[str, Any]:
    candles = generate_demo_candles(symbol=symbol, timeframe=timeframe, bars=bars, seed=seed)
    return analyze_market_structure(candles, symbol=symbol, timeframe=timeframe)


@router.post("/analyze")
def trading_war_room_analyze(payload: AnalyzePayload) -> dict[str, Any]:
    candles = [item.dict() for item in payload.candles]
    return analyze_market_structure(candles, symbol=payload.symbol, timeframe=payload.timeframe, settings=payload.settings)


@router.post("/backtest")
def trading_war_room_backtest(payload: BacktestPayload) -> dict[str, Any]:
    candles = [item.dict() for item in payload.candles]
    return backtest_auto_strategy(candles, symbol=payload.symbol, timeframe=payload.timeframe, settings=payload.settings)


@router.post("/ticket")
def trading_war_room_ticket(payload: TicketPayload) -> dict[str, Any]:
    settings = dict(payload.settings or {})
    risk = dict(settings.get("risk") or {})
    risk.update({"account_equity": payload.account_equity, "risk_pct": payload.risk_pct})
    settings["risk"] = risk
    candles = [item.dict() for item in payload.candles]
    analysis = analyze_market_structure(candles, symbol=payload.symbol, timeframe=payload.timeframe, settings=settings)
    if not analysis.get("ok"):
        return analysis
    side = (payload.side or analysis["signals"].get("primary_bias") or "long").lower()
    if side in {"buy", "long", "buy_long"}:
        side_key = "long"
        order_side = "buy"
    elif side in {"sell", "short", "sell_short"}:
        side_key = "short"
        order_side = "sell"
    else:
        side_key = analysis["signals"].get("primary_bias", "long")
        order_side = "buy" if side_key == "long" else "sell"
    plan = analysis["signals"]["trade_plans"][side_key]
    futures = payload.market_type in {"swap", "future", "futures", "perpetual"}
    signal = {
        "source": "sentinel-war-room",
        "symbol": payload.symbol,
        "side": order_side,
        "market_type": payload.market_type,
        "exchange": payload.venue,
        "price": plan["entry"],
        "quote_amount": plan["suggested_quote_notional"],
        "risk_pct": payload.risk_pct,
        "leverage": payload.leverage if futures else 1,
        "strategy_id": f"war_room_{analysis['signals'].get('recommendation', 'manual')}",
        "bracket": {
            "stop_loss": plan["stop_loss"],
            "take_profit": plan["targets"][0]["target"] if plan.get("targets") else None,
            "take_profit_targets": plan.get("targets", []),
            "trailing_stop": {
                "activation_rr": plan.get("trailing", {}).get("activation_rr", 1.0),
                "callback_atr_multiple": plan.get("trailing", {}).get("callback_atr_multiple", 1.15),
                "after_take_profit": True,
            },
            "breakeven_after_take_profit": True,
            "profit_lock_after_take_profit": True,
        },
        "operator_note": analysis["signals"].get("why", {}).get("headline"),
        "paper_only": True,
        "reduce_only_exits": futures,
    }
    return {"ok": True, "analysis": analysis, "plan": plan, "signal": signal}


def register_war_room_routes(app: Any) -> Any:
    """Register routes on a FastAPI app and return the app for patch wrappers."""
    marker = "_sentinel_war_room_routes_registered"
    if getattr(app, marker, False):
        return app
    app.include_router(router)
    setattr(app, marker, True)
    return app
