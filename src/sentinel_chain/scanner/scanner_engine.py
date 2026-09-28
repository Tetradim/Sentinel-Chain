"""Scanner engine that evaluates rules across symbols/timeframes.

The engine is deliberately not an order router. It produces ScanHit objects and
promotion payloads for Guardian/signals/live-preview routes.
"""
from __future__ import annotations

import math
import random
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .scanner_models import (
    CandlePoint,
    MarketContext,
    ScanHit,
    ScannerCondition,
    ScannerRule,
    ScannerRunRequest,
    ScannerRunResponse,
    TradeIntent,
    candles_from_any,
    model_dump_compat,
)
from .scanner_rules import evaluate_rule, preset_rules


def _normalize_symbol(symbol: str) -> str:
    return symbol.replace("/", "").replace("-PERP", "").upper().strip()


def _get_nested_candles(raw: Dict[str, Any], symbol: str, timeframe: str) -> List[CandlePoint]:
    """Accept flexible candle maps from the Guardian or the frontend.

    Supported shapes:
      candles_by_symbol["BTCUSDT"]["15m"] = [...]
      candles_by_symbol["BTCUSDT"] = [...]
      candles_by_symbol["BTC/USDT"] = {"candles": [...]}
      candles_by_symbol["BTCUSDT:15m"] = [...]
    """
    if not raw:
        return []
    keys = [symbol, _normalize_symbol(symbol), symbol.replace("USDT", "/USDT"), f"{symbol}:{timeframe}", f"{_normalize_symbol(symbol)}:{timeframe}"]
    for key in keys:
        if key in raw:
            value = raw[key]
            if isinstance(value, dict) and timeframe in value:
                return candles_from_any(value[timeframe])
            return candles_from_any(value)
    # Case-insensitive fallback.
    wanted = {_normalize_symbol(k) for k in keys}
    for key, value in raw.items():
        if _normalize_symbol(str(key).split(":", 1)[0]) in wanted:
            if isinstance(value, dict) and timeframe in value:
                return candles_from_any(value[timeframe])
            return candles_from_any(value)
    return []


def synthesize_candles(symbol: str, timeframe: str, n: int = 160) -> List[CandlePoint]:
    """Deterministic-enough demo candles so the scanner UI works before wiring feeds."""
    seed = sum(ord(ch) for ch in symbol + timeframe)
    rng = random.Random(seed)
    base = 60000.0 if "BTC" in symbol.upper() else 3200.0 if "ETH" in symbol.upper() else 120.0
    price = base * (0.92 + rng.random() * 0.18)
    candles: List[CandlePoint] = []
    trend = rng.choice([-0.0004, 0.0002, 0.0006, 0.001])
    squeeze_start = int(n * 0.65)
    for i in range(n):
        compression = 1.0
        if i > squeeze_start:
            compression = max(0.28, 1.0 - (i - squeeze_start) / max(1, n - squeeze_start) * 0.7)
        drift = trend + math.sin(i / 12.0) * 0.001
        shock = rng.gauss(0, 0.004 * compression)
        open_ = price
        close = max(0.0001, open_ * (1.0 + drift + shock))
        range_pct = abs(rng.gauss(0.006, 0.002)) * compression + 0.0015
        high = max(open_, close) * (1.0 + range_pct * rng.uniform(0.35, 1.0))
        low = min(open_, close) * (1.0 - range_pct * rng.uniform(0.35, 1.0))
        volume_base = 1000.0 + rng.random() * 500.0
        volume = volume_base * (1.0 + abs(shock) * 80.0)
        # Force occasional breakout/rejection setups for demos.
        if i == n - 2 and seed % 3 == 0:
            close = max(close, max(c.high for c in candles[-25:]) * 1.002) if candles else close
            high = max(high, close * 1.003)
            volume *= 2.4
        elif i == n - 1 and seed % 4 == 0:
            high = max(high, max(c.high for c in candles[-25:]) * 1.006) if candles else high
            close = open_ * 0.998
            low = min(low, close * 0.997)
            volume *= 1.8
        candles.append(CandlePoint(timestamp=i, open=open_, high=high, low=low, close=close, volume=volume))
        price = close
    return candles


