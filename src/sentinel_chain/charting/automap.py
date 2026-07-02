"""Sentinel Chain chart auto-mapping and confluence engine.

This module is deliberately dependency-light so it can be dropped into the
existing paper-first Sentinel Chain FastAPI application without requiring numpy,
pandas, talib, browser build tooling, or a websocket feed.  It accepts plain
OHLCV candles and returns overlay-ready JSON for the War Room UI:

* adaptive pivot highs/lows
* support/resistance clusters
* Hough-style trend lines and channels
* volume profile, point of control, and high/low-volume nodes
* Fibonacci map
* FVG/imbalance zones
* simple order-block zones
* candlestick, structure, divergence, compression, and base-pattern signals
* long/short confluence scoring with trade plan, invalidation, and reasons
* a small deterministic demo-feed generator for offline UI testing

The calculations are decision-support heuristics. They are not financial advice,
and live execution remains controlled by Sentinel Chain's normal risk gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt
from random import Random
from statistics import mean, median
from typing import Any, Iterable, Mapping, Sequence

Number = float | int


@dataclass(frozen=True)
class NormalizedCandle:
    time: str | int | float
    open: float
    high: float
    low: float
    close: float
    volume: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "time": self.time,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if isfinite(parsed) else default


def _round(value: Any, digits: int = 8) -> float | None:
    parsed = _to_float(value, float("nan"))
    if not isfinite(parsed):
        return None
    return round(parsed, digits)


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    if not denominator or not isfinite(denominator):
        return default
    return numerator / denominator


def _percent_change(current: float, reference: float) -> float:
    return _safe_div(current - reference, reference) * 100.0


def _compact_symbol(symbol: str) -> str:
    return str(symbol or "BTCUSDT").replace("/", "").replace("-", "").replace("_", "").upper()


def normalize_candles(candles: Sequence[Mapping[str, Any]] | None) -> list[NormalizedCandle]:
    normalized: list[NormalizedCandle] = []
    for index, candle in enumerate(candles or []):
        if not isinstance(candle, Mapping):
            continue
        open_price = _to_float(candle.get("open", candle.get("o")), float("nan"))
        high = _to_float(candle.get("high", candle.get("h")), float("nan"))
        low = _to_float(candle.get("low", candle.get("l")), float("nan"))
        close = _to_float(candle.get("close", candle.get("c")), float("nan"))
        volume = _to_float(candle.get("volume", candle.get("v", 0.0)), 0.0)
        if not all(isfinite(value) for value in (open_price, high, low, close)):
            continue
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        time_value = candle.get("time", candle.get("timestamp", candle.get("t", index)))
        normalized.append(NormalizedCandle(time_value, open_price, high, low, close, max(0.0, volume)))
    return normalized


def _series(candles: Sequence[NormalizedCandle], field: str) -> list[float]:
    return [float(getattr(candle, field)) for candle in candles]


def sma(values: Sequence[float], period: int) -> list[float | None]:
    if period <= 0:
        return [None for _ in values]
    result: list[float | None] = []
    rolling = 0.0
    queue: list[float] = []
    for value in values:
        queue.append(value)
        rolling += value
        if len(queue) > period:
            rolling -= queue.pop(0)
        result.append(rolling / period if len(queue) == period else None)
    return result


def ema(values: Sequence[float], period: int) -> list[float | None]:
    if period <= 0:
        return [None for _ in values]
    result: list[float | None] = []
    multiplier = 2.0 / (period + 1.0)
    previous: float | None = None
    seed: list[float] = []
    for value in values:
        if previous is None:
            seed.append(value)
            if len(seed) < period:
                result.append(None)
                continue
            previous = sum(seed[-period:]) / period
            result.append(previous)
            continue
        previous = ((value - previous) * multiplier) + previous
        result.append(previous)
    return result


def true_range(candles: Sequence[NormalizedCandle]) -> list[float]:
    ranges: list[float] = []
    previous_close: float | None = None
    for candle in candles:
        if previous_close is None:
            ranges.append(candle.high - candle.low)
        else:
            ranges.append(max(candle.high - candle.low, abs(candle.high - previous_close), abs(candle.low - previous_close)))
        previous_close = candle.close
    return ranges


def atr(candles: Sequence[NormalizedCandle], period: int = 14) -> list[float | None]:
    ranges = true_range(candles)
    if not ranges:
        return []
    result: list[float | None] = []
    previous: float | None = None
    for index, value in enumerate(ranges):
        if index + 1 < period:
            result.append(None)
            continue
        if previous is None:
            previous = sum(ranges[index + 1 - period : index + 1]) / period
        else:
            previous = ((previous * (period - 1)) + value) / period
        result.append(previous)
    return result


def rsi(values: Sequence[float], period: int = 14) -> list[float | None]:
    if len(values) < 2 or period <= 0:
        return [None for _ in values]
    result: list[float | None] = [None]
    gains: list[float] = []
    losses: list[float] = []
    avg_gain: float | None = None
    avg_loss: float | None = None
    for index in range(1, len(values)):
        delta = values[index] - values[index - 1]
        gains.append(max(0.0, delta))
        losses.append(max(0.0, -delta))
        if index < period:
            result.append(None)
            continue
        if avg_gain is None or avg_loss is None:
            avg_gain = sum(gains[-period:]) / period
            avg_loss = sum(losses[-period:]) / period
        else:
            avg_gain = ((avg_gain * (period - 1)) + gains[-1]) / period
            avg_loss = ((avg_loss * (period - 1)) + losses[-1]) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100.0 - (100.0 / (1.0 + rs)))
    return result


def macd(values: Sequence[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict[str, list[float | None]]:
    fast_line = ema(values, fast)
    slow_line = ema(values, slow)
    line: list[float | None] = []
    macd_values_for_signal: list[float] = []
    signal_values: list[float | None] = [None for _ in values]
    for index, (fast_value, slow_value) in enumerate(zip(fast_line, slow_line, strict=False)):
        if fast_value is None or slow_value is None:
            line.append(None)
            continue
        value = fast_value - slow_value
        line.append(value)
        macd_values_for_signal.append(value)
        if len(macd_values_for_signal) >= signal:
            sig_series = ema(macd_values_for_signal, signal)
            signal_values[index] = sig_series[-1]
    histogram: list[float | None] = []
    for value, sig_value in zip(line, signal_values, strict=False):
        histogram.append(value - sig_value if value is not None and sig_value is not None else None)
    return {"line": line, "signal": signal_values, "histogram": histogram}


def bollinger(values: Sequence[float], period: int = 20, deviations: float = 2.0) -> dict[str, list[float | None]]:
    middle = sma(values, period)
    upper: list[float | None] = []
    lower: list[float | None] = []
    width: list[float | None] = []
    for index, mid in enumerate(middle):
        if mid is None:
            upper.append(None)
            lower.append(None)
            width.append(None)
            continue
        window = values[index + 1 - period : index + 1]
        variance = sum((value - mid) ** 2 for value in window) / period
        standard = sqrt(variance)
        top = mid + deviations * standard
        bottom = mid - deviations * standard
        upper.append(top)
        lower.append(bottom)
        width.append(_safe_div(top - bottom, mid) * 100.0)
    return {"middle": middle, "upper": upper, "lower": lower, "width_pct": width}


def vwap(candles: Sequence[NormalizedCandle]) -> list[float | None]:
    result: list[float | None] = []
    cumulative_price_volume = 0.0
    cumulative_volume = 0.0
    for candle in candles:
        typical = (candle.high + candle.low + candle.close) / 3.0
        cumulative_price_volume += typical * candle.volume
        cumulative_volume += candle.volume
        result.append(cumulative_price_volume / cumulative_volume if cumulative_volume else None)
    return result


def stochastic(candles: Sequence[NormalizedCandle], period: int = 14, smooth: int = 3) -> dict[str, list[float | None]]:
    close = _series(candles, "close")
    highs = _series(candles, "high")
    lows = _series(candles, "low")
    k_values: list[float | None] = []
    for index, value in enumerate(close):
        if index + 1 < period:
            k_values.append(None)
            continue
        highest = max(highs[index + 1 - period : index + 1])
        lowest = min(lows[index + 1 - period : index + 1])
        k_values.append(_safe_div(value - lowest, highest - lowest) * 100.0)
    d_values = sma([value if value is not None else 0.0 for value in k_values], smooth)
    d_values = [d if k_values[index] is not None and index + 1 >= period + smooth - 1 else None for index, d in enumerate(d_values)]
    return {"k": k_values, "d": d_values}


def adx(candles: Sequence[NormalizedCandle], period: int = 14) -> dict[str, list[float | None]]:
    if not candles:
        return {"adx": [], "plus_di": [], "minus_di": []}
    plus_dm = [0.0]
    minus_dm = [0.0]
    ranges = true_range(candles)
    for index in range(1, len(candles)):
        up_move = candles[index].high - candles[index - 1].high
        down_move = candles[index - 1].low - candles[index].low
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0.0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0.0)

    def wild(values: Sequence[float]) -> list[float | None]:
        smoothed: list[float | None] = []
        previous: float | None = None
        for index, value in enumerate(values):
            if index + 1 < period:
                smoothed.append(None)
            elif previous is None:
                previous = sum(values[index + 1 - period : index + 1])
                smoothed.append(previous)
            else:
                previous = previous - (previous / period) + value
                smoothed.append(previous)
        return smoothed

    smoothed_tr = wild(ranges)
    smoothed_plus = wild(plus_dm)
    smoothed_minus = wild(minus_dm)
    plus_di: list[float | None] = []
    minus_di: list[float | None] = []
    dx_values: list[float] = []
    adx_values: list[float | None] = [None for _ in candles]
    for index, (tr, plus, minus) in enumerate(zip(smoothed_tr, smoothed_plus, smoothed_minus, strict=False)):
        if tr is None or plus is None or minus is None or tr == 0:
            plus_di.append(None)
            minus_di.append(None)
            continue
        plus_value = 100.0 * plus / tr
        minus_value = 100.0 * minus / tr
        plus_di.append(plus_value)
        minus_di.append(minus_value)
        dx = 100.0 * _safe_div(abs(plus_value - minus_value), plus_value + minus_value)
        dx_values.append(dx)
        if len(dx_values) >= period:
            if len(dx_values) == period:
                adx_values[index] = sum(dx_values[-period:]) / period
            else:
                previous_adx = next((value for value in reversed(adx_values[:index]) if value is not None), None)
                adx_values[index] = ((previous_adx or dx) * (period - 1) + dx) / period
    while len(plus_di) < len(candles):
        plus_di.append(None)
        minus_di.append(None)
    return {"adx": adx_values, "plus_di": plus_di, "minus_di": minus_di}


def _last_number(values: Sequence[float | None], default: float | None = None) -> float | None:
    for value in reversed(values):
        if value is not None and isfinite(float(value)):
            return float(value)
    return default


def _last_n_numbers(values: Sequence[float | None], n: int) -> list[float]:
    result: list[float] = []
    for value in reversed(values):
        if value is not None and isfinite(float(value)):
            result.append(float(value))
            if len(result) >= n:
                break
    return list(reversed(result))


def indicator_pack(candles: Sequence[NormalizedCandle]) -> dict[str, Any]:
    close = _series(candles, "close")
    atr14 = atr(candles, 14)
    rsi14 = rsi(close, 14)
    macd_pack = macd(close)
    bb = bollinger(close)
    adx_pack = adx(candles)
    stoch = stochastic(candles)
    ema_values = {period: ema(close, period) for period in (8, 9, 20, 21, 50, 100, 200)}
    sma_values = {period: sma(close, period) for period in (20, 50, 200)}
    vwap_values = vwap(candles)
    latest: dict[str, Any] = {
        "close": _round(close[-1] if close else None),
        "atr14": _round(_last_number(atr14), 8),
        "atr_pct": _round(_safe_div(_last_number(atr14) or 0.0, close[-1] if close else 0.0) * 100.0, 5),
        "rsi14": _round(_last_number(rsi14), 3),
        "macd": _round(_last_number(macd_pack["line"]), 8),
        "macd_signal": _round(_last_number(macd_pack["signal"]), 8),
        "macd_histogram": _round(_last_number(macd_pack["histogram"]), 8),
        "bb_width_pct": _round(_last_number(bb["width_pct"]), 4),
        "adx14": _round(_last_number(adx_pack["adx"]), 3),
        "plus_di": _round(_last_number(adx_pack["plus_di"]), 3),
        "minus_di": _round(_last_number(adx_pack["minus_di"]), 3),
        "stoch_k": _round(_last_number(stoch["k"]), 3),
        "stoch_d": _round(_last_number(stoch["d"]), 3),
        "vwap": _round(_last_number(vwap_values), 8),
    }
    for period, values in ema_values.items():
        latest[f"ema{period}"] = _round(_last_number(values), 8)
    for period, values in sma_values.items():
        latest[f"sma{period}"] = _round(_last_number(values), 8)
    return {
        "latest": latest,
        "series": {
            "atr14": [_round(value, 8) for value in atr14],
            "rsi14": [_round(value, 4) for value in rsi14],
            "macd": [_round(value, 8) for value in macd_pack["line"]],
            "macd_signal": [_round(value, 8) for value in macd_pack["signal"]],
            "macd_histogram": [_round(value, 8) for value in macd_pack["histogram"]],
            "bb_upper": [_round(value, 8) for value in bb["upper"]],
            "bb_middle": [_round(value, 8) for value in bb["middle"]],
            "bb_lower": [_round(value, 8) for value in bb["lower"]],
            "bb_width_pct": [_round(value, 4) for value in bb["width_pct"]],
            "vwap": [_round(value, 8) for value in vwap_values],
            "ema8": [_round(value, 8) for value in ema_values[8]],
            "ema20": [_round(value, 8) for value in ema_values[20]],
            "ema50": [_round(value, 8) for value in ema_values[50]],
            "ema200": [_round(value, 8) for value in ema_values[200]],
            "adx14": [_round(value, 4) for value in adx_pack["adx"]],
            "plus_di": [_round(value, 4) for value in adx_pack["plus_di"]],
            "minus_di": [_round(value, 4) for value in adx_pack["minus_di"]],
            "stoch_k": [_round(value, 4) for value in stoch["k"]],
            "stoch_d": [_round(value, 4) for value in stoch["d"]],
        },
    }


def adaptive_pivots(
    candles: Sequence[NormalizedCandle],
    atr_values: Sequence[float | None],
    left: int = 3,
    right: int = 3,
    max_pivots: int = 180,
) -> list[dict[str, Any]]:
    pivots: list[dict[str, Any]] = []
    if len(candles) < left + right + 3:
        return pivots
    close = _series(candles, "close")
    recent_atr = _last_number(atr_values, default=(max(close) - min(close)) / max(1, len(close))) or 0.0
    threshold = max(recent_atr * 0.18, (close[-1] if close else 1.0) * 0.0004)
    for index in range(left, len(candles) - right):
        window = candles[index - left : index + right + 1]
        candle = candles[index]
        high = candle.high
        low = candle.low
        high_is_pivot = high >= max(item.high for item in window) and (high - min(item.low for item in window)) >= threshold
        low_is_pivot = low <= min(item.low for item in window) and (max(item.high for item in window) - low) >= threshold
        volume_window = [item.volume for item in candles[max(0, index - 20) : index + 1]]
        average_volume = mean(volume_window) if volume_window else candle.volume or 1.0
        importance = 1.0 + _safe_div(candle.volume, average_volume, 1.0) * 0.35
        if high_is_pivot:
            pivots.append(
                {
                    "index": index,
                    "time": candle.time,
                    "price": round(high, 8),
                    "kind": "high",
                    "strength": round(importance + _safe_div(high - low, recent_atr or 1.0) * 0.25, 4),
                }
            )
        if low_is_pivot:
            pivots.append(
                {
                    "index": index,
                    "time": candle.time,
                    "price": round(low, 8),
                    "kind": "low",
                    "strength": round(importance + _safe_div(high - low, recent_atr or 1.0) * 0.25, 4),
                }
            )
    pivots.sort(key=lambda item: item["index"])
    return pivots[-max_pivots:]


def cluster_support_resistance(
    candles: Sequence[NormalizedCandle],
    pivots: Sequence[Mapping[str, Any]],
    atr_value: float | None,
    max_levels: int = 18,
) -> list[dict[str, Any]]:
    if not candles or not pivots:
        return []
    last_close = candles[-1].close
    tolerance = max((atr_value or 0.0) * 0.55, last_close * 0.0012)
    clusters: list[dict[str, Any]] = []
    for pivot in pivots:
        price = _to_float(pivot.get("price"))
        if price <= 0:
            continue
        matched = None
        for cluster in clusters:
            if abs(cluster["price"] - price) <= tolerance:
                matched = cluster
                break
        if matched is None:
            matched = {
                "prices": [],
                "indices": [],
                "kinds": {"high": 0, "low": 0},
                "strength_sum": 0.0,
                "volume_sum": 0.0,
                "price": price,
            }
            clusters.append(matched)
        matched["prices"].append(price)
        matched["indices"].append(int(pivot.get("index", 0)))
        kind = str(pivot.get("kind") or "")
        if kind in matched["kinds"]:
            matched["kinds"][kind] += 1
        matched["strength_sum"] += _to_float(pivot.get("strength"), 1.0)
        idx = int(pivot.get("index", 0))
        if 0 <= idx < len(candles):
            matched["volume_sum"] += candles[idx].volume
        matched["price"] = sum(matched["prices"]) / len(matched["prices"])
    max_volume = max((cluster["volume_sum"] for cluster in clusters), default=1.0)
    levels: list[dict[str, Any]] = []
    for cluster in clusters:
        touch_count = len(cluster["prices"])
        if touch_count < 2 and len(candles) > 80:
            continue
        price = cluster["price"]
        kind = "support" if price < last_close else "resistance" if price > last_close else "pivot"
        recency = 1.0 - min(1.0, (len(candles) - 1 - max(cluster["indices"])) / max(1, len(candles)))
        proximity = 1.0 - min(1.0, abs(price - last_close) / max(last_close * 0.08, tolerance))
        high_bias = cluster["kinds"].get("high", 0)
        low_bias = cluster["kinds"].get("low", 0)
        polarity = "supply" if high_bias > low_bias else "demand" if low_bias > high_bias else "balanced"
        strength = (
            touch_count * 1.5
            + cluster["strength_sum"] * 0.8
            + _safe_div(cluster["volume_sum"], max_volume) * 2.5
            + recency * 1.2
            + proximity * 1.1
        )
        levels.append(
            {
                "id": f"sr-{len(levels) + 1}",
                "price": round(price, 8),
                "kind": kind,
                "polarity": polarity,
                "touches": touch_count,
                "last_touch_index": max(cluster["indices"]),
                "distance_pct": round(_percent_change(price, last_close), 4),
                "strength": round(strength, 4),
                "zone_low": round(price - tolerance, 8),
                "zone_high": round(price + tolerance, 8),
            }
        )
    levels.sort(key=lambda item: (item["strength"], -abs(item["distance_pct"])), reverse=True)
    return levels[:max_levels]


def _line_from_points(point_a: Mapping[str, Any], point_b: Mapping[str, Any]) -> tuple[float, float] | None:
    x1 = _to_float(point_a.get("index"))
    x2 = _to_float(point_b.get("index"))
    y1 = _to_float(point_a.get("price"))
    y2 = _to_float(point_b.get("price"))
    if x1 == x2:
        return None
    slope = (y2 - y1) / (x2 - x1)
    intercept = y1 - slope * x1
    return slope, intercept


def auto_trendlines(
    candles: Sequence[NormalizedCandle],
    pivots: Sequence[Mapping[str, Any]],
    atr_value: float | None,
    max_lines: int = 8,
) -> list[dict[str, Any]]:
    if len(candles) < 30 or len(pivots) < 4:
        return []
    last_index = len(candles) - 1
    tolerance = max((atr_value or 0.0) * 0.65, candles[-1].close * 0.0015)
    candidates: list[dict[str, Any]] = []
    for kind in ("low", "high"):
        kind_pivots = [pivot for pivot in pivots if pivot.get("kind") == kind][-34:]
        for left_index in range(len(kind_pivots)):
            for right_index in range(left_index + 1, len(kind_pivots)):
                a = kind_pivots[left_index]
                b = kind_pivots[right_index]
                if int(b.get("index", 0)) - int(a.get("index", 0)) < 12:
                    continue
                line = _line_from_points(a, b)
                if line is None:
                    continue
                slope, intercept = line
                touches = 0
                max_error = 0.0
                errors: list[float] = []
                for pivot in kind_pivots:
                    x = _to_float(pivot.get("index"))
                    y = _to_float(pivot.get("price"))
                    projected = slope * x + intercept
                    error = abs(y - projected)
                    if error <= tolerance:
                        touches += 1
                        errors.append(error)
                        max_error = max(max_error, error)
                if touches < 3:
                    continue
                projected_now = slope * last_index + intercept
                if projected_now <= 0:
                    continue
                age = int(b.get("index", 0)) - int(a.get("index", 0))
                recency = 1.0 - min(1.0, (last_index - int(b.get("index", 0))) / max(1, len(candles)))
                error_score = 1.0 - min(1.0, (mean(errors) if errors else max_error) / max(tolerance, 1e-12))
                score = touches * 2.2 + min(3.0, age / 40.0) + recency * 2.0 + error_score * 2.5
                line_kind = "support_trend" if kind == "low" else "resistance_trend"
                candidates.append(
                    {
                        "id": f"tl-{kind}-{int(a.get('index', 0))}-{int(b.get('index', 0))}",
                        "kind": line_kind,
                        "start_index": int(a.get("index", 0)),
                        "end_index": int(b.get("index", 0)),
                        "start_price": round(_to_float(a.get("price")), 8),
                        "end_price": round(_to_float(b.get("price")), 8),
                        "projected_price": round(projected_now, 8),
                        "slope": round(slope, 10),
                        "slope_pct_per_bar": round(_safe_div(slope, candles[-1].close) * 100.0, 6),
                        "touches": touches,
                        "strength": round(score, 4),
                    }
                )
    # de-duplicate very similar projections.
    candidates.sort(key=lambda item: item["strength"], reverse=True)
    chosen: list[dict[str, Any]] = []
    for candidate in candidates:
        if any(
            candidate["kind"] == existing["kind"]
            and abs(candidate["projected_price"] - existing["projected_price"]) <= tolerance
            for existing in chosen
        ):
            continue
        chosen.append(candidate)
        if len(chosen) >= max_lines:
            break
    return chosen


def volume_profile(candles: Sequence[NormalizedCandle], bins: int = 48) -> dict[str, Any]:
    if not candles:
        return {"bins": [], "poc": None, "vah": None, "val": None, "hvn": [], "lvn": []}
    lookback = candles[-180:] if len(candles) > 180 else list(candles)
    min_price = min(c.low for c in lookback)
    max_price = max(c.high for c in lookback)
    if max_price <= min_price:
        max_price = min_price + max(1e-8, min_price * 0.001)
    step = (max_price - min_price) / bins
    volume_bins = [0.0 for _ in range(bins)]
    for candle in lookback:
        low_idx = max(0, min(bins - 1, int((candle.low - min_price) / step)))
        high_idx = max(0, min(bins - 1, int((candle.high - min_price) / step)))
        spread = max(1, high_idx - low_idx + 1)
        # Weight close-near bins slightly more while still respecting candle range.
        close_idx = max(0, min(bins - 1, int((candle.close - min_price) / step)))
        for idx in range(low_idx, high_idx + 1):
            weight = 1.35 if idx == close_idx else 1.0
            volume_bins[idx] += candle.volume * weight / spread
    max_volume = max(volume_bins) if volume_bins else 0.0
    total_volume = sum(volume_bins)
    bin_rows: list[dict[str, Any]] = []
    for idx, volume_value in enumerate(volume_bins):
        low = min_price + idx * step
        high = low + step
        bin_rows.append(
            {
                "index": idx,
                "price_low": round(low, 8),
                "price_high": round(high, 8),
                "mid": round((low + high) / 2.0, 8),
                "volume": round(volume_value, 4),
                "ratio": round(_safe_div(volume_value, max_volume), 5),
            }
        )
    poc_index = max(range(len(volume_bins)), key=lambda idx: volume_bins[idx]) if volume_bins else 0
    sorted_by_volume = sorted(range(len(volume_bins)), key=lambda idx: volume_bins[idx], reverse=True)
    accepted: set[int] = set()
    accepted_volume = 0.0
    for idx in sorted_by_volume:
        accepted.add(idx)
        accepted_volume += volume_bins[idx]
        if accepted_volume >= total_volume * 0.70:
            break
    value_lows = [idx for idx in accepted]
    val_index = min(value_lows) if value_lows else poc_index
    vah_index = max(value_lows) if value_lows else poc_index
    hvn = sorted(bin_rows, key=lambda row: row["volume"], reverse=True)[:6]
    average_volume = total_volume / max(1, bins)
    lvn_candidates = [row for row in bin_rows if row["volume"] <= average_volume * 0.45]
    lvn = sorted(lvn_candidates, key=lambda row: row["volume"])[:6]
    return {
        "bins": bin_rows,
        "poc": bin_rows[poc_index] if bin_rows else None,
        "vah": bin_rows[vah_index] if bin_rows else None,
        "val": bin_rows[val_index] if bin_rows else None,
        "hvn": hvn,
        "lvn": lvn,
        "total_volume": round(total_volume, 4),
    }


def fibonacci_map(candles: Sequence[NormalizedCandle], lookback: int = 180) -> dict[str, Any]:
    if len(candles) < 10:
        return {"anchor_low": None, "anchor_high": None, "levels": []}
    sample = candles[-lookback:]
    low_index, low_candle = min(enumerate(sample), key=lambda item: item[1].low)
    high_index, high_candle = max(enumerate(sample), key=lambda item: item[1].high)
    offset = len(candles) - len(sample)
    trend = "upswing" if low_index < high_index else "downswing"
    low = low_candle.low
    high = high_candle.high
    span = max(1e-12, high - low)
    ratios = [0.0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 1.0, 1.272, 1.618]
    levels: list[dict[str, Any]] = []
    for ratio in ratios:
        if trend == "upswing":
            price = high - span * ratio if ratio <= 1.0 else high + span * (ratio - 1.0)
        else:
            price = low + span * ratio if ratio <= 1.0 else low - span * (ratio - 1.0)
        levels.append({"ratio": ratio, "label": f"{ratio:.3f}".rstrip("0").rstrip("."), "price": round(price, 8)})
    return {
        "trend": trend,
        "anchor_low": {"index": offset + low_index, "time": low_candle.time, "price": round(low, 8)},
        "anchor_high": {"index": offset + high_index, "time": high_candle.time, "price": round(high, 8)},
        "levels": levels,
    }


def imbalance_zones(candles: Sequence[NormalizedCandle], max_zones: int = 24) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for index in range(2, len(candles)):
        left = candles[index - 2]
        current = candles[index]
        if current.low > left.high:
            low = left.high
            high = current.low
            mitigated_index = None
            for forward in range(index + 1, len(candles)):
                if candles[forward].low <= high:
                    mitigated_index = forward
                    break
            zones.append(
                {
                    "id": f"fvg-bull-{index}",
                    "kind": "bullish_fvg",
                    "start_index": index - 2,
                    "end_index": mitigated_index or len(candles) - 1,
                    "zone_low": round(low, 8),
                    "zone_high": round(high, 8),
                    "mid": round((low + high) / 2.0, 8),
                    "status": "mitigated" if mitigated_index else "open",
                    "strength": round(_safe_div(high - low, candles[-1].close) * 100.0, 5),
                }
            )
        if current.high < left.low:
            low = current.high
            high = left.low
            mitigated_index = None
            for forward in range(index + 1, len(candles)):
                if candles[forward].high >= low:
                    mitigated_index = forward
                    break
            zones.append(
                {
                    "id": f"fvg-bear-{index}",
                    "kind": "bearish_fvg",
                    "start_index": index - 2,
                    "end_index": mitigated_index or len(candles) - 1,
                    "zone_low": round(low, 8),
                    "zone_high": round(high, 8),
                    "mid": round((low + high) / 2.0, 8),
                    "status": "mitigated" if mitigated_index else "open",
                    "strength": round(_safe_div(high - low, candles[-1].close) * 100.0, 5),
                }
            )
    zones.sort(key=lambda zone: (zone["status"] == "open", zone["start_index"]), reverse=True)
    return zones[:max_zones]


def order_blocks(candles: Sequence[NormalizedCandle], atr_values: Sequence[float | None], max_zones: int = 18) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    if len(candles) < 30:
        return zones
    for index in range(20, len(candles)):
        candle = candles[index]
        atr_now = atr_values[index] if index < len(atr_values) else None
        if not atr_now:
            continue
        body = abs(candle.close - candle.open)
        range_value = candle.high - candle.low
        if range_value < atr_now * 1.25 or body < range_value * 0.55:
            continue
        previous_high = max(item.high for item in candles[index - 16 : index])
        previous_low = min(item.low for item in candles[index - 16 : index])
        bullish_break = candle.close > previous_high
        bearish_break = candle.close < previous_low
        if not bullish_break and not bearish_break:
            continue
        lookback = candles[max(0, index - 8) : index]
        block: NormalizedCandle | None = None
        block_index = index - 1
        if bullish_break:
            for reverse_offset, candidate in enumerate(reversed(lookback)):
                if candidate.close < candidate.open:
                    block = candidate
                    block_index = index - 1 - reverse_offset
                    break
            if block:
                zones.append(
                    {
                        "id": f"ob-demand-{index}",
                        "kind": "bullish_order_block",
                        "start_index": block_index,
                        "end_index": len(candles) - 1,
                        "zone_low": round(block.low, 8),
                        "zone_high": round(max(block.open, block.close), 8),
                        "break_index": index,
                        "status": "active" if candles[-1].low > block.low else "tested",
                        "strength": round(_safe_div(range_value, atr_now) + _safe_div(candle.volume, mean([c.volume for c in lookback]) or 1.0), 4),
                    }
                )
        if bearish_break:
            for reverse_offset, candidate in enumerate(reversed(lookback)):
                if candidate.close > candidate.open:
                    block = candidate
                    block_index = index - 1 - reverse_offset
                    break
            if block:
                zones.append(
                    {
                        "id": f"ob-supply-{index}",
                        "kind": "bearish_order_block",
                        "start_index": block_index,
                        "end_index": len(candles) - 1,
                        "zone_low": round(min(block.open, block.close), 8),
                        "zone_high": round(block.high, 8),
                        "break_index": index,
                        "status": "active" if candles[-1].high < block.high else "tested",
                        "strength": round(_safe_div(range_value, atr_now) + _safe_div(candle.volume, mean([c.volume for c in lookback]) or 1.0), 4),
                    }
                )
    zones.sort(key=lambda zone: (zone["status"] == "active", zone["strength"], zone["start_index"]), reverse=True)
    return zones[:max_zones]


def candle_patterns(candles: Sequence[NormalizedCandle], max_patterns: int = 40) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    for index, candle in enumerate(candles):
        body = abs(candle.close - candle.open)
        candle_range = max(1e-12, candle.high - candle.low)
        upper = candle.high - max(candle.close, candle.open)
        lower = min(candle.close, candle.open) - candle.low
        body_ratio = body / candle_range
        if body_ratio <= 0.1:
            patterns.append({"index": index, "time": candle.time, "kind": "doji", "direction": "neutral", "strength": round(1.0 - body_ratio, 4)})
        if lower >= body * 2.0 and upper <= body * 0.8 and body_ratio <= 0.45:
            patterns.append({"index": index, "time": candle.time, "kind": "hammer", "direction": "bullish", "strength": round(lower / candle_range, 4)})
        if upper >= body * 2.0 and lower <= body * 0.8 and body_ratio <= 0.45:
            patterns.append({"index": index, "time": candle.time, "kind": "shooting_star", "direction": "bearish", "strength": round(upper / candle_range, 4)})
        if body_ratio >= 0.72:
            direction = "bullish" if candle.close > candle.open else "bearish"
            patterns.append({"index": index, "time": candle.time, "kind": "marubozu", "direction": direction, "strength": round(body_ratio, 4)})
        if index == 0:
            continue
        prev = candles[index - 1]
        prev_low_body = min(prev.open, prev.close)
        prev_high_body = max(prev.open, prev.close)
        curr_low_body = min(candle.open, candle.close)
        curr_high_body = max(candle.open, candle.close)
        if prev.close < prev.open and candle.close > candle.open and curr_low_body <= prev_low_body and curr_high_body >= prev_high_body:
            patterns.append({"index": index, "time": candle.time, "kind": "bullish_engulfing", "direction": "bullish", "strength": round(body_ratio + 0.75, 4)})
        if prev.close > prev.open and candle.close < candle.open and curr_low_body <= prev_low_body and curr_high_body >= prev_high_body:
            patterns.append({"index": index, "time": candle.time, "kind": "bearish_engulfing", "direction": "bearish", "strength": round(body_ratio + 0.75, 4)})
    return patterns[-max_patterns:]


def market_structure(candles: Sequence[NormalizedCandle], pivots: Sequence[Mapping[str, Any]], indicators: Mapping[str, Any]) -> dict[str, Any]:
    if not candles:
        return {"state": "unknown", "events": []}
    close = candles[-1].close
    latest = indicators.get("latest", {}) if isinstance(indicators, Mapping) else {}
    ema20 = _to_float(latest.get("ema20"), float("nan"))
    ema50 = _to_float(latest.get("ema50"), float("nan"))
    ema200 = _to_float(latest.get("ema200"), float("nan"))
    trend_votes = 0
    trend_votes += 1 if isfinite(ema20) and close > ema20 else -1 if isfinite(ema20) and close < ema20 else 0
    trend_votes += 1 if isfinite(ema50) and ema20 > ema50 else -1 if isfinite(ema50) and ema20 < ema50 else 0
    trend_votes += 1 if isfinite(ema200) and close > ema200 else -1 if isfinite(ema200) and close < ema200 else 0
    state = "bull_trend" if trend_votes >= 2 else "bear_trend" if trend_votes <= -2 else "mixed_range"
    recent_highs = [pivot for pivot in pivots if pivot.get("kind") == "high"][-5:]
    recent_lows = [pivot for pivot in pivots if pivot.get("kind") == "low"][-5:]
    events: list[dict[str, Any]] = []
    if recent_highs:
        last_high = recent_highs[-1]
        if close > _to_float(last_high.get("price")):
            events.append({"kind": "bullish_bos", "label": "Break of structure above last swing high", "index": len(candles) - 1, "price": round(close, 8), "reference": last_high})
    if recent_lows:
        last_low = recent_lows[-1]
        if close < _to_float(last_low.get("price")):
            events.append({"kind": "bearish_bos", "label": "Break of structure below last swing low", "index": len(candles) - 1, "price": round(close, 8), "reference": last_low})
    if len(recent_highs) >= 2 and len(recent_lows) >= 2:
        higher_highs = _to_float(recent_highs[-1].get("price")) > _to_float(recent_highs[-2].get("price"))
        higher_lows = _to_float(recent_lows[-1].get("price")) > _to_float(recent_lows[-2].get("price"))
        lower_highs = _to_float(recent_highs[-1].get("price")) < _to_float(recent_highs[-2].get("price"))
        lower_lows = _to_float(recent_lows[-1].get("price")) < _to_float(recent_lows[-2].get("price"))
        if higher_highs and higher_lows:
            state = "bull_structure"
        elif lower_highs and lower_lows:
            state = "bear_structure"
        elif higher_highs and lower_lows:
            state = "expanding_range"
        elif lower_highs and higher_lows:
            state = "compression"
    return {
        "state": state,
        "trend_votes": trend_votes,
        "events": events[-8:],
        "last_swing_high": recent_highs[-1] if recent_highs else None,
        "last_swing_low": recent_lows[-1] if recent_lows else None,
    }


def detect_divergences(
    candles: Sequence[NormalizedCandle],
    pivots: Sequence[Mapping[str, Any]],
    rsi_values: Sequence[float | None],
    macd_histogram: Sequence[float | None],
) -> list[dict[str, Any]]:
    divergences: list[dict[str, Any]] = []
    lows = [pivot for pivot in pivots if pivot.get("kind") == "low"][-6:]
    highs = [pivot for pivot in pivots if pivot.get("kind") == "high"][-6:]

    def value_at(series: Sequence[float | None], index: int) -> float | None:
        if 0 <= index < len(series):
            value = series[index]
            return float(value) if value is not None else None
        return None

    if len(lows) >= 2:
        prev, curr = lows[-2], lows[-1]
        prev_idx = int(prev.get("index", 0))
        curr_idx = int(curr.get("index", 0))
        prev_price = _to_float(prev.get("price"))
        curr_price = _to_float(curr.get("price"))
        prev_rsi = value_at(rsi_values, prev_idx)
        curr_rsi = value_at(rsi_values, curr_idx)
        prev_macd = value_at(macd_histogram, prev_idx)
        curr_macd = value_at(macd_histogram, curr_idx)
        if prev_rsi is not None and curr_rsi is not None and curr_price < prev_price and curr_rsi > prev_rsi:
            divergences.append({"kind": "bullish_rsi_divergence", "direction": "bullish", "from_index": prev_idx, "to_index": curr_idx, "strength": round(curr_rsi - prev_rsi, 4)})
        if prev_macd is not None and curr_macd is not None and curr_price < prev_price and curr_macd > prev_macd:
            divergences.append({"kind": "bullish_macd_divergence", "direction": "bullish", "from_index": prev_idx, "to_index": curr_idx, "strength": round(curr_macd - prev_macd, 8)})
    if len(highs) >= 2:
        prev, curr = highs[-2], highs[-1]
        prev_idx = int(prev.get("index", 0))
        curr_idx = int(curr.get("index", 0))
        prev_price = _to_float(prev.get("price"))
        curr_price = _to_float(curr.get("price"))
        prev_rsi = value_at(rsi_values, prev_idx)
        curr_rsi = value_at(rsi_values, curr_idx)
        prev_macd = value_at(macd_histogram, prev_idx)
        curr_macd = value_at(macd_histogram, curr_idx)
        if prev_rsi is not None and curr_rsi is not None and curr_price > prev_price and curr_rsi < prev_rsi:
            divergences.append({"kind": "bearish_rsi_divergence", "direction": "bearish", "from_index": prev_idx, "to_index": curr_idx, "strength": round(prev_rsi - curr_rsi, 4)})
        if prev_macd is not None and curr_macd is not None and curr_price > prev_price and curr_macd < prev_macd:
            divergences.append({"kind": "bearish_macd_divergence", "direction": "bearish", "from_index": prev_idx, "to_index": curr_idx, "strength": round(prev_macd - curr_macd, 8)})
    return divergences


def detect_chart_patterns(
    candles: Sequence[NormalizedCandle],
    pivots: Sequence[Mapping[str, Any]],
    indicators: Mapping[str, Any],
) -> list[dict[str, Any]]:
    patterns: list[dict[str, Any]] = []
    if len(candles) < 30:
        return patterns
    close = _series(candles, "close")
    latest_close = close[-1]
    atr_value = _to_float(indicators.get("latest", {}).get("atr14"), max(close) - min(close))
    tolerance = max(atr_value * 0.8, latest_close * 0.006)
    highs = [pivot for pivot in pivots if pivot.get("kind") == "high"][-8:]
    lows = [pivot for pivot in pivots if pivot.get("kind") == "low"][-8:]
    if len(highs) >= 2:
        h1, h2 = highs[-2], highs[-1]
        p1 = _to_float(h1.get("price"))
        p2 = _to_float(h2.get("price"))
        if abs(p1 - p2) <= tolerance:
            between_lows = [pivot for pivot in lows if int(h1.get("index", 0)) < int(pivot.get("index", 0)) < int(h2.get("index", 0))]
            neckline = min((_to_float(pivot.get("price")) for pivot in between_lows), default=min(c.low for c in candles[int(h1.get("index", 0)) : int(h2.get("index", 0)) + 1]))
            patterns.append({"kind": "double_top", "direction": "bearish", "status": "confirmed" if latest_close < neckline else "forming", "level": round((p1 + p2) / 2.0, 8), "neckline": round(neckline, 8), "strength": round(1.0 + _safe_div(tolerance - abs(p1 - p2), tolerance), 4)})
    if len(lows) >= 2:
        l1, l2 = lows[-2], lows[-1]
        p1 = _to_float(l1.get("price"))
        p2 = _to_float(l2.get("price"))
        if abs(p1 - p2) <= tolerance:
            between_highs = [pivot for pivot in highs if int(l1.get("index", 0)) < int(pivot.get("index", 0)) < int(l2.get("index", 0))]
            neckline = max((_to_float(pivot.get("price")) for pivot in between_highs), default=max(c.high for c in candles[int(l1.get("index", 0)) : int(l2.get("index", 0)) + 1]))
            patterns.append({"kind": "double_bottom", "direction": "bullish", "status": "confirmed" if latest_close > neckline else "forming", "level": round((p1 + p2) / 2.0, 8), "neckline": round(neckline, 8), "strength": round(1.0 + _safe_div(tolerance - abs(p1 - p2), tolerance), 4)})
    if len(highs) >= 3 and len(lows) >= 3:
        h_prices = [_to_float(pivot.get("price")) for pivot in highs[-3:]]
        l_prices = [_to_float(pivot.get("price")) for pivot in lows[-3:]]
        high_range = max(h_prices) - min(h_prices)
        low_rising = l_prices[-1] > l_prices[0]
        low_falling = l_prices[-1] < l_prices[0]
        highs_falling = h_prices[-1] < h_prices[0]
        highs_rising = h_prices[-1] > h_prices[0]
        if high_range <= tolerance * 1.5 and low_rising:
            patterns.append({"kind": "ascending_triangle", "direction": "bullish", "status": "breakout" if latest_close > max(h_prices) else "coiling", "resistance": round(mean(h_prices), 8), "strength": 2.25})
        if (max(l_prices) - min(l_prices)) <= tolerance * 1.5 and highs_falling:
            patterns.append({"kind": "descending_triangle", "direction": "bearish", "status": "breakdown" if latest_close < min(l_prices) else "coiling", "support": round(mean(l_prices), 8), "strength": 2.25})
        if highs_falling and low_rising:
            patterns.append({"kind": "symmetrical_triangle", "direction": "neutral", "status": "compression", "strength": 1.85})
        if highs_rising and low_falling:
            patterns.append({"kind": "expanding_wedge", "direction": "neutral", "status": "volatile", "strength": 1.65})
    # Flat base: a narrow consolidation after a meaningful advance.
    base_window = candles[-28:]
    prior_window = candles[-80:-28] if len(candles) >= 80 else candles[:-28]
    if base_window and prior_window:
        base_high = max(c.high for c in base_window)
        base_low = min(c.low for c in base_window)
        base_range_pct = _safe_div(base_high - base_low, latest_close) * 100.0
        prior_return = _percent_change(base_window[0].close, prior_window[0].close)
        if prior_return > 8.0 and base_range_pct < 8.0:
            patterns.append({"kind": "flat_base", "direction": "bullish", "status": "breakout" if latest_close > base_high else "building", "support": round(base_low, 8), "resistance": round(base_high, 8), "strength": round(2.0 + max(0.0, 8.0 - base_range_pct) / 5.0, 4)})
    # Bull/bear flag: impulse followed by contained pullback.
    if len(candles) >= 42:
        impulse = candles[-42:-22]
        flag = candles[-22:]
        impulse_return = _percent_change(impulse[-1].close, impulse[0].close)
        flag_return = _percent_change(flag[-1].close, flag[0].close)
        flag_high = max(c.high for c in flag)
        flag_low = min(c.low for c in flag)
        flag_range_pct = _safe_div(flag_high - flag_low, latest_close) * 100.0
        if impulse_return > 7.0 and -8.0 <= flag_return <= 2.5 and flag_range_pct < abs(impulse_return) * 0.85:
            patterns.append({"kind": "bull_flag", "direction": "bullish", "status": "breakout" if latest_close > flag_high else "forming", "support": round(flag_low, 8), "resistance": round(flag_high, 8), "strength": round(2.15 + impulse_return / 20.0, 4)})
        if impulse_return < -7.0 and -2.5 <= flag_return <= 8.0 and flag_range_pct < abs(impulse_return) * 0.85:
            patterns.append({"kind": "bear_flag", "direction": "bearish", "status": "breakdown" if latest_close < flag_low else "forming", "support": round(flag_low, 8), "resistance": round(flag_high, 8), "strength": round(2.15 + abs(impulse_return) / 20.0, 4)})
    # Cup-and-handle style broad base.
    if len(candles) >= 90:
        sample = candles[-90:]
        first = max(sample[:25], key=lambda c: c.high)
        middle = min(sample[25:65], key=lambda c: c.low)
        right = max(sample[60:82], key=lambda c: c.high)
        rim_similarity = abs(first.high - right.high) / max(first.high, right.high)
        depth = (min(first.high, right.high) - middle.low) / max(1e-12, min(first.high, right.high))
        handle = candles[-14:]
        handle_low = min(c.low for c in handle)
        handle_depth = (right.high - handle_low) / max(1e-12, right.high)
        if rim_similarity < 0.06 and 0.08 <= depth <= 0.45 and handle_depth <= depth * 0.45:
            patterns.append({"kind": "cup_with_handle", "direction": "bullish", "status": "breakout" if latest_close > right.high else "handle", "pivot": round(right.high, 8), "handle_low": round(handle_low, 8), "strength": round(2.5 + depth * 3.0, 4)})
    # Bollinger/ATR squeeze.
    width_series = [value for value in indicators.get("series", {}).get("bb_width_pct", []) if value is not None]
    if len(width_series) >= 50:
        current_width = width_series[-1]
        percentile_rank = sum(1 for value in width_series[-80:] if value <= current_width) / min(80, len(width_series[-80:]))
        if percentile_rank <= 0.2:
            patterns.append({"kind": "volatility_squeeze", "direction": "neutral", "status": "coiling", "bb_width_pct": round(current_width, 4), "percentile": round(percentile_rank, 4), "strength": round(2.0 + (0.2 - percentile_rank) * 4.0, 4)})
    patterns.sort(key=lambda item: item.get("strength", 0), reverse=True)
    return patterns[:18]


def _nearest_level(levels: Sequence[Mapping[str, Any]], side: str, price: float) -> Mapping[str, Any] | None:
    if side == "below":
        candidates = [level for level in levels if _to_float(level.get("price")) < price]
        return max(candidates, key=lambda level: _to_float(level.get("price")), default=None)
    candidates = [level for level in levels if _to_float(level.get("price")) > price]
    return min(candidates, key=lambda level: _to_float(level.get("price")), default=None)


def build_trade_plan(
    candles: Sequence[NormalizedCandle],
    levels: Sequence[Mapping[str, Any]],
    trendlines: Sequence[Mapping[str, Any]],
    indicators: Mapping[str, Any],
    bias: str,
    risk_settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    risk_settings = risk_settings or {}
    price = candles[-1].close if candles else 0.0
    atr_value = _to_float(indicators.get("latest", {}).get("atr14"), price * 0.015)
    min_stop_pct = _to_float(risk_settings.get("min_stop_pct"), 0.35)
    max_stop_pct = _to_float(risk_settings.get("max_stop_pct"), 6.5)
    min_stop_distance = max(price * min_stop_pct / 100.0, atr_value * 0.65)
    max_stop_distance = max(min_stop_distance, price * max_stop_pct / 100.0)
    account_size = max(1.0, _to_float(risk_settings.get("account_equity"), 10000.0))
    risk_pct = min(10.0, max(0.05, _to_float(risk_settings.get("risk_pct"), 1.0)))
    risk_amount = account_size * risk_pct / 100.0
    if bias == "short":
        nearest_resistance = _nearest_level(levels, "above", price)
        nearest_support = _nearest_level(levels, "below", price)
        entry_zone_high = price + atr_value * 0.18
        entry_zone_low = price - atr_value * 0.28
        raw_stop = (_to_float(nearest_resistance.get("zone_high")) if nearest_resistance else price + atr_value * 1.5) if nearest_resistance else price + atr_value * 1.5
        stop = max(raw_stop, price + min_stop_distance)
        if stop - price > max_stop_distance:
            stop = price + max_stop_distance
        risk_per_unit = max(1e-12, stop - price)
        t1 = _to_float(nearest_support.get("price")) if nearest_support else price - risk_per_unit
        targets = [min(t1, price - risk_per_unit), price - risk_per_unit * 2.0, price - risk_per_unit * 3.2]
        direction = "sell_short"
    else:
        nearest_support = _nearest_level(levels, "below", price)
        nearest_resistance = _nearest_level(levels, "above", price)
        entry_zone_low = price - atr_value * 0.18
        entry_zone_high = price + atr_value * 0.28
        raw_stop = (_to_float(nearest_support.get("zone_low")) if nearest_support else price - atr_value * 1.5) if nearest_support else price - atr_value * 1.5
        stop = min(raw_stop, price - min_stop_distance)
        if price - stop > max_stop_distance:
            stop = price - max_stop_distance
        risk_per_unit = max(1e-12, price - stop)
        t1 = _to_float(nearest_resistance.get("price")) if nearest_resistance else price + risk_per_unit
        targets = [max(t1, price + risk_per_unit), price + risk_per_unit * 2.0, price + risk_per_unit * 3.2]
        direction = "buy_long"
    quantity = _safe_div(risk_amount, risk_per_unit)
    quote_notional = quantity * price
    staged = []
    for idx, (target, close_pct) in enumerate(zip(targets, (0.35, 0.35, 0.30), strict=False), start=1):
        reward = abs(target - price)
        staged.append(
            {
                "target": round(target, 8),
                "close_pct": round(close_pct * 100.0, 2),
                "rr": round(_safe_div(reward, risk_per_unit), 4),
                "label": f"TP{idx}",
            }
        )
    rr_first = staged[0]["rr"] if staged else 0.0
    rr_blended = sum(item["rr"] * item["close_pct"] / 100.0 for item in staged)
    return {
        "bias": bias,
        "direction": direction,
        "entry": round(price, 8),
        "entry_zone_low": round(entry_zone_low, 8),
        "entry_zone_high": round(entry_zone_high, 8),
        "stop_loss": round(stop, 8),
        "risk_per_unit": round(risk_per_unit, 8),
        "risk_amount": round(risk_amount, 2),
        "suggested_quantity": round(quantity, 8),
        "suggested_quote_notional": round(quote_notional, 2),
        "targets": staged,
        "rr_first": round(rr_first, 4),
        "rr_blended": round(rr_blended, 4),
        "trailing": {
            "activation_rr": 1.0,
            "callback_atr_multiple": 1.15,
            "profit_lock_after_tp1": "breakeven_plus_fees",
            "tighten_after_tp2": "lock_0.8R",
        },
        "invalidation": "Close beyond stop-loss or failed reclaim of mapped level after breakout.",
        "management": [
            "Scale 35/35/30 across targets unless liquidity is thin.",
            "After TP1, move protective stop to breakeven or entry plus fees.",
            "If price accepts back inside the broken zone for two candles, downgrade to wait/manage.",
        ],
    }


def confluence_score(
    candles: Sequence[NormalizedCandle],
    indicators: Mapping[str, Any],
    levels: Sequence[Mapping[str, Any]],
    structure: Mapping[str, Any],
    chart_patterns: Sequence[Mapping[str, Any]],
    divergences: Sequence[Mapping[str, Any]],
    imbalances: Sequence[Mapping[str, Any]],
    blocks: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    risk_settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    price = candles[-1].close if candles else 0.0
    latest = indicators.get("latest", {})
    long_score = 0.0
    short_score = 0.0
    reasons: list[dict[str, Any]] = []

    def add(direction: str, title: str, detail: str, weight: float) -> None:
        nonlocal long_score, short_score
        if direction == "long":
            long_score += weight
        elif direction == "short":
            short_score += weight
        else:
            long_score += weight * 0.5
            short_score += weight * 0.5
        reasons.append({"direction": direction, "title": title, "detail": detail, "weight": round(weight, 3)})

    ema20 = _to_float(latest.get("ema20"), float("nan"))
    ema50 = _to_float(latest.get("ema50"), float("nan"))
    ema200 = _to_float(latest.get("ema200"), float("nan"))
    if isfinite(ema20) and isfinite(ema50):
        if price > ema20 > ema50:
            add("long", "Trend stack bullish", "Price is above EMA20 and EMA20 is above EMA50.", 12.0)
        elif price < ema20 < ema50:
            add("short", "Trend stack bearish", "Price is below EMA20 and EMA20 is below EMA50.", 12.0)
        else:
            add("neutral", "Trend mixed", "Moving averages do not agree; size down or wait for confirmation.", 2.0)
    if isfinite(ema200):
        if price > ema200:
            add("long", "Above long-term mean", "Price is above EMA200, favoring long continuation plans.", 5.0)
        elif price < ema200:
            add("short", "Below long-term mean", "Price is below EMA200, favoring short continuation plans.", 5.0)
    rsi_value = _to_float(latest.get("rsi14"), float("nan"))
    if isfinite(rsi_value):
        if 52 <= rsi_value <= 68:
            add("long", "Constructive RSI", f"RSI {rsi_value:.1f} shows upside momentum without extreme overbought pressure.", 7.0)
        elif 32 <= rsi_value <= 48:
            add("short", "Constructive short RSI", f"RSI {rsi_value:.1f} shows downside momentum without extreme oversold pressure.", 7.0)
        elif rsi_value < 30:
            add("long", "Oversold reversal fuel", f"RSI {rsi_value:.1f} can support a reversal only after structure confirms.", 3.5)
        elif rsi_value > 70:
            add("short", "Overbought reversal risk", f"RSI {rsi_value:.1f} warns that new longs need extra confirmation.", 3.5)
    macd_hist = _to_float(latest.get("macd_histogram"), 0.0)
    if macd_hist > 0:
        add("long", "MACD pressure positive", "MACD histogram is above zero.", 5.5)
    elif macd_hist < 0:
        add("short", "MACD pressure negative", "MACD histogram is below zero.", 5.5)
    adx_value = _to_float(latest.get("adx14"), float("nan"))
    if isfinite(adx_value) and adx_value >= 22:
        if _to_float(latest.get("plus_di"), 0.0) > _to_float(latest.get("minus_di"), 0.0):
            add("long", "Directional trend strength", f"ADX {adx_value:.1f} with +DI above -DI.", 4.0)
        else:
            add("short", "Directional trend strength", f"ADX {adx_value:.1f} with -DI above +DI.", 4.0)
    state = str(structure.get("state", ""))
    if "bull" in state:
        add("long", "Market structure bullish", f"Structure engine classified the tape as {state.replace('_', ' ')}.", 9.0)
    elif "bear" in state:
        add("short", "Market structure bearish", f"Structure engine classified the tape as {state.replace('_', ' ')}.", 9.0)
    elif state in {"compression", "mixed_range"}:
        add("neutral", "Compression/range context", "Breakout confirmation matters more than prediction in this regime.", 4.0)
    support = _nearest_level(levels, "below", price)
    resistance = _nearest_level(levels, "above", price)
    atr_pct = _to_float(latest.get("atr_pct"), 1.0)
    if support:
        distance = abs(_percent_change(price, _to_float(support.get("price"))))
        if distance <= max(atr_pct * 1.5, 1.2):
            add("long", "Near mapped demand", f"Nearest support/demand is {distance:.2f}% below price with {support.get('touches')} touches.", 7.0)
    if resistance:
        distance = abs(_percent_change(_to_float(resistance.get("price")), price))
        if distance <= max(atr_pct * 1.5, 1.2):
            add("short", "Near mapped supply", f"Nearest resistance/supply is {distance:.2f}% above price with {resistance.get('touches')} touches.", 7.0)
    for pattern in chart_patterns[:8]:
        direction = str(pattern.get("direction"))
        weight = min(8.0, 2.5 + _to_float(pattern.get("strength"), 1.0) * 1.2)
        if direction == "bullish":
            add("long", str(pattern.get("kind", "bullish pattern")).replace("_", " ").title(), f"Pattern status: {pattern.get('status', 'active')}.", weight)
        elif direction == "bearish":
            add("short", str(pattern.get("kind", "bearish pattern")).replace("_", " ").title(), f"Pattern status: {pattern.get('status', 'active')}.", weight)
        elif str(pattern.get("kind")) in {"volatility_squeeze", "symmetrical_triangle"}:
            add("neutral", str(pattern.get("kind")).replace("_", " ").title(), "Directional trigger required; expect expansion after compression.", 2.5)
    for divergence in divergences[-4:]:
        if divergence.get("direction") == "bullish":
            add("long", "Bullish divergence", str(divergence.get("kind", "")).replace("_", " "), 6.0)
        elif divergence.get("direction") == "bearish":
            add("short", "Bearish divergence", str(divergence.get("kind", "")).replace("_", " "), 6.0)
    for zone in imbalances[:6]:
        if zone.get("status") != "open":
            continue
        low = _to_float(zone.get("zone_low"))
        high = _to_float(zone.get("zone_high"))
        if low <= price <= high:
            add("long" if "bullish" in str(zone.get("kind")) else "short", "Inside open imbalance", "Price is trading inside a still-open FVG/imbalance zone.", 3.5)
    for block in blocks[:5]:
        low = _to_float(block.get("zone_low"))
        high = _to_float(block.get("zone_high"))
        if low <= price <= high:
            add("long" if "bullish" in str(block.get("kind")) else "short", "Inside order block", "Price is inside an auto-mapped order-block zone.", 5.5)
    poc = profile.get("poc") if isinstance(profile, Mapping) else None
    if isinstance(poc, Mapping):
        poc_mid = _to_float(poc.get("mid"))
        if price > poc_mid:
            add("long", "Above volume POC", "Price is holding above the volume profile point of control.", 3.5)
        elif price < poc_mid:
            add("short", "Below volume POC", "Price is trading below the volume profile point of control.", 3.5)
    # Volatility sanity check.
    if atr_pct > 0:
        if atr_pct <= 0.25:
            add("neutral", "Low volatility", "ATR is very compressed; use breakout triggers instead of blind entries.", 1.5)
        elif atr_pct >= 8.0:
            add("neutral", "High volatility", "ATR is elevated; bracket width and leverage should be reduced.", 1.5)
    # Normalize to a confidence-like 0-100 score.
    max_possible = 90.0
    long_confidence = min(100.0, max(0.0, long_score / max_possible * 100.0))
    short_confidence = min(100.0, max(0.0, short_score / max_possible * 100.0))
    if long_confidence >= short_confidence + 8 and long_confidence >= 45:
        recommendation = "long_bias"
        primary_bias = "long"
    elif short_confidence >= long_confidence + 8 and short_confidence >= 45:
        recommendation = "short_bias"
        primary_bias = "short"
    else:
        recommendation = "wait_for_trigger"
        primary_bias = "long" if long_confidence >= short_confidence else "short"
    long_plan = build_trade_plan(candles, levels, [], indicators, "long", risk_settings)
    short_plan = build_trade_plan(candles, levels, [], indicators, "short", risk_settings)
    primary_plan = long_plan if primary_bias == "long" else short_plan
    reasons.sort(key=lambda item: item["weight"], reverse=True)
    return {
        "recommendation": recommendation,
        "primary_bias": primary_bias,
        "confidence": round(max(long_confidence, short_confidence), 2),
        "long_score": round(long_confidence, 2),
        "short_score": round(short_confidence, 2),
        "reasons": reasons[:24],
        "trade_plans": {"long": long_plan, "short": short_plan, "primary": primary_plan},
        "why": _build_why(recommendation, primary_plan, reasons[:8]),
    }


def _build_why(recommendation: str, plan: Mapping[str, Any], reasons: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if recommendation == "wait_for_trigger":
        headline = "Wait: evidence is mixed or the best trade still needs a trigger."
    elif recommendation == "long_bias":
        headline = "Long bias: enough bullish confluence exists to plan a bracket, subject to risk gates."
    else:
        headline = "Short bias: enough bearish confluence exists to plan a bracket, subject to risk gates."
    return {
        "headline": headline,
        "when_to_trade": [
            "Enter only after price confirms the selected trigger zone with a candle close or decisive sweep/reclaim.",
            "Avoid entry directly into the nearest opposite support/resistance unless the first target still offers acceptable R/R.",
            "Stand down when spread, slippage, funding, or daily-loss controls fail the bot preflight.",
        ],
        "how_to_trade": [
            f"Use entry zone {plan.get('entry_zone_low')} - {plan.get('entry_zone_high')} with stop {plan.get('stop_loss')}.",
            "Prefer bracket/OCO protection immediately after entry; futures legs should be reduce-only where the venue supports it.",
            "Scale out across TP1/TP2/runner and let the trail manage the final quantity after TP1.",
        ],
        "why_good_or_bad": [str(reason.get("title")) + ": " + str(reason.get("detail")) for reason in reasons[:6]],
    }


def signal_markers(
    candles: Sequence[NormalizedCandle],
    pivots: Sequence[Mapping[str, Any]],
    patterns: Sequence[Mapping[str, Any]],
    divergences: Sequence[Mapping[str, Any]],
    structure: Mapping[str, Any],
) -> list[dict[str, Any]]:
    markers: list[dict[str, Any]] = []
    for pattern in patterns:
        kind = str(pattern.get("kind", ""))
        direction = str(pattern.get("direction", "neutral"))
        index = int(pattern.get("index", len(candles) - 1)) if "index" in pattern else len(candles) - 1
        if direction in {"bullish", "bearish"}:
            markers.append(
                {
                    "index": index,
                    "time": candles[index].time if 0 <= index < len(candles) else candles[-1].time,
                    "side": "buy" if direction == "bullish" else "sell",
                    "kind": kind,
                    "label": kind.replace("_", " ").title(),
                    "price": round(candles[index].low if direction == "bullish" and 0 <= index < len(candles) else candles[index].high if 0 <= index < len(candles) else candles[-1].close, 8),
                }
            )
    for divergence in divergences:
        idx = int(divergence.get("to_index", len(candles) - 1))
        direction = str(divergence.get("direction"))
        markers.append(
            {
                "index": idx,
                "time": candles[idx].time if 0 <= idx < len(candles) else candles[-1].time,
                "side": "buy" if direction == "bullish" else "sell",
                "kind": str(divergence.get("kind")),
                "label": "Divergence",
                "price": round(candles[idx].low if direction == "bullish" and 0 <= idx < len(candles) else candles[idx].high if 0 <= idx < len(candles) else candles[-1].close, 8),
            }
        )
    for event in structure.get("events", []) if isinstance(structure, Mapping) else []:
        kind = str(event.get("kind", ""))
        if kind in {"bullish_bos", "bearish_bos"}:
            markers.append(
                {
                    "index": int(event.get("index", len(candles) - 1)),
                    "time": candles[-1].time,
                    "side": "buy" if kind == "bullish_bos" else "sell",
                    "kind": kind,
                    "label": "BOS",
                    "price": round(_to_float(event.get("price"), candles[-1].close), 8),
                }
            )
    markers.sort(key=lambda item: item["index"])
    return markers[-40:]


def playbook_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": "liquidity_sweep_reclaim",
            "name": "Liquidity Sweep + Reclaim",
            "best_for": "Reversals around obvious highs/lows, crypto futures stop runs, and failed breakdowns.",
            "entry_rules": ["Sweep mapped support/resistance", "Close back inside prior range", "RSI/MACD divergence or volume climax"],
            "risk": "Stop outside the sweep wick; first target at midpoint/POC; runner to opposite liquidity.",
        },
        {
            "id": "breakout_retest",
            "name": "Breakout Retest Bracket",
            "best_for": "Flat bases, triangles, flags, and high-volume acceptance above resistance.",
            "entry_rules": ["Close through mapped level", "Retest holds as support/resistance", "Volume above recent average"],
            "risk": "Stop beyond retest zone; TP1 at 1R or next HVN; trail after TP1.",
        },
        {
            "id": "trend_pullback",
            "name": "Trend Pullback Continuation",
            "best_for": "Strong EMA stacks and ADX-confirmed continuation after shallow pullbacks.",
            "entry_rules": ["EMA20/50 stack agrees", "Pullback into VWAP, EMA20, or demand block", "Momentum turns back with candle confirmation"],
            "risk": "Stop under pullback low/high; staged targets at trendline projection and fib extensions.",
        },
        {
            "id": "range_reversion",
            "name": "Range Reversion Fade",
            "best_for": "Mixed/range markets with respected support/resistance and no broad trend.",
            "entry_rules": ["Price reaches mapped edge", "Momentum divergence or exhaustion candle", "First target to POC/midrange"],
            "risk": "Tight stop outside range; no trade if trendline break confirms expansion.",
        },
        {
            "id": "squeeze_expansion",
            "name": "Squeeze Expansion",
            "best_for": "Low Bollinger width, compression triangles, and volatility expansion setups.",
            "entry_rules": ["Squeeze percentile low", "Break compression boundary", "Volume expansion"],
            "risk": "Initial stop behind compression; reduce leverage if ATR expands too quickly.",
        },
    ]


def risk_dashboard(candles: Sequence[NormalizedCandle], indicators: Mapping[str, Any], score: Mapping[str, Any]) -> dict[str, Any]:
    latest = indicators.get("latest", {}) if isinstance(indicators, Mapping) else {}
    price = candles[-1].close if candles else 0.0
    atr_value = _to_float(latest.get("atr14"), 0.0)
    atr_pct = _safe_div(atr_value, price) * 100.0 if price else 0.0
    confidence = _to_float(score.get("confidence"), 0.0)
    recommended_max_leverage = 1.0
    if atr_pct > 0:
        recommended_max_leverage = max(1.0, min(20.0, 12.0 / max(0.4, atr_pct)))
    if confidence < 50:
        recommended_max_leverage = min(recommended_max_leverage, 3.0)
    warnings = []
    if atr_pct >= 5.0:
        warnings.append("ATR is high; reduce leverage and widen/slim quantity rather than moving stops too tight.")
    if confidence < 45:
        warnings.append("Signal confidence is below trade threshold; use alert-only mode until a trigger appears.")
    if score.get("recommendation") == "wait_for_trigger":
        warnings.append("Recommendation is wait-for-trigger; do not send market orders without confirmation.")
    return {
        "atr_pct": round(atr_pct, 4),
        "recommended_max_leverage": round(recommended_max_leverage, 2),
        "suggested_risk_pct": 0.5 if confidence < 45 else 0.75 if confidence < 60 else 1.0,
        "warnings": warnings,
        "preflight": [
            {"name": "Paper-first mode", "status": "required", "ok": True},
            {"name": "Bracket protection", "status": "stop + target + trail", "ok": True},
            {"name": "Confidence threshold", "status": f"{confidence:.1f}/100", "ok": confidence >= 45},
            {"name": "Volatility check", "status": f"ATR {atr_pct:.2f}%", "ok": atr_pct < 8.0},
        ],
    }


def analyze_market_structure(
    candles: Sequence[Mapping[str, Any]] | None,
    *,
    symbol: str = "BTCUSDT",
    timeframe: str = "15m",
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_candles(candles)
    settings = settings or {}
    if len(normalized) < 30:
        return {
            "ok": False,
            "symbol": _compact_symbol(symbol),
            "timeframe": timeframe,
            "error": "At least 30 OHLCV candles are required for auto-mapping.",
            "candles": [c.as_dict() for c in normalized],
        }
    indicators = indicator_pack(normalized)
    atr_values_raw = [value if value is None else float(value) for value in indicators["series"]["atr14"]]
    pivots = adaptive_pivots(normalized, atr_values_raw)
    atr_value = _to_float(indicators["latest"].get("atr14"), None if False else normalized[-1].close * 0.01)
    levels = cluster_support_resistance(normalized, pivots, atr_value)
    trendlines = auto_trendlines(normalized, pivots, atr_value)
    profile = volume_profile(normalized, int(settings.get("volume_bins", 48) or 48))
    fib = fibonacci_map(normalized)
    imbalances = imbalance_zones(normalized)
    blocks = order_blocks(normalized, atr_values_raw)
    candles_patterns = candle_patterns(normalized)
    structure = market_structure(normalized, pivots, indicators)
    chart_patterns = detect_chart_patterns(normalized, pivots, indicators)
    divergences = detect_divergences(normalized, pivots, indicators["series"]["rsi14"], indicators["series"]["macd_histogram"])
    score = confluence_score(normalized, indicators, levels, structure, chart_patterns + candles_patterns[-12:], divergences, imbalances, blocks, profile, settings.get("risk", {}))
    markers = signal_markers(normalized, pivots, candles_patterns + chart_patterns, divergences, structure)
    risk = risk_dashboard(normalized, indicators, score)
    last_close = normalized[-1].close
    nearest_support = _nearest_level(levels, "below", last_close)
    nearest_resistance = _nearest_level(levels, "above", last_close)
    return {
        "ok": True,
        "symbol": _compact_symbol(symbol),
        "timeframe": timeframe,
        "bar_count": len(normalized),
        "candles": [c.as_dict() for c in normalized],
        "indicators": indicators,
        "overlays": {
            "pivots": pivots,
            "support_resistance": levels,
            "trendlines": trendlines,
            "volume_profile": profile,
            "fibonacci": fib,
            "imbalances": imbalances,
            "order_blocks": blocks,
        },
        "patterns": {
            "candles": candles_patterns,
            "chart": chart_patterns,
            "divergences": divergences,
            "structure": structure,
        },
        "signals": {
            "markers": markers,
            "nearest_support": nearest_support,
            "nearest_resistance": nearest_resistance,
            **score,
        },
        "risk": risk,
        "playbooks": playbook_catalog(),
        "feature_flags": {
            "support_resistance": True,
            "trendlines": True,
            "volume_profile": True,
            "fibonacci": True,
            "fvg_imbalances": True,
            "order_blocks": True,
            "candlestick_patterns": True,
            "chart_patterns": True,
            "divergence": True,
            "structure_bos_choch": True,
            "trade_plan": True,
            "dom_ladder_projection": True,
        },
    }


def generate_demo_candles(symbol: str = "BTCUSDT", timeframe: str = "15m", bars: int = 240, seed: int | None = None) -> list[dict[str, Any]]:
    compact = _compact_symbol(symbol)
    seed_value = seed if seed is not None else sum(ord(ch) for ch in compact + timeframe)
    rng = Random(seed_value)
    base_price = 46000.0 if "BTC" in compact else 3200.0 if "ETH" in compact else 150.0 if "SOL" in compact else 100.0
    price = base_price * (0.92 + rng.random() * 0.16)
    candles: list[dict[str, Any]] = []
    trend = rng.choice([-1, 1]) * base_price * 0.0008
    for index in range(max(30, min(1200, int(bars)))):
        cycle = base_price * 0.006 * (rng.random() - 0.5) + base_price * 0.003 * (1 if (index // 35) % 2 == 0 else -1)
        if index in {70, 130, 190, 210}:
            trend *= -0.65
        drift = trend + cycle * 0.18
        shock = rng.gauss(0, base_price * 0.0035)
        open_price = price
        close = max(base_price * 0.08, open_price + drift + shock)
        high = max(open_price, close) + abs(rng.gauss(base_price * 0.002, base_price * 0.0018))
        low = min(open_price, close) - abs(rng.gauss(base_price * 0.002, base_price * 0.0018))
        if index % 57 == 0 and index > 0:
            # wick sweep
            if rng.random() > 0.5:
                high += base_price * rng.uniform(0.012, 0.035)
            else:
                low -= base_price * rng.uniform(0.012, 0.035)
        volume = max(1.0, rng.gauss(1000, 260) * (1.0 + abs(close - open_price) / max(1.0, base_price) * 24.0))
        if index % 57 == 0:
            volume *= rng.uniform(2.0, 4.5)
        candles.append(
            {
                "time": index,
                "open": round(open_price, 8),
                "high": round(max(high, open_price, close), 8),
                "low": round(max(0.00000001, min(low, open_price, close)), 8),
                "close": round(close, 8),
                "volume": round(volume, 4),
            }
        )
        price = close
    return candles


def backtest_auto_strategy(
    candles: Sequence[Mapping[str, Any]] | None,
    *,
    symbol: str = "BTCUSDT",
    timeframe: str = "15m",
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    normalized = normalize_candles(candles)
    settings = settings or {}
    if len(normalized) < 80:
        return {"ok": False, "error": "At least 80 candles are required for this quick strategy backtest."}
    closes = _series(normalized, "close")
    ema_fast = ema(closes, int(settings.get("fast_ema", 20) or 20))
    ema_slow = ema(closes, int(settings.get("slow_ema", 50) or 50))
    rsi_values = rsi(closes, 14)
    atr_values = atr(normalized, 14)
    equity = float(settings.get("starting_equity", 10000.0) or 10000.0)
    risk_pct = float(settings.get("risk_pct", 1.0) or 1.0)
    allow_short = bool(settings.get("allow_short", True))
    position: dict[str, Any] | None = None
    trades: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = []
    max_equity = equity
    max_drawdown = 0.0
    for index in range(55, len(normalized)):
        candle = normalized[index]
        mark = candle.close
        fast_now = ema_fast[index]
        slow_now = ema_slow[index]
        fast_prev = ema_fast[index - 1]
        slow_prev = ema_slow[index - 1]
        rsi_now = rsi_values[index]
        atr_now = atr_values[index] or mark * 0.01
        if position:
            side = position["side"]
            stop_hit = candle.low <= position["stop"] if side == "long" else candle.high >= position["stop"]
            target_hit = candle.high >= position["target"] if side == "long" else candle.low <= position["target"]
            exit_reason = None
            exit_price = mark
            if stop_hit and target_hit:
                exit_reason = "ambiguous_stop_first"
                exit_price = position["stop"]
            elif stop_hit:
                exit_reason = "stop"
                exit_price = position["stop"]
            elif target_hit:
                exit_reason = "target"
                exit_price = position["target"]
            elif index - position["entry_index"] >= int(settings.get("max_bars", 48) or 48):
                exit_reason = "time"
                exit_price = mark
            if exit_reason:
                pnl_per_unit = (exit_price - position["entry"]) if side == "long" else (position["entry"] - exit_price)
                pnl = pnl_per_unit * position["qty"]
                equity += pnl
                trades.append(
                    {
                        "side": side,
                        "entry_index": position["entry_index"],
                        "exit_index": index,
                        "entry": round(position["entry"], 8),
                        "exit": round(exit_price, 8),
                        "qty": round(position["qty"], 8),
                        "pnl": round(pnl, 2),
                        "return_pct": round(_safe_div(pnl, position["notional"]) * 100.0, 4),
                        "reason": exit_reason,
                    }
                )
                position = None
        if position is None and all(value is not None for value in (fast_now, slow_now, fast_prev, slow_prev, rsi_now)):
            crossed_up = fast_prev <= slow_prev and fast_now > slow_now and rsi_now >= 48
            crossed_down = fast_prev >= slow_prev and fast_now < slow_now and rsi_now <= 52
            if crossed_up:
                stop = mark - atr_now * 1.6
                target = mark + atr_now * 2.6
                qty = _safe_div(equity * risk_pct / 100.0, mark - stop)
                position = {"side": "long", "entry": mark, "stop": stop, "target": target, "qty": qty, "notional": qty * mark, "entry_index": index}
            elif allow_short and crossed_down:
                stop = mark + atr_now * 1.6
                target = mark - atr_now * 2.6
                qty = _safe_div(equity * risk_pct / 100.0, stop - mark)
                position = {"side": "short", "entry": mark, "stop": stop, "target": target, "qty": qty, "notional": qty * mark, "entry_index": index}
        unrealized = 0.0
        if position:
            unrealized = ((mark - position["entry"]) if position["side"] == "long" else (position["entry"] - mark)) * position["qty"]
        mark_equity = equity + unrealized
        max_equity = max(max_equity, mark_equity)
        max_drawdown = min(max_drawdown, _safe_div(mark_equity - max_equity, max_equity) * 100.0)
        curve.append({"index": index, "time": candle.time, "equity": round(mark_equity, 2), "drawdown_pct": round(_safe_div(mark_equity - max_equity, max_equity) * 100.0, 4)})
    wins = [trade for trade in trades if trade["pnl"] > 0]
    losses = [trade for trade in trades if trade["pnl"] < 0]
    gross_profit = sum(trade["pnl"] for trade in wins)
    gross_loss = abs(sum(trade["pnl"] for trade in losses))
    return {
        "ok": True,
        "symbol": _compact_symbol(symbol),
        "timeframe": timeframe,
        "settings": {"fast_ema": settings.get("fast_ema", 20), "slow_ema": settings.get("slow_ema", 50), "risk_pct": risk_pct, "allow_short": allow_short},
        "metrics": {
            "starting_equity": round(float(settings.get("starting_equity", 10000.0) or 10000.0), 2),
            "ending_equity": round(equity, 2),
            "return_pct": round(_percent_change(equity, float(settings.get("starting_equity", 10000.0) or 10000.0)), 4),
            "total_trades": len(trades),
            "win_rate_pct": round(_safe_div(len(wins), len(trades)) * 100.0, 2),
            "profit_factor": round(_safe_div(gross_profit, gross_loss, gross_profit if gross_profit else 0.0), 4),
            "max_drawdown_pct": round(max_drawdown, 4),
            "average_trade": round(mean([trade["pnl"] for trade in trades]) if trades else 0.0, 2),
        },
        "trades": trades[-100:],
        "equity_curve": curve,
    }
