from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from typing import Any

from .config import (
    LIVE_TRADING_CONFIRMATION,
    LIVE_TRADING_CONFIRMATION_ENV,
    REQUIRE_APPROVAL_ENV,
    WEBHOOK_SECRET_ENV,
    live_readiness_requirements_satisfied,
)
from .exchanges.bitunix_adapter import bitunix_credentials_configured, bitunix_live_execution_enabled
from .execution import build_exit_orders
from .risk import RiskDecision
from .signals import CryptoSignal

LIVE_ORDER_CONFIRMATION = "PLACE LIVE ORDER"
BITUNIX_EXCHANGE_ID = "bitunix"
BITUNIX_MAX_CONFIGURABLE_LEVERAGE = 200
BITUNIX_CHANGE_LEVERAGE_ENDPOINT = "/api/v1/futures/account/change_leverage"


@dataclass(frozen=True)
class LiveOrderPreview:
    exchange_id: str
    signal_id: str
    live_order_safe: bool
    reason_codes: tuple[str, ...]
    warnings: tuple[str, ...]
    order_payload: dict[str, Any] | None
    leverage_setting: dict[str, Any] | None = None
    confirmation_phrase: str = LIVE_ORDER_CONFIRMATION

    def to_dict(self) -> dict[str, Any]:
        return {
            "exchange_id": self.exchange_id,
            "signal_id": self.signal_id,
            "live_order_safe": self.live_order_safe,
            "reason_codes": list(self.reason_codes),
            "warnings": list(self.warnings),
            "order_payload": self.order_payload,
            "leverage_setting": self.leverage_setting,
            "confirmation_phrase": self.confirmation_phrase,
        }


def live_execution_status_payload() -> dict[str, Any]:
    """Return redacted live-execution readiness status for the operator UI."""
    readiness = live_readiness_requirements_satisfied()
    return {
        "default_live_confirmation_env": LIVE_TRADING_CONFIRMATION_ENV,
        "required_live_confirmation_value": LIVE_TRADING_CONFIRMATION,
        "manual_order_confirmation_phrase": LIVE_ORDER_CONFIRMATION,
        "readiness_satisfied": readiness,
        "approval_mode_required_env": REQUIRE_APPROVAL_ENV,
        "webhook_secret_required_env": WEBHOOK_SECRET_ENV,
        "bitunix": {
            "credentials_configured": bitunix_credentials_configured(),
            "live_execution_enabled": bitunix_live_execution_enabled(),
            "driver": "bitunix-native-futures",
            "place_order_endpoint": "/api/v1/futures/trade/place_order",
            "change_leverage_endpoint": BITUNIX_CHANGE_LEVERAGE_ENDPOINT,
            "max_configurable_leverage": BITUNIX_MAX_CONFIGURABLE_LEVERAGE,
        },
        "safety_model": {
            "default": "locked",
            "requires_operator_session": True,
            "requires_preview_ticket": True,
            "requires_manual_confirmation": LIVE_ORDER_CONFIRMATION,
            "requires_risk_approval": True,
            "stores_audit_event": True,
        },
    }


def bitunix_live_order_preview(
    signal: CryptoSignal,
    decision: RiskDecision,
    *,
    engine_halted: bool = False,
    runtime_blocked: bool = False,
) -> LiveOrderPreview:
    """Map a normalized Sentinel signal into a Bitunix futures order preview.

    The result is executable only for a conservative single-entry futures order
    with optional native TP/SL. Staged targets, trailing exits, and synthetic
    time exits stay paper/managed because they require orchestration beyond a
    single native Bitunix order.
    """
    warnings: list[str] = []
    reasons: list[str] = []
    if signal.exchange != BITUNIX_EXCHANGE_ID:
        reasons.append("exchange_not_bitunix")
    if signal.market_type not in {"future", "futures", "perp", "perpetual", "swap"}:
        reasons.append("market_type_not_futures")
    if engine_halted:
        reasons.append("engine_halted")
    if runtime_blocked:
        reasons.append("runtime_controls_blocked")
    if not decision.approved:
        reasons.extend(str(code) for code in decision.reason_codes or ["risk_rejected"])
    if not bitunix_live_execution_enabled():
        reasons.append("bitunix_live_execution_disabled")
    if not bitunix_credentials_configured():
        reasons.append("bitunix_credentials_missing")

    order_payload: dict[str, Any] | None = None
    leverage_setting: dict[str, Any] | None = None
    try:
        order_payload, payload_warnings = build_bitunix_futures_order_payload(signal, decision)
        warnings.extend(payload_warnings)
    except ValueError as exc:
        reasons.append(str(exc))
    try:
        leverage_setting = build_bitunix_futures_leverage_setting(signal)
    except ValueError as exc:
        reasons.append(str(exc))

    # Stop if the mapping relies on Sentinel's paper/synthetic bracket engine.
    if "staged_take_profit_requires_manager" in warnings:
        reasons.append("staged_take_profit_not_native_live_safe")
    if "partial_take_profit_requires_manager" in warnings:
        reasons.append("partial_take_profit_not_native_live_safe")
    if "trailing_stop_requires_manager" in warnings:
        reasons.append("trailing_stop_not_native_live_safe")
    if "time_exit_requires_manager" in warnings:
        reasons.append("time_exit_not_native_live_safe")

    return LiveOrderPreview(
        exchange_id=BITUNIX_EXCHANGE_ID,
        signal_id=signal.signal_id,
        live_order_safe=not reasons and order_payload is not None,
        reason_codes=tuple(dict.fromkeys(reasons)),
        warnings=tuple(dict.fromkeys(warnings)),
        order_payload=order_payload,
        leverage_setting=leverage_setting,
    )