class ScannerEngine:
    def __init__(self, store: Any = None):
        self.store = store

    def build_rules(self, request: ScannerRunRequest) -> List[Any]:
        presets = {rule.id: rule for rule in preset_rules()}
        rules = []
        if request.preset_ids:
            for preset_id in request.preset_ids:
                if preset_id == "*":
                    rules.extend(presets.values())
                elif preset_id in presets:
                    rules.append(presets[preset_id])
        # No preset selected means evaluate every preset plus saved rules.
        if not request.preset_ids and not request.rules:
            rules.extend(presets.values())
        if request.rules:
            rules.extend(request.rules)
        if self.store is not None:
            try:
                rules.extend(self.store.list_rules(enabled_only=True))
            except Exception:
                pass
        # De-duplicate by id while preserving order; request-provided rules win.
        seen = set()
        unique = []
        for rule in rules:
            if rule.id in seen:
                continue
            seen.add(rule.id)
            unique.append(rule)
        return unique

    def context_for(self, request: ScannerRunRequest, symbol: str, timeframe: str) -> MarketContext:
        candles = _get_nested_candles(request.candles_by_symbol, symbol, timeframe)
        if not candles and request.synthesize_missing:
            candles = synthesize_candles(symbol, timeframe)
        ticker = request.ticker_by_symbol.get(symbol) or request.ticker_by_symbol.get(_normalize_symbol(symbol)) or {}
        orderbook = request.orderbook_by_symbol.get(symbol) or request.orderbook_by_symbol.get(_normalize_symbol(symbol)) or {}
        edge = request.edge_by_symbol.get(symbol) or request.edge_by_symbol.get(_normalize_symbol(symbol)) or {}
        funding = edge.get("funding_rate") if isinstance(edge, dict) else None
        oi = edge.get("open_interest") if isinstance(edge, dict) else None
        oi_prev = edge.get("open_interest_prev") if isinstance(edge, dict) else None
        return MarketContext(
            symbol=_normalize_symbol(symbol),
            timeframe=timeframe,
            exchange=request.exchange,
            source=request.source,
            candles=candles,
            ticker=ticker,
            orderbook=orderbook,
            edge=edge,
            funding_rate=funding,
            open_interest=oi,
            open_interest_prev=oi_prev,
        )

    def run(self, request: ScannerRunRequest) -> ScannerRunResponse:
        response = ScannerRunResponse(exchange=request.exchange, source=request.source)
        rules = self.build_rules(request)
        response.rules_evaluated = len(rules)
        hits: List[ScanHit] = []

        symbols = [_normalize_symbol(s) for s in request.watchlist if str(s).strip()]
        timeframes = request.timeframes or ["15m"]
        for symbol in symbols:
            for timeframe in timeframes:
                context = self.context_for(request, symbol, timeframe)
                if len(context.candles) < 2:
                    response.warnings.append(f"{symbol} {timeframe}: no candles available")
                    continue
                response.markets_evaluated += 1
                for rule in rules:
                    # Rule-level symbol/timeframe overrides are respected, but scanner request can narrow universe.
                    try:
                        hit = evaluate_rule(rule, context)
                    except Exception as exc:
                        response.warnings.append(f"{symbol} {timeframe} {rule.name}: {exc}")
                        continue
                    if hit is not None:
                        if not request.include_features:
                            hit.features = {}
                        hits.append(hit)

        if not hits and _is_synthetic_demo_request(request) and symbols:
            demo_hit = self._demo_hit(request, symbols[0], timeframes[0])
            if demo_hit is not None:
                hits.append(demo_hit)
                response.warnings.append("demo_fallback_hit_added")

        hits.sort(key=lambda h: (h.score, h.created_at), reverse=True)
        response.hits = hits[: max(1, request.max_hits)]
        if request.persist_hits and self.store is not None:
            for hit in response.hits:
                try:
                    self.store.add_hit(hit)
                except Exception as exc:
                    response.warnings.append(f"store add hit failed: {exc}")
        return response

    def _demo_hit(self, request: ScannerRunRequest, symbol: str, timeframe: str) -> ScanHit | None:
        """Create one deterministic demo hit when synthetic presets are too quiet.

        This path only runs for the bundled demo mode. If callers provide real
        candles/tickers/orderbook/Edge maps, no fallback hit is added.
        """
        context = self.context_for(request, symbol, timeframe)
        if len(context.candles) < 2:
            return None
        rule = ScannerRule(
            id="demo_scanner_smoke_positive_close",
            name="Demo Scanner Smoke Hit",
            description="Synthetic demo fallback so the scanner cockpit can be tested immediately.",
            symbols=[symbol],
            timeframes=[timeframe],
            side_bias="long",
            min_score=1,
            tags=["demo", "smoke"],
            action="create_guardian_plan",
            conditions=[
                ScannerCondition(
                    field="close",
                    op=">",
                    value=0,
                    weight=1,
                    required=True,
                    label="demo candle close is valid",
                )
            ],
            metadata={"demo_fallback": True},
        )
        hit = evaluate_rule(rule, context)
        if hit is not None:
            hit.warnings.append("synthetic_demo_fallback")
            hit.reasons.append("Synthetic demo fallback added because selected presets produced no matches.")
        return hit


def _is_synthetic_demo_request(request: ScannerRunRequest) -> bool:
    return (
        request.synthesize_missing
        and not request.candles_by_symbol
        and not request.ticker_by_symbol
        and not request.orderbook_by_symbol
        and not request.edge_by_symbol
    )


