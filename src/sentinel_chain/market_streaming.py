from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping
from decimal import Decimal, InvalidOperation
from typing import Any

BITUNIX_PUBLIC_WS_URL = "wss://fapi.bitunix.com/public"

_INTERVAL_TO_CHANNEL = {
    "1m": "1min",
    "3m": "3min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "60min",
    "2h": "2h",
    "4h": "4h",
    "6h": "6h",
    "8h": "8h",
    "12h": "12h",
    "1d": "1day",
    "3d": "3day",
    "1w": "1week",
    "1M": "1month",
    "1month": "1month",
}


def bitunix_kline_channel(interval: str, *, price_type: str = "market") -> str:
    normalized_interval = _INTERVAL_TO_CHANNEL.get(interval, interval)
    normalized_price_type = "mark" if str(price_type).lower() in {"mark", "marked", "mark_price", "mark-price", "markprice"} else "market"
    return f"{normalized_price_type}_kline_{normalized_interval}"


def normalize_bitunix_ws_kline_message(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    data = payload.get("data")
    if not isinstance(data, Mapping):
        return None
    candle = _normalize_ohlcv(data)
    if candle is None:
        return None
    if not candle.get("time") and payload.get("ts") is not None:
        candle["time"] = str(payload.get("ts"))
    return {
        "event": "candle",
        "source": "bitunix_ws",
        "symbol": payload.get("symbol"),
        "channel": payload.get("ch"),
        "timestamp": payload.get("ts"),
        "candle": candle,
        "raw": dict(payload),
    }


def normalize_bitunix_rest_candles(candles: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for candle in candles:
        item = _normalize_ohlcv(candle)
        if item is not None:
            label = candle.get("label") or candle.get("time") or candle.get("timestamp") or candle.get("open_time")
            if label is not None:
                item["time"] = str(label)
            normalized.append(item)
    return normalized


async def bitunix_ws_candles(
    *,
    symbol: str,
    interval: str,
    price_type: str = "market",
    ws_url: str = BITUNIX_PUBLIC_WS_URL,
) -> AsyncIterator[dict[str, Any]]:
    try:
        import websockets  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on optional runtime package.
        raise RuntimeError("websockets package is required for upstream Bitunix streaming") from exc

    channel = bitunix_kline_channel(interval, price_type=price_type)
    subscribe = {"op": "subscribe", "args": [{"symbol": symbol.upper(), "ch": channel}]}
    async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as upstream:
        await upstream.send(json.dumps(subscribe))
        async for raw in upstream:
            try:
                payload = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                continue
            if not isinstance(payload, Mapping):
                continue
            normalized = normalize_bitunix_ws_kline_message(payload)
            if normalized is not None:
                yield normalized


def _normalize_ohlcv(item: Mapping[str, Any]) -> dict[str, Any] | None:
    try:
        open_price = _decimal_any(item.get("o") or item.get("open"))
        high = _decimal_any(item.get("h") or item.get("high"))
        low = _decimal_any(item.get("l") or item.get("low"))
        close = _decimal_any(item.get("c") or item.get("close"))
        volume = _decimal_any(item.get("b") or item.get("volume") or item.get("baseVolume") or 0, allow_zero=True)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if min(open_price, high, low, close) <= 0 or low > high:
        return None
    return {
        "time": str(item.get("time") or item.get("timestamp") or item.get("t") or ""),
        "open": float(open_price),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "volume": float(volume),
    }


def _decimal_any(value: Any, *, allow_zero: bool = False) -> Decimal:
    if value in (None, ""):
        raise ValueError("missing decimal value")
    parsed = Decimal(str(value))
    if parsed < 0 or (parsed == 0 and not allow_zero):
        raise ValueError("decimal value must be positive")
    return parsed
