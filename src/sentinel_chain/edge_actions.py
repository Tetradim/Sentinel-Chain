from __future__ import annotations

from typing import Any

from .bot_event_bus import BotEvent, publish_event
from .engine import TradingEngine
from .repository import SQLiteRepository


HALTING_EDGE_ACTIONS = {
    "stop_buying",
    "stop_all",
    "emergency_exit",
    "downtrend_warning",
    "market_downtrend_warning",
}


def apply_edge_action(
    *,
    event: BotEvent,
    engine: TradingEngine,
    repository: SQLiteRepository | None = None,
) -> dict[str, Any]:
    payload = event.payload or {}
    action = str(payload.get("action") or "").strip().lower()
    symbol = str(payload.get("symbol") or "GLOBAL").strip().upper() or "GLOBAL"
    reason = str(payload.get("reason") or f"Edge action: {action}").strip()

    if action in HALTING_EDGE_ACTIONS:
        halt_reason = f"edge:{action}:{symbol}:{reason}"
        engine.halt(halt_reason)
        result = {
            "status": "applied",
            "effect": "halted_new_orders",
            "halted": True,
            "reason": halt_reason,
            "action": action,
            "symbol": symbol,
            "event_id": event.event_id,
        }
    else:
        result = {
            "status": "ignored",
            "effect": "no_auto_crypto_mapping",
            "halted": engine.halted,
            "reason": f"no Sentinel Chain mapping for Edge action: {action}",
            "action": action,
            "symbol": symbol,
            "event_id": event.event_id,
        }

    if repository:
        repository.record_audit(
            "edge.action.received",
            {
                "event_id": event.event_id,
                "action": action,
                "symbol": symbol,
                "status": result["status"],
                "effect": result["effect"],
                "reason": result["reason"],
            },
        )

    publish_event(
        "auto_crypto.edge_action.applied",
        payload=result,
        correlation_id=event.correlation_id or event.event_id,
        dedupe_key=f"sentinel-chain:{event.event_id}:{result['status']}",
        target_bots=["sentinel-edge", "openclaw"],
        trace={"source_event_id": event.event_id},
    )
    return result