def build_guardian_plan_payload(hit: ScanHit, account_id: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ticket = hit.suggested_ticket
    payload: Dict[str, Any] = {
        "source": "scanner",
        "hit_id": hit.id,
        "account_id": account_id,
        "exchange": hit.exchange,
        "symbol": hit.symbol,
        "timeframe": hit.timeframe,
        "side": hit.side,
        "score": hit.score,
        "confidence": hit.confidence,
        "trigger": hit.trigger,
        "why": hit.reasons,
        "warnings": hit.warnings,
        "route_intent": "guardian_plan",
        "live_ready": True,
        "execution_note": "Scanner generated this plan; Guardian/signals/live-preview should perform risk, account, position, and exchange validation before any live submission.",
    }
    if ticket is not None:
        payload["ticket"] = model_dump_compat(ticket)
        payload.update(
            {
                "entry": ticket.entry,
                "stop_loss": ticket.stop_loss,
                "take_profits": ticket.take_profits,
                "order_type": ticket.order_type,
                "leverage": ticket.leverage,
                "margin_mode": ticket.margin_mode,
                "reduce_only_exits": ticket.reduce_only_exits,
            }
        )
    if overrides:
        payload["overrides"] = overrides
    return payload


def build_trade_intent_payload(hit: ScanHit, account_id: Optional[str] = None, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the scanner-owned intent object before Guardian creates an order plan."""
    ticket = hit.suggested_ticket
    route_hints = {
        "scanner_hit": f"/scanner/hits/{hit.id}",
        "chart": "/war-room/ui",
        "ticket": f"/scanner/hits/{hit.id}/ticket",
        "guardian_plan": f"/scanner/hits/{hit.id}/guardian-plan",
        "signal_preview": f"/scanner/hits/{hit.id}/signal-preview",
        "guardian_live_preview": f"/scanner/hits/{hit.id}/live-preview",
        "submit": "/signals/submit",
    }
    mode = "require_approval"
    if overrides and overrides.get("execution_mode") in {"alert_only", "auto_build_plan", "require_approval", "live_autopilot"}:
        mode = str(overrides["execution_mode"])
    feature_keys = [
        "close", "volume_ratio", "atr_pct", "vwap", "support", "resistance",
        "breakout_above_resistance", "support_break", "rejection_at_resistance",
        "rejection_at_support", "vcp_score", "spread_pct", "funding_rate",
        "open_interest_change_pct", "bid_ask_imbalance", "volume_profile_poc",
    ]
    snapshot = {k: hit.features.get(k) for k in feature_keys if k in hit.features}
    intent = TradeIntent(
        scan_hit_id=hit.id,
        account_id=account_id,
        exchange=hit.exchange,
        symbol=hit.symbol,
        timeframe=hit.timeframe,
        side=hit.side,
        score=hit.score,
        confidence=hit.confidence,
        setup_name=hit.rule_name,
        thesis=hit.reasons,
        cautions=hit.warnings,
        execution_mode=mode,
        live_ready=True,
        entry=ticket.entry if ticket else hit.price,
        stop_loss=ticket.stop_loss if ticket else None,
        take_profits=ticket.take_profits if ticket else [],
        risk_reward=ticket.risk_reward if ticket else None,
        invalidation=ticket.invalidation if ticket else "",
        suggested_ticket=ticket,
        feature_snapshot=snapshot,
        route_hints=route_hints,
        metadata={
            "trigger": hit.trigger,
            "scanner_role": "discovery_and_intent_layer",
            "execution_owner": "Guardian/signals/live-preview",
        },
    )
    payload = model_dump_compat(intent)
    if overrides:
        payload["overrides"] = overrides
    return payload


def build_chart_review_payload(hit: ScanHit) -> Dict[str, Any]:
    """Return a compact War Room/Guardian chart payload for Send to Chart."""
    f = hit.features or {}
    return {
        "source": "scanner",
        "hit_id": hit.id,
        "symbol": hit.symbol,
        "timeframe": hit.timeframe,
        "exchange": hit.exchange,
        "side": hit.side,
        "score": hit.score,
        "trigger": hit.trigger,
        "candles": f.get("chart_candles", []),
        "overlays": {
            "support": f.get("support"),
            "resistance": f.get("resistance"),
            "vwap": f.get("vwap"),
            "volume_profile_poc": f.get("volume_profile_poc"),
            "support_levels": f.get("support_levels", []),
            "resistance_levels": f.get("resistance_levels", []),
            "entry": getattr(hit.suggested_ticket, "entry", None) if hit.suggested_ticket else None,
            "stop_loss": getattr(hit.suggested_ticket, "stop_loss", None) if hit.suggested_ticket else None,
            "take_profits": getattr(hit.suggested_ticket, "take_profits", []) if hit.suggested_ticket else [],
        },
        "why": hit.reasons,
        "warnings": hit.warnings,
        "target_route": "/war-room/ui",
    }