def build_bitunix_futures_order_payload(signal: CryptoSignal, decision: RiskDecision) -> tuple[dict[str, Any], list[str]]:
    if decision.order_notional is None and signal.base_amount is None:
        raise ValueError("approved_notional_or_base_quantity_required")
    if signal.quote_amount is not None and signal.price is None and signal.base_amount is None:
        raise ValueError("entry_price_required_to_convert_quote_amount")

    warnings: list[str] = []
    qty = signal.base_amount or _quantity_from_notional(decision.order_notional or signal.quote_amount, signal.price)
    if qty is None or qty <= 0:
        raise ValueError("positive_base_quantity_required")

    order_type = "LIMIT" if signal.price is not None else "MARKET"
    payload: dict[str, Any] = {
        "symbol": signal.symbol.replace("/", ""),
        "qty": _plain(qty),
        "side": "BUY" if signal.side == "buy" else "SELL",
        "tradeSide": "CLOSE" if signal.reduce_only else "OPEN",
        "orderType": order_type,
        "clientId": _client_id(signal.signal_id),
        "reduceOnly": bool(signal.reduce_only),
    }
    if order_type == "LIMIT":
        payload["price"] = _plain(signal.price)  # type: ignore[arg-type]
        payload["effect"] = "GTC"

    exit_orders = build_exit_orders(signal)
    take_profit_exits = [exit_order for exit_order in exit_orders if exit_order.kind == "take_profit"]
    stop_exits = [exit_order for exit_order in exit_orders if exit_order.kind == "stop_loss"]
    trailing_exits = [exit_order for exit_order in exit_orders if exit_order.kind == "trailing_stop"]
    time_exits = [exit_order for exit_order in exit_orders if exit_order.kind == "time_exit"]

    if trailing_exits:
        warnings.append("trailing_stop_requires_manager")
    if time_exits:
        warnings.append("time_exit_requires_manager")
    if len(take_profit_exits) > 1:
        warnings.append("staged_take_profit_requires_manager")
    if any(exit_order.close_pct < Decimal("100") for exit_order in take_profit_exits):
        warnings.append("partial_take_profit_requires_manager")

    if stop_exits:
        stop = stop_exits[0]
        payload.update(
            {
                "slPrice": _plain(stop.trigger_price),
                "slStopType": "MARK_PRICE",
                "slOrderType": "MARKET",
            }
        )
    if take_profit_exits:
        target = take_profit_exits[0]
        payload.update(
            {
                "tpPrice": _plain(target.trigger_price),
                "tpStopType": "MARK_PRICE",
                "tpOrderType": "MARKET",
            }
        )
    return payload, warnings


def build_bitunix_futures_leverage_setting(signal: CryptoSignal) -> dict[str, Any] | None:
    if signal.reduce_only:
        return None
    if signal.market_type not in {"future", "futures", "perp", "perpetual", "swap"}:
        return None
    leverage = signal.leverage
    if leverage != leverage.to_integral_value():
        raise ValueError("bitunix_leverage_must_be_integer")
    leverage_int = int(leverage)
    if leverage_int < 1 or leverage_int > BITUNIX_MAX_CONFIGURABLE_LEVERAGE:
        raise ValueError("bitunix_leverage_out_of_supported_range")
    return {
        "endpoint": BITUNIX_CHANGE_LEVERAGE_ENDPOINT,
        "marginCoin": "USDT",
        "symbol": signal.symbol.replace("/", "").upper(),
        "leverage": leverage_int,
    }


def _quantity_from_notional(notional: Decimal | None, price: Decimal | None) -> Decimal | None:
    if notional is None or price is None or price <= 0:
        return None
    return (notional / price).quantize(Decimal("0.00000001"), rounding=ROUND_DOWN)


def _plain(value: Decimal) -> str:
    normalized = value.normalize()
    text = format(normalized, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _client_id(signal_id: str) -> str:
    raw = re.sub(r"[^A-Za-z0-9_-]", "", signal_id)
    if not raw:
        raw = "manual"
    # Leave room for the sc- prefix and keep the identifier exchange-friendly.
    return f"sc-{raw[:28]}"
