from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from sentinel_chain.execution import ExecutionCostConfig


def positive_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        raise ValueError("price is required")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid price: {value}") from exc
    if parsed <= 0:
        raise ValueError("price must be positive")
    return parsed


def optional_positive_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal: {value}") from exc
    if parsed <= 0:
        raise ValueError("decimal value must be positive")
    return parsed


def optional_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid datetime: {value}") from exc


def truthy(value: Any) -> bool:
    if value is None or value == "":
        return False
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def non_negative_int(value: Any, *, default: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer: {value}") from exc
    if parsed < 0:
        raise ValueError("integer value must be non-negative")
    return parsed


def optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid integer: {value}") from exc


def non_negative_decimal(value: Any, *, default: Decimal) -> Decimal:
    if value is None or value == "":
        return default
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal: {value}") from exc
    if parsed < 0:
        raise ValueError("value must be non-negative")
    return parsed


def decimal_value(value: Any, *, default: Decimal) -> Decimal:
    if value is None or value == "":
        return default
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"invalid decimal: {value}") from exc


def candle_payload(value: Any) -> dict[str, Decimal]:
    if not isinstance(value, dict):
        raise ValueError("candles entries must be objects")
    high = positive_decimal(value.get("high"))
    low = positive_decimal(value.get("low"))
    if low > high:
        raise ValueError("candle low cannot exceed high")
    return {
        "label": value.get("label") or value.get("time") or value.get("timestamp"),
        "high": high,
        "low": low,
        "close": positive_decimal(value.get("close")),
    }


def stress_scenario_payload(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("scenario entries must be objects")
    marks_payload = value.get("prices") or value.get("marks") or []
    candles_payload = value.get("candles") or []
    if candles_payload and marks_payload:
        raise ValueError("scenario must send either prices or candles, not both")
    if candles_payload:
        if not isinstance(candles_payload, list):
            raise ValueError("scenario candles must be a list")
        path = {"candles": [candle_payload(candle) for candle in candles_payload]}
    else:
        if not isinstance(marks_payload, list) or not marks_payload:
            raise ValueError("scenario prices or candles must be a non-empty list")
        path = {"prices": [positive_decimal(price) for price in marks_payload]}
    costs_payload = value.get("costs") if isinstance(value.get("costs"), dict) else value
    return {
        "name": str(value.get("name") or value.get("label") or "scenario"),
        **path,
        "close_final_positions": truthy(value.get("close_final_positions") or value.get("force_close_final")),
        "costs": ExecutionCostConfig(
            fee_bps=non_negative_decimal(costs_payload.get("fee_bps"), default=Decimal("0")),
            slippage_bps=non_negative_decimal(costs_payload.get("slippage_bps"), default=Decimal("0")),
            funding_rate_bps=decimal_value(costs_payload.get("funding_rate_bps"), default=Decimal("0")),
            funding_periods_per_mark=non_negative_decimal(
                costs_payload.get("funding_periods_per_mark"),
                default=Decimal("0"),
            ),
        ),
    }


def batch_backtest_candidate_payload(
    value: dict[str, Any],
    *,
    base_signal: dict[str, Any],
    default_name: str,
    default_payload: dict[str, Any],
) -> dict[str, Any]:
    candidate_signal = value.get("signal") if isinstance(value.get("signal"), dict) else {}
    inline_signal = {
        key: item
        for key, item in value.items()
        if key
        not in {
            "name",
            "label",
            "signal",
            "prices",
            "marks",
            "candles",
            "costs",
            "close_final_positions",
            "force_close_final",
        }
    }
    signal_payload = {**base_signal, **inline_signal, **candidate_signal}
    if not signal_payload.get("symbol") and value.get("symbol"):
        signal_payload["symbol"] = value["symbol"]

    marks_payload = value.get("prices") or value.get("marks") or []
    candles_payload = value.get("candles") or []
    if candles_payload and marks_payload:
        raise ValueError("candidate must send either prices or candles, not both")
    if candles_payload:
        if not isinstance(candles_payload, list):
            raise ValueError("candidate candles must be a list")
        path = {"candles": [candle_payload(candle) for candle in candles_payload]}
    else:
        if not isinstance(marks_payload, list) or not marks_payload:
            raise ValueError("candidate prices or candles must be a non-empty list")
        path = {"prices": [positive_decimal(price) for price in marks_payload]}

    cost_payload = {**default_payload, **value}
    return {
        "name": str(value.get("name") or value.get("label") or signal_payload.get("symbol") or default_name),
        "signal": signal_payload,
        **path,
        "close_final_positions": truthy(
            value.get("close_final_positions")
            if "close_final_positions" in value
            else value.get("force_close_final")
            if "force_close_final" in value
            else default_payload.get("close_final_positions") or default_payload.get("force_close_final")
        ),
        "costs": execution_cost_payload(cost_payload),
    }


def execution_cost_payload(payload: dict[str, Any]) -> ExecutionCostConfig:
    costs = payload.get("costs") if isinstance(payload.get("costs"), dict) else {}
    fee_bps = costs.get("fee_bps") if costs else payload.get("fee_bps")
    slippage_bps = costs.get("slippage_bps") if costs else payload.get("slippage_bps")
    funding_rate_bps = costs.get("funding_rate_bps") if costs else payload.get("funding_rate_bps")
    funding_periods_per_mark = (
        costs.get("funding_periods_per_mark") if costs else payload.get("funding_periods_per_mark")
    )
    return ExecutionCostConfig(
        fee_bps=non_negative_decimal(fee_bps, default=Decimal("0")),
        slippage_bps=non_negative_decimal(slippage_bps, default=Decimal("0")),
        funding_rate_bps=decimal_value(funding_rate_bps, default=Decimal("0")),
        funding_periods_per_mark=non_negative_decimal(funding_periods_per_mark, default=Decimal("0")),
    )


def bitunix_kline_query(payload: dict[str, Any]) -> dict[str, Any]:
    market_data = payload.get("market_data") if isinstance(payload.get("market_data"), dict) else {}
    symbol = str(payload.get("symbol") or market_data.get("symbol") or "").strip().upper()
    if not symbol:
        signal = payload.get("signal") if isinstance(payload.get("signal"), dict) else {}
        symbol = str(signal.get("symbol") or "").strip().upper().replace("/", "")
    interval = str(payload.get("interval") or market_data.get("interval") or "").strip()
    if not symbol:
        raise ValueError("Bitunix kline symbol is required")
    if not interval:
        raise ValueError("Bitunix kline interval is required")
    limit = payload.get("limit") if payload.get("limit") is not None else market_data.get("limit")
    query: dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "start_time": optional_int(payload.get("start_time") or market_data.get("start_time")),
        "end_time": optional_int(payload.get("end_time") or market_data.get("end_time")),
        "limit": optional_int(limit),
        "price_type": payload.get("price_type") or market_data.get("price_type") or payload.get("type"),
    }
    if query["limit"] is not None and (query["limit"] <= 0 or query["limit"] > 200):
        raise ValueError("Bitunix kline limit must be between 1 and 200")
    return query
