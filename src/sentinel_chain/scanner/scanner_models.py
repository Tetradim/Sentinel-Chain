"""Typed models for Sentinel Chain's live-ready scanner layer.

The scanner intentionally sits above Guardian/signals/live-preview. It discovers
and explains setups, then emits structured tickets that existing execution routes
can validate and submit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Sequence, Union
from uuid import uuid4

try:  # FastAPI already depends on pydantic; keep imports local-friendly.
    from pydantic import BaseModel, Field
except Exception:  # pragma: no cover - pydantic should be present in Sentinel Chain.
    BaseModel = object  # type: ignore
    Field = lambda default=None, **_: default  # type: ignore


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class CandlePoint(BaseModel):
    """OHLCV candle used by scanner rules.

    Timestamp may be epoch milliseconds, epoch seconds, ISO string, or omitted.
    """

    timestamp: Union[int, float, str, None] = None
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class ScannerCondition(BaseModel):
    """One rule condition.

    `value` may be a number or a feature name such as "pivot_high",
    "support", "resistance", "vwap", or "atr".
    """

    field: str
    op: Literal[
        ">",
        ">=",
        "<",
        "<=",
        "==",
        "!=",
        "between",
        "outside",
        "crosses_above",
        "crosses_below",
        "near",
        "not_near",
        "truthy",
        "falsy",
    ]
    value: Any = None
    value2: Any = None
    weight: float = 1.0
    required: bool = True
    label: Optional[str] = None


class ScannerRule(BaseModel):
    id: str = Field(default_factory=lambda: new_id("rule"))
    name: str
    description: str = ""
    enabled: bool = True
    exchange: str = "bitunix"
    source: str = "guardian"
    symbols: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    timeframes: List[str] = Field(default_factory=lambda: ["15m"])
    side_bias: Literal["long", "short", "auto", "both"] = "auto"
    min_score: float = 70.0
    tags: List[str] = Field(default_factory=list)
    action: Literal[
        "alert_only",
        "create_ticket",
        "create_guardian_plan",
        "signal_preview",
        "live_preview",
    ] = "create_guardian_plan"
    max_hits_per_run: int = 25
    conditions: List[ScannerCondition] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MarketContext(BaseModel):
    symbol: str
    timeframe: str = "15m"
    exchange: str = "bitunix"
    source: str = "guardian"
    candles: List[CandlePoint] = Field(default_factory=list)
    ticker: Dict[str, Any] = Field(default_factory=dict)
    orderbook: Dict[str, Any] = Field(default_factory=dict)
    edge: Dict[str, Any] = Field(default_factory=dict)
    funding_rate: Optional[float] = None
    open_interest: Optional[float] = None
    open_interest_prev: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConditionMatch(BaseModel):
    field: str
    op: str
    passed: bool
    required: bool = True
    weight: float = 1.0
    actual: Any = None
    expected: Any = None
    label: str = ""
    reason: str = ""


class SuggestedTicket(BaseModel):
    mode: Literal["spot", "futures"] = "futures"
    exchange: str = "bitunix"
    symbol: str
    side: Literal["buy", "sell", "long", "short"]
    order_type: Literal["market", "limit", "stop_limit", "stop_market"] = "limit"
    entry: float
    stop_loss: float
    take_profits: List[Dict[str, Any]] = Field(default_factory=list)
    risk_reward: Optional[float] = None
    leverage: Optional[float] = None
    margin_mode: Optional[str] = "cross"
    reduce_only_exits: bool = True
    trailing: Dict[str, Any] = Field(default_factory=dict)
    breakeven: Dict[str, Any] = Field(default_factory=dict)
    sizing: Dict[str, Any] = Field(default_factory=dict)
    invalidation: str = ""
    management: List[str] = Field(default_factory=list)
    route_hints: Dict[str, str] = Field(default_factory=dict)


class ScanHit(BaseModel):
    id: str = Field(default_factory=lambda: new_id("hit"))
    created_at: str = Field(default_factory=utc_now_iso)
    exchange: str = "bitunix"
    source: str = "guardian"
    symbol: str
    timeframe: str = "15m"
    rule_id: str
    rule_name: str
    side: Literal["long", "short", "neutral"] = "neutral"
    score: float = 0.0
    confidence: Literal["low", "medium", "high", "very_high"] = "low"
    price: float = 0.0
    trigger: str = ""
    reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    condition_results: List[ConditionMatch] = Field(default_factory=list)
    features: Dict[str, Any] = Field(default_factory=dict)
    suggested_ticket: Optional[SuggestedTicket] = None
    status: Literal["new", "reviewed", "promoted", "ignored"] = "new"




class TradeIntent(BaseModel):
    """Scanner-owned intent object between a ScanHit and Guardian execution planning.

    This is the hybrid boundary: the scanner declares what it found and what it
    wants to do next, while Guardian/signals/live-preview still validate account,
    venue, risk, position, and submit permissions.
    """

    id: str = Field(default_factory=lambda: new_id("intent"))
    created_at: str = Field(default_factory=utc_now_iso)
    source: str = "scanner"
    scan_hit_id: str
    account_id: Optional[str] = None
    exchange: str
    symbol: str
    timeframe: str
    side: Literal["long", "short", "neutral"]
    score: float = 0.0
    confidence: Literal["low", "medium", "high", "very_high"] = "low"
    setup_name: str = ""
    thesis: List[str] = Field(default_factory=list)
    cautions: List[str] = Field(default_factory=list)
    execution_mode: Literal["alert_only", "auto_build_plan", "require_approval", "live_autopilot"] = "require_approval"
    live_ready: bool = True
    entry: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profits: List[Dict[str, Any]] = Field(default_factory=list)
    risk_reward: Optional[float] = None
    invalidation: str = ""
    suggested_ticket: Optional[SuggestedTicket] = None
    feature_snapshot: Dict[str, Any] = Field(default_factory=dict)
    action_stack: List[str] = Field(default_factory=lambda: [
        "open_chart",
        "build_bracket",
        "guardian_plan",
        "signal_preview",
        "guardian_live_preview",
        "submit_through_existing_live_gate",
    ])
    route_hints: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ScannerRunRequest(BaseModel):
    exchange: str = "bitunix"
    source: str = "guardian"
    watchlist: List[str] = Field(default_factory=lambda: ["BTCUSDT", "ETHUSDT", "SOLUSDT"])
    timeframes: List[str] = Field(default_factory=lambda: ["15m"])
    preset_ids: List[str] = Field(default_factory=list)
    rules: List[ScannerRule] = Field(default_factory=list)
    candles_by_symbol: Dict[str, Any] = Field(default_factory=dict)
    ticker_by_symbol: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    orderbook_by_symbol: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    edge_by_symbol: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    max_hits: int = 100
    synthesize_missing: bool = True
    persist_hits: bool = True
    include_features: bool = True


class ScannerRunResponse(BaseModel):
    run_id: str = Field(default_factory=lambda: new_id("run"))
    created_at: str = Field(default_factory=utc_now_iso)
    exchange: str = "bitunix"
    source: str = "guardian"
    rules_evaluated: int = 0
    markets_evaluated: int = 0
    hits: List[ScanHit] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class SaveRuleRequest(BaseModel):
    rule: ScannerRule


class HitPromotionRequest(BaseModel):
    mode: Literal["ticket", "guardian_plan", "signal_preview", "live_preview"] = "ticket"
    account_id: Optional[str] = None
    risk_fraction: Optional[float] = None
    quantity: Optional[float] = None
    leverage: Optional[float] = None
    margin_mode: Optional[str] = None
    order_type: Optional[str] = None
    live_ready: bool = True
    notes: Optional[str] = None


class WebsocketSubscribeRequest(BaseModel):
    watchlist: List[str] = Field(default_factory=list)
    min_score: float = 0.0
    limit: int = 50


def model_dump_compat(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    if isinstance(model, dict):
        return dict(model)
    return dict(model.__dict__)


def candles_from_any(raw: Any) -> List[CandlePoint]:
    """Accept common candle shapes from Guardian/CCXT/CSV parsers."""
    if raw is None:
        return []
    if isinstance(raw, dict):
        if "candles" in raw:
            raw = raw["candles"]
        elif "data" in raw:
            raw = raw["data"]
        else:
            raw = list(raw.values())
    candles: List[CandlePoint] = []
    for item in raw or []:
        if isinstance(item, CandlePoint):
            candles.append(item)
        elif isinstance(item, dict):
            normalized = {
                "timestamp": item.get("timestamp") or item.get("time") or item.get("t") or item.get("date"),
                "open": float(item.get("open", item.get("o"))),
                "high": float(item.get("high", item.get("h"))),
                "low": float(item.get("low", item.get("l"))),
                "close": float(item.get("close", item.get("c"))),
                "volume": float(item.get("volume", item.get("v", 0.0)) or 0.0),
            }
            candles.append(CandlePoint(**normalized))
        elif isinstance(item, (list, tuple)) and len(item) >= 5:
            if len(item) >= 6:
                timestamp, open_, high, low, close, volume = item[:6]
            else:
                timestamp, open_, high, low, close, volume = None, *item[:5]
            candles.append(
                CandlePoint(
                    timestamp=timestamp,
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    volume=float(volume or 0.0),
                )
            )
    return candles
