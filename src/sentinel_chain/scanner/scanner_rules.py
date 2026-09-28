"""Pure scanner feature extraction, preset rules, scoring, and ticket building."""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .scanner_models import (
    CandlePoint,
    ConditionMatch,
    MarketContext,
    ScanHit,
    ScannerCondition,
    ScannerRule,
    SuggestedTicket,
)

EPS = 1e-12


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        return float(value)
    except Exception:
        return default


def _pct(a: float, b: float) -> float:
    if abs(b) < EPS:
        return 0.0
    return (a - b) / b * 100.0


def _sma(values: Sequence[float], length: int) -> Optional[float]:
    if length <= 0 or len(values) < length:
        return None
    return sum(values[-length:]) / length


def _ema(values: Sequence[float], length: int) -> Optional[float]:
    if length <= 0 or len(values) < length:
        return None
    alpha = 2.0 / (length + 1.0)
    ema = sum(values[:length]) / length
    for value in values[length:]:
        ema = alpha * value + (1.0 - alpha) * ema
    return ema


def _true_ranges(candles: Sequence[CandlePoint]) -> List[float]:
    trs: List[float] = []
    prev_close: Optional[float] = None
    for c in candles:
        if prev_close is None:
            tr = c.high - c.low
        else:
            tr = max(c.high - c.low, abs(c.high - prev_close), abs(c.low - prev_close))
        trs.append(max(tr, 0.0))
        prev_close = c.close
    return trs


def _atr(candles: Sequence[CandlePoint], length: int = 14) -> Optional[float]:
    trs = _true_ranges(candles)
    return _sma(trs, min(length, len(trs))) if trs else None


def _rsi(values: Sequence[float], length: int = 14) -> Optional[float]:
    if len(values) <= length:
        return None
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0.0))
        losses.append(abs(min(delta, 0.0)))
    avg_gain = sum(gains[:length]) / length
    avg_loss = sum(losses[:length]) / length
    for gain, loss in zip(gains[length:], losses[length:]):
        avg_gain = (avg_gain * (length - 1) + gain) / length
        avg_loss = (avg_loss * (length - 1) + loss) / length
    if avg_loss < EPS:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _macd(values: Sequence[float]) -> Tuple[Optional[float], Optional[float], Optional[float]]:
    if len(values) < 35:
        return None, None, None
    macd_series: List[float] = []
    for end in range(26, len(values) + 1):
        sub = values[:end]
        e12 = _ema(sub, 12)
        e26 = _ema(sub, 26)
        if e12 is not None and e26 is not None:
            macd_series.append(e12 - e26)
    if not macd_series:
        return None, None, None
    line = macd_series[-1]
    signal = _ema(macd_series, min(9, len(macd_series)))
    hist = line - signal if signal is not None else None
    return line, signal, hist


def _stochastic(candles: Sequence[CandlePoint], length: int = 14) -> Tuple[Optional[float], Optional[float]]:
    if len(candles) < length:
        return None, None
    window = candles[-length:]
    highest = max(c.high for c in window)
    lowest = min(c.low for c in window)
    if abs(highest - lowest) < EPS:
        k = 50.0
    else:
        k = (candles[-1].close - lowest) / (highest - lowest) * 100.0
    # quick %D from last three %K values
    ks = []
    for i in range(max(length, len(candles) - 2), len(candles) + 1):
        w = candles[max(0, i - length) : i]
        if len(w) < length:
            continue
        hi = max(c.high for c in w)
        lo = min(c.low for c in w)
        ks.append(50.0 if abs(hi - lo) < EPS else (w[-1].close - lo) / (hi - lo) * 100.0)
    d = sum(ks[-3:]) / min(3, len(ks)) if ks else k
    return k, d


def _vwap(candles: Sequence[CandlePoint], length: int = 50) -> Optional[float]:
    if not candles:
        return None
    window = candles[-min(length, len(candles)) :]
    pv = 0.0
    vol = 0.0
    for c in window:
        typical = (c.high + c.low + c.close) / 3.0
        pv += typical * max(c.volume, 0.0)
        vol += max(c.volume, 0.0)
    if vol < EPS:
        return None
    return pv / vol


def _bollinger_width(values: Sequence[float], length: int = 20, mult: float = 2.0) -> Optional[float]:
    if len(values) < length:
        return None
    window = list(values[-length:])
    mid = sum(window) / length
    if abs(mid) < EPS:
        return None
    sd = statistics.pstdev(window)
    upper = mid + mult * sd
    lower = mid - mult * sd
    return (upper - lower) / mid * 100.0


def _adx(candles: Sequence[CandlePoint], length: int = 14) -> Optional[float]:
    if len(candles) < length + 2:
        return None
    trs: List[float] = []
    pdm: List[float] = []
    ndm: List[float] = []
    for i in range(1, len(candles)):
        cur = candles[i]
        prev = candles[i - 1]
        up = cur.high - prev.high
        down = prev.low - cur.low
        pdm.append(up if up > down and up > 0 else 0.0)
        ndm.append(down if down > up and down > 0 else 0.0)
        trs.append(max(cur.high - cur.low, abs(cur.high - prev.close), abs(cur.low - prev.close)))
    dxs: List[float] = []
    for i in range(length, len(trs) + 1):
        tr = sum(trs[i - length : i])
        if tr < EPS:
            continue
        pdi = 100.0 * sum(pdm[i - length : i]) / tr
        ndi = 100.0 * sum(ndm[i - length : i]) / tr
        denom = pdi + ndi
        if denom > EPS:
            dxs.append(100.0 * abs(pdi - ndi) / denom)
    return sum(dxs[-length:]) / min(length, len(dxs)) if dxs else None


def _pivots(candles: Sequence[CandlePoint], left: int = 3, right: int = 3) -> Tuple[List[Tuple[int, float]], List[Tuple[int, float]]]:
    highs: List[Tuple[int, float]] = []
    lows: List[Tuple[int, float]] = []
    n = len(candles)
    if n < left + right + 1:
        return highs, lows
    for i in range(left, n - right):
        h = candles[i].high
        l = candles[i].low
        if all(h >= candles[j].high for j in range(i - left, i + right + 1) if j != i):
            highs.append((i, h))
        if all(l <= candles[j].low for j in range(i - left, i + right + 1) if j != i):
            lows.append((i, l))
    return highs, lows


def _cluster_levels(levels: Sequence[Tuple[int, float]], price: float, atr: float, n: int = 6) -> List[Dict[str, Any]]:
    if not levels:
        return []
    tolerance = max(abs(price) * 0.0025, atr * 0.6, EPS)
    clusters: List[Dict[str, Any]] = []
    for idx, level in sorted(levels, key=lambda x: x[1]):
        placed = False
        for cluster in clusters:
            if abs(level - cluster["level"]) <= tolerance:
                touches = cluster["touches"] + 1
                cluster["level"] = (cluster["level"] * cluster["touches"] + level) / touches
                cluster["touches"] = touches
                cluster["last_index"] = max(cluster["last_index"], idx)
                placed = True
                break
        if not placed:
            clusters.append({"level": level, "touches": 1, "last_index": idx})
    for c in clusters:
        distance_pct = abs(c["level"] - price) / max(abs(price), EPS) * 100.0
        recency = c["last_index"] / max(1, len(levels))
        c["score"] = c["touches"] * 18.0 + max(0.0, 30.0 - distance_pct * 5.0) + recency * 10.0
        c["distance_pct"] = distance_pct
    return sorted(clusters, key=lambda x: x["score"], reverse=True)[:n]


def _nearest_level(levels: Sequence[Dict[str, Any]], price: float, above: bool) -> Optional[Dict[str, Any]]:
    candidates = [l for l in levels if (l["level"] >= price if above else l["level"] <= price)]
    if not candidates:
        return None
    return min(candidates, key=lambda l: abs(l["level"] - price))


def _contraction_count(candles: Sequence[CandlePoint], lookback: int = 40) -> int:
    if len(candles) < 12:
        return 0
    window = candles[-min(lookback, len(candles)) :]
    # Split into up to four blocks and count shrinking high-low ranges.
    blocks = []
    block_size = max(3, len(window) // 4)
    for start in range(0, len(window), block_size):
        block = window[start : start + block_size]
        if len(block) >= 3:
            blocks.append(max(c.high for c in block) - min(c.low for c in block))
    count = 0
    for prev, cur in zip(blocks, blocks[1:]):
        if cur < prev * 0.82:
            count += 1
    return count


def _volume_profile(candles: Sequence[CandlePoint], bins: int = 24) -> Dict[str, Any]:
    if not candles:
        return {}
    hi = max(c.high for c in candles)
    lo = min(c.low for c in candles)
    if abs(hi - lo) < EPS:
        return {"poc": candles[-1].close, "vah": candles[-1].close, "val": candles[-1].close, "bins": []}
    buckets = [0.0 for _ in range(bins)]
    for c in candles:
        typical = (c.high + c.low + c.close) / 3.0
        idx = min(bins - 1, max(0, int((typical - lo) / (hi - lo) * bins)))
        buckets[idx] += max(c.volume, 0.0)
    max_idx = max(range(bins), key=lambda i: buckets[i])
    total = sum(buckets) or EPS
    # Build 70% value area around POC.
    low_idx = high_idx = max_idx
    covered = buckets[max_idx]
    while covered / total < 0.70 and (low_idx > 0 or high_idx < bins - 1):
        left = buckets[low_idx - 1] if low_idx > 0 else -1.0
        right = buckets[high_idx + 1] if high_idx < bins - 1 else -1.0
        if right >= left:
            high_idx += 1
            covered += buckets[high_idx]
        else:
            low_idx -= 1
            covered += buckets[low_idx]
    step = (hi - lo) / bins
    bin_rows = [
        {"price": lo + (i + 0.5) * step, "volume": buckets[i], "share": buckets[i] / total}
        for i in range(bins)
    ]
    return {
        "poc": lo + (max_idx + 0.5) * step,
        "vah": lo + (high_idx + 1.0) * step,
        "val": lo + low_idx * step,
        "bins": bin_rows,
    }


def _wick_rejection(candle: CandlePoint) -> Dict[str, float]:
    body = abs(candle.close - candle.open)
    rng = max(candle.high - candle.low, EPS)
    upper = candle.high - max(candle.open, candle.close)
    lower = min(candle.open, candle.close) - candle.low
    return {
        "upper_wick_pct": upper / rng * 100.0,
        "lower_wick_pct": lower / rng * 100.0,
        "body_pct": body / rng * 100.0,
    }


def _bid_ask_imbalance(orderbook: Dict[str, Any]) -> Optional[float]:
    bids = orderbook.get("bids") or orderbook.get("bid") or []
    asks = orderbook.get("asks") or orderbook.get("ask") or []
    try:
        bid_size = sum(float(row[1]) for row in bids[:10])
        ask_size = sum(float(row[1]) for row in asks[:10])
    except Exception:
        return None
    total = bid_size + ask_size
    if total < EPS:
        return None
    return (bid_size - ask_size) / total


def _infer_open_interest_change(context: MarketContext) -> Optional[float]:
    if context.open_interest is not None and context.open_interest_prev:
        return _pct(float(context.open_interest), float(context.open_interest_prev))
    edge = context.edge or {}
    for key in ("open_interest_change_pct", "oi_change_pct"):
        if key in edge:
            return _safe_float(edge.get(key))
    return None


def compute_features(context: MarketContext) -> Dict[str, Any]:
    candles = list(context.candles)
    if len(candles) < 2:
        raise ValueError("scanner needs at least two candles")

    closes = [c.close for c in candles]
    highs = [c.high for c in candles]
    lows = [c.low for c in candles]
    volumes = [c.volume for c in candles]
    last = candles[-1]
    prev = candles[-2]
    atr = _atr(candles, 14) or max(last.high - last.low, abs(last.close) * 0.002, EPS)
    atr_pct = atr / max(abs(last.close), EPS) * 100.0

    pivot_highs, pivot_lows = _pivots(candles)
    high_levels = _cluster_levels(pivot_highs, last.close, atr)
    low_levels = _cluster_levels(pivot_lows, last.close, atr)
    all_level_candidates = high_levels + low_levels
    resistance = _nearest_level(all_level_candidates, last.close, above=True) or (high_levels[0] if high_levels else None)
    support = _nearest_level(all_level_candidates, last.close, above=False) or (low_levels[0] if low_levels else None)
    latest_pivot_high = pivot_highs[-1][1] if pivot_highs else max(highs[-20:])
    latest_pivot_low = pivot_lows[-1][1] if pivot_lows else min(lows[-20:])

    ema8 = _ema(closes, min(8, len(closes)))
    ema21 = _ema(closes, min(21, len(closes)))
    ema50 = _ema(closes, min(50, len(closes)))
    ema200 = _ema(closes, min(200, len(closes)))
    sma20 = _sma(closes, min(20, len(closes)))
    sma50 = _sma(closes, min(50, len(closes)))
    vwap = _vwap(candles)
    rsi = _rsi(closes)
    macd_line, macd_signal, macd_hist = _macd(closes)
    stoch_k, stoch_d = _stochastic(candles)
    bb_width = _bollinger_width(closes)
    adx = _adx(candles)
    volume_sma = _sma(volumes, min(20, len(volumes))) or max(sum(volumes) / len(volumes), EPS)
    volume_ratio = last.volume / max(volume_sma, EPS)

    avg_range_recent = sum(_true_ranges(candles[-10:])) / min(10, len(candles))
    avg_range_prev = sum(_true_ranges(candles[-30:-10])) / max(1, len(candles[-30:-10])) if len(candles) > 20 else avg_range_recent
    range_compression = avg_range_recent / max(avg_range_prev, EPS)
    contraction_count = _contraction_count(candles)
    wicks = _wick_rejection(last)

    res_level = resistance["level"] if resistance else latest_pivot_high
    sup_level = support["level"] if support else latest_pivot_low
    resistance_distance_pct = (res_level - last.close) / max(abs(last.close), EPS) * 100.0
    support_distance_pct = (last.close - sup_level) / max(abs(last.close), EPS) * 100.0
    near_resistance = abs(res_level - last.close) <= max(atr * 0.7, abs(last.close) * 0.0025)
    near_support = abs(last.close - sup_level) <= max(atr * 0.7, abs(last.close) * 0.0025)
    breakout_above_resistance = prev.close <= res_level and last.close > res_level
    support_break = prev.close >= sup_level and last.close < sup_level
    rejection_at_resistance = near_resistance and wicks["upper_wick_pct"] > 45.0 and last.close < last.open
    rejection_at_support = near_support and wicks["lower_wick_pct"] > 45.0 and last.close > last.open

    higher_lows = False
    lower_highs = False
    if len(pivot_lows) >= 3:
        higher_lows = pivot_lows[-1][1] > pivot_lows[-2][1] > pivot_lows[-3][1]
    if len(pivot_highs) >= 3:
        lower_highs = pivot_highs[-1][1] < pivot_highs[-2][1] < pivot_highs[-3][1]

    spread_pct = None
    ticker = context.ticker or {}
    bid = _safe_float(ticker.get("bid") or ticker.get("best_bid"), 0.0)
    ask = _safe_float(ticker.get("ask") or ticker.get("best_ask"), 0.0)
    if bid > 0 and ask > 0:
        spread_pct = (ask - bid) / ((ask + bid) / 2.0) * 100.0

    profile = _volume_profile(candles[-min(len(candles), 120) :])
    imbalance = _bid_ask_imbalance(context.orderbook or {})
    funding_rate = context.funding_rate
    if funding_rate is None:
        funding_rate = _safe_float((context.edge or {}).get("funding_rate"), 0.0) if (context.edge or {}).get("funding_rate") is not None else None
    oi_change = _infer_open_interest_change(context)

    vcp_score = 0.0
    if contraction_count:
        vcp_score += min(45.0, contraction_count * 15.0)
    if range_compression < 0.8:
        vcp_score += 20.0
    if volume_ratio < 0.9:
        vcp_score += 15.0
    if higher_lows:
        vcp_score += 10.0
    if near_resistance:
        vcp_score += 10.0

    bullish_trend = bool(ema8 and ema21 and ema50 and last.close > ema8 > ema21 > ema50)
    bearish_trend = bool(ema8 and ema21 and ema50 and last.close < ema8 < ema21 < ema50)
    trend_pullback_long = bool(bullish_trend and last.low <= (ema21 or last.low) * 1.004 and last.close > last.open)
    trend_pullback_short = bool(bearish_trend and last.high >= (ema21 or last.high) * 0.996 and last.close < last.open)

    price_change_pct = _pct(last.close, prev.close)
    features: Dict[str, Any] = {
        "symbol": context.symbol,
        "timeframe": context.timeframe,
        "exchange": context.exchange,
        "open": last.open,
        "high": last.high,
        "low": last.low,
        "close": last.close,
        "prev_close": prev.close,
        "volume": last.volume,
        "volume_sma": volume_sma,
        "volume_ratio": volume_ratio,
        "price_change_pct": price_change_pct,
        "atr": atr,
        "atr_pct": atr_pct,
        "range_compression": range_compression,
        "contraction_count": contraction_count,
        "vcp_score": vcp_score,
        "ema_8": ema8,
        "ema_21": ema21,
        "ema_50": ema50,
        "ema_200": ema200,
        "sma_20": sma20,
        "sma_50": sma50,
        "ema_stack_bullish": bullish_trend,
        "ema_stack_bearish": bearish_trend,
        "trend_pullback_long": trend_pullback_long,
        "trend_pullback_short": trend_pullback_short,
        "vwap": vwap,
        "vwap_distance_pct": _pct(last.close, vwap) if vwap else None,
        "rsi": rsi,
        "macd": macd_line,
        "macd_signal": macd_signal,
        "macd_hist": macd_hist,
        "macd_bullish": bool(macd_line is not None and macd_signal is not None and macd_line > macd_signal),
        "macd_bearish": bool(macd_line is not None and macd_signal is not None and macd_line < macd_signal),
        "stoch_k": stoch_k,
        "stoch_d": stoch_d,
        "bb_width_pct": bb_width,
        "adx": adx,
        "pivot_high": latest_pivot_high,
        "pivot_low": latest_pivot_low,
        "support": sup_level,
        "resistance": res_level,
        "support_distance_pct": support_distance_pct,
        "resistance_distance_pct": resistance_distance_pct,
        "near_support": near_support,
        "near_resistance": near_resistance,
        "breakout_above_resistance": breakout_above_resistance,
        "support_break": support_break,
        "rejection_at_resistance": rejection_at_resistance,
        "rejection_at_support": rejection_at_support,
        "higher_lows": higher_lows,
        "lower_highs": lower_highs,
        "upper_wick_pct": wicks["upper_wick_pct"],
        "lower_wick_pct": wicks["lower_wick_pct"],
        "body_pct": wicks["body_pct"],
        "spread_pct": spread_pct,
        "bid_ask_imbalance": imbalance,
        "funding_rate": funding_rate,
        "open_interest_change_pct": oi_change,
        "volume_profile_poc": profile.get("poc"),
        "volume_profile_vah": profile.get("vah"),
        "volume_profile_val": profile.get("val"),
        "support_levels": low_levels,
        "resistance_levels": high_levels,
        "volume_profile": profile,
        "chart_candles": [
            {"t": c.timestamp, "o": c.open, "h": c.high, "l": c.low, "c": c.close, "v": c.volume}
            for c in candles[-120:]
        ],
    }
    return features


def _resolve_value(value: Any, features: Dict[str, Any]) -> Any:
    if isinstance(value, str) and value in features:
        return features.get(value)
    if isinstance(value, str):
        # Allow string numbers from frontend rule builder.
        try:
            return float(value)
        except Exception:
            return value
    return value


def _compare(actual: Any, op: str, expected: Any, expected2: Any = None, *, tolerance_pct: float = 0.35) -> bool:
    if op == "truthy":
        return bool(actual)
    if op == "falsy":
        return not bool(actual)

    if op in {"==", "!="}:
        result = actual == expected
        return result if op == "==" else not result

    a = _safe_float(actual, float("nan"))
    b = _safe_float(expected, float("nan"))
    c = _safe_float(expected2, float("nan")) if expected2 is not None else None
    if math.isnan(a) or math.isnan(b):
        return False

    if op == ">":
        return a > b
    if op == ">=":
        return a >= b
    if op == "<":
        return a < b
    if op == "<=":
        return a <= b
    if op == "between":
        if isinstance(expected, (list, tuple)) and len(expected) >= 2:
            lo = _safe_float(expected[0])
            hi = _safe_float(expected[1])
        else:
            lo = min(b, c if c is not None and not math.isnan(c) else b)
            hi = max(b, c if c is not None and not math.isnan(c) else b)
        return lo <= a <= hi
    if op == "outside":
        if isinstance(expected, (list, tuple)) and len(expected) >= 2:
            lo = _safe_float(expected[0])
            hi = _safe_float(expected[1])
        else:
            lo = min(b, c if c is not None and not math.isnan(c) else b)
            hi = max(b, c if c is not None and not math.isnan(c) else b)
        return a < lo or a > hi
    if op == "near":
        return abs(a - b) / max(abs(b), EPS) * 100.0 <= tolerance_pct
    if op == "not_near":
        return abs(a - b) / max(abs(b), EPS) * 100.0 > tolerance_pct
    return False


def evaluate_condition(condition: ScannerCondition, features: Dict[str, Any]) -> ConditionMatch:
    actual = features.get(condition.field)
    expected = _resolve_value(condition.value, features)
    expected2 = _resolve_value(condition.value2, features)

    passed: bool
    if condition.op == "crosses_above":
        previous = features.get("prev_" + condition.field, features.get("prev_close"))
        passed = _compare(previous, "<=", expected) and _compare(actual, ">", expected)
    elif condition.op == "crosses_below":
        previous = features.get("prev_" + condition.field, features.get("prev_close"))
        passed = _compare(previous, ">=", expected) and _compare(actual, "<", expected)
    else:
        passed = _compare(actual, condition.op, expected, expected2)

    label = condition.label or f"{condition.field} {condition.op} {condition.value}"
    reason = f"{label}: actual={_format_value(actual)}, expected={_format_value(expected)}"
    return ConditionMatch(
        field=condition.field,
        op=condition.op,
        passed=passed,
        required=condition.required,
        weight=condition.weight,
        actual=actual,
        expected=expected,
        label=label,
        reason=reason,
    )


def _format_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def _confidence(score: float) -> str:
    if score >= 90:
        return "very_high"
    if score >= 78:
        return "high"
    if score >= 62:
        return "medium"
    return "low"


def _infer_side(rule: ScannerRule, features: Dict[str, Any]) -> str:
    if rule.side_bias in {"long", "short"}:
        return rule.side_bias
    long_score = 0.0
    short_score = 0.0
    if features.get("breakout_above_resistance"):
        long_score += 20
    if features.get("rejection_at_support"):
        long_score += 15
    if features.get("ema_stack_bullish"):
        long_score += 12
    if features.get("trend_pullback_long"):
        long_score += 10
    if features.get("macd_bullish"):
        long_score += 5
    if _safe_float(features.get("bid_ask_imbalance"), 0.0) > 0.15:
        long_score += 6

    if features.get("support_break"):
        short_score += 20
    if features.get("rejection_at_resistance"):
        short_score += 15
    if features.get("ema_stack_bearish"):
        short_score += 12
    if features.get("trend_pullback_short"):
        short_score += 10
    if features.get("macd_bearish"):
        short_score += 5
    if _safe_float(features.get("bid_ask_imbalance"), 0.0) < -0.15:
        short_score += 6

    # VCP/breakout names are usually long unless explicit short.
    name = rule.name.lower()
    if "short" in name or "breakdown" in name:
        short_score += 10
    if "long" in name or "breakout" in name or "vcp" in name:
        long_score += 10

    if long_score == short_score:
        return "neutral"
    return "long" if long_score > short_score else "short"


def build_ticket(hit_side: str, features: Dict[str, Any], context: MarketContext, rule: ScannerRule) -> SuggestedTicket:
    entry = _safe_float(features.get("close"))
    atr = max(_safe_float(features.get("atr"), abs(entry) * 0.005), EPS)
    support = _safe_float(features.get("support"), entry - 1.6 * atr)
    resistance = _safe_float(features.get("resistance"), entry + 1.6 * atr)
    pivot_low = _safe_float(features.get("pivot_low"), support)
    pivot_high = _safe_float(features.get("pivot_high"), resistance)

    if hit_side == "short":
        side = "short"
        structure_stop = max(resistance, pivot_high, entry + 1.15 * atr)
        stop = structure_stop + 0.15 * atr
        risk = max(stop - entry, atr * 0.45)
        targets = [entry - risk * 1.5, entry - risk * 2.5, entry - risk * 4.0]
        invalidation = "Short invalidates on acceptance back above the rejection/supply zone."
    else:
        side = "long"
        structure_stop = min(support, pivot_low, entry - 1.15 * atr)
        stop = structure_stop - 0.15 * atr
        risk = max(entry - stop, atr * 0.45)
        targets = [entry + risk * 1.5, entry + risk * 2.5, entry + risk * 4.0]
        invalidation = "Long invalidates on acceptance back below the reclaimed support/demand zone."

    take_profits = [
        {"label": "TP1", "price": round(targets[0], 8), "size_pct": 35, "reason": "De-risk at first impulse target near 1.5R."},
        {"label": "TP2", "price": round(targets[1], 8), "size_pct": 35, "reason": "Scale out around expansion target near 2.5R."},
        {"label": "Runner", "price": round(targets[2], 8), "size_pct": 30, "reason": "Leave runner for measured move / liquidity sweep."},
    ]

    management = [
        "Validate spread/liquidity immediately before live preview.",
        "After TP1 fill, arm breakeven or trail below/above the last structure pivot.",
        "If price stalls for the configured time stop, cancel remaining entry and reassess.",
    ]
    if features.get("funding_rate") is not None:
        management.append(f"Futures funding context: {features.get('funding_rate')}; reduce size if funding is crowded against the setup.")
    if features.get("spread_pct") is not None and _safe_float(features.get("spread_pct")) > 0.20:
        management.append("Spread is wide; use limit/stop-limit execution or reduce risk.")

    rr = abs(targets[1] - entry) / max(abs(entry - stop), EPS)
    return SuggestedTicket(
        mode="futures",
        exchange=context.exchange,
        symbol=context.symbol,
        side=side,  # type: ignore[arg-type]
        order_type="limit",
        entry=round(entry, 8),
        stop_loss=round(stop, 8),
        take_profits=take_profits,
        risk_reward=round(rr, 3),
        leverage=_safe_float(rule.metadata.get("default_leverage"), 1.0) if rule.metadata else 1.0,
        margin_mode=str(rule.metadata.get("margin_mode", "cross")) if rule.metadata else "cross",
        reduce_only_exits=True,
        trailing={"enabled": True, "arm_after": "TP1", "trail_by": "1.1 ATR or last pivot", "atr": round(atr, 8)},
        breakeven={"enabled": True, "after": "TP1", "offset_ticks": 0},
        sizing={"risk_fraction": rule.metadata.get("risk_fraction", 0.005) if rule.metadata else 0.005, "risk_per_unit": round(abs(entry - stop), 8)},
        invalidation=invalidation,
        management=management,
        route_hints={
            "chart": "/war-room/ui",
            "guardian_plan": "/scanner/hits/{hit_id}/guardian-plan",
            "signal_preview": "/signals/preview",
            "live_preview": "/guardian/live/preview",
            "submit": "/signals/submit",
        },
    )


def evaluate_rule(rule: ScannerRule, context: MarketContext) -> Optional[ScanHit]:
    if not rule.enabled:
        return None
    if rule.symbols and context.symbol not in rule.symbols and "*" not in rule.symbols:
        return None
    if rule.timeframes and context.timeframe not in rule.timeframes:
        return None

    features = compute_features(context)
    condition_results = [evaluate_condition(condition, features) for condition in rule.conditions]
    required_failures = [r for r in condition_results if r.required and not r.passed]
    if required_failures:
        return None

    total_weight = sum(max(0.0, r.weight) for r in condition_results) or 1.0
    passed_weight = sum(max(0.0, r.weight) for r in condition_results if r.passed)
    score = min(100.0, max(0.0, passed_weight / total_weight * 100.0))

    # Add a small contextual bonus/penalty without letting weak rules fake a setup.
    if features.get("volume_ratio") is not None and _safe_float(features.get("volume_ratio")) >= 1.5:
        score = min(100.0, score + 3.0)
    if features.get("spread_pct") is not None and _safe_float(features.get("spread_pct")) > 0.25:
        score = max(0.0, score - 6.0)
    if score < rule.min_score:
        return None

    side = _infer_side(rule, features)
    ticket = build_ticket(side, features, context, rule) if side in {"long", "short"} else None
    reasons = [r.reason for r in condition_results if r.passed]
    if side == "long" and features.get("breakout_above_resistance"):
        reasons.insert(0, "Price broke above mapped resistance with confirmation candle.")
    if side == "short" and features.get("rejection_at_resistance"):
        reasons.insert(0, "Price rejected mapped resistance/supply with upper-wick pressure.")
    if features.get("vcp_score", 0) >= 55:
        reasons.append(f"VCP/compression score is elevated at {features.get('vcp_score'):.1f}.")

    warnings: List[str] = []
    if features.get("spread_pct") is not None and _safe_float(features.get("spread_pct")) > 0.15:
        warnings.append(f"Spread is {features.get('spread_pct'):.3f}%; confirm liquidity before live preview.")
    if context.source not in {"guardian", "bitunix", "ccxt", "war-room"}:
        warnings.append(f"Unknown source '{context.source}'; validate candle provenance before execution.")

    trigger = _build_trigger_summary(rule, side, features)
    return ScanHit(
        exchange=context.exchange,
        source=context.source,
        symbol=context.symbol,
        timeframe=context.timeframe,
        rule_id=rule.id,
        rule_name=rule.name,
        side=side,  # type: ignore[arg-type]
        score=round(score, 2),
        confidence=_confidence(score),  # type: ignore[arg-type]
        price=round(_safe_float(features.get("close")), 8),
        trigger=trigger,
        reasons=reasons[:12],
        warnings=warnings,
        condition_results=condition_results,
        features=features,
        suggested_ticket=ticket,
    )


def _build_trigger_summary(rule: ScannerRule, side: str, features: Dict[str, Any]) -> str:
    snippets: List[str] = []
    if features.get("breakout_above_resistance"):
        snippets.append("close broke resistance")
    if features.get("support_break"):
        snippets.append("close lost support")
    if features.get("rejection_at_resistance"):
        snippets.append("upper-wick rejection at resistance")
    if features.get("rejection_at_support"):
        snippets.append("lower-wick rejection at support")
    if features.get("contraction_count", 0):
        snippets.append(f"{features.get('contraction_count')} contractions")
    if features.get("volume_ratio") is not None:
        snippets.append(f"volume {features.get('volume_ratio'):.2f}x")
    if features.get("atr_pct") is not None:
        snippets.append(f"ATR {features.get('atr_pct'):.2f}%")
    if not snippets:
        snippets.append("rule conditions matched")
    direction = side.upper() if side != "neutral" else "WATCH"
    return f"{direction}: {rule.name} — " + ", ".join(snippets[:5])


def preset_rules() -> List[ScannerRule]:
    """Opinionated live-ready scanner presets.

    They are intentionally explainable and conservative enough to promote into
    Guardian/signals preview instead of sending direct orders.
    """
    return [
        ScannerRule(
            id="preset_volume_spike_long",
            name="Volume Spike Momentum Long",
            description="Large relative-volume candle with constructive VWAP/trend context.",
            side_bias="long",
            min_score=72,
            tags=["momentum", "volume", "long"],
            conditions=[
                ScannerCondition(field="volume_ratio", op=">=", value=2.0, weight=2.0, label="relative volume >= 2x"),
                ScannerCondition(field="price_change_pct", op=">", value=0.15, weight=1.0, label="green impulse candle"),
                ScannerCondition(field="close", op=">", value="vwap", weight=1.0, required=False, label="close above VWAP"),
                ScannerCondition(field="spread_pct", op="<", value=0.20, weight=1.0, required=False, label="spread acceptable"),
            ],
        ),
        ScannerRule(
            id="preset_breakout_long",
            name="Resistance Breakout Long",
            description="Close clears mapped resistance/pivot with volume and trend support.",
            side_bias="long",
            min_score=70,
            tags=["breakout", "long", "structure"],
            conditions=[
                ScannerCondition(field="breakout_above_resistance", op="truthy", weight=2.5, label="breakout above mapped resistance"),
                ScannerCondition(field="volume_ratio", op=">=", value=1.25, weight=1.5, label="volume confirmation"),
                ScannerCondition(field="ema_stack_bullish", op="truthy", weight=1.0, required=False, label="bullish EMA stack"),
                ScannerCondition(field="rsi", op="between", value=[45, 78], weight=0.75, required=False, label="RSI constructive, not extreme"),
            ],
        ),
        ScannerRule(
            id="preset_vcp_breakout_watch",
            name="VCP Breakout Watch",
            description="Volatility contraction pattern near resistance with drying volume.",
            side_bias="long",
            min_score=70,
            tags=["vcp", "compression", "long"],
            conditions=[
                ScannerCondition(field="contraction_count", op=">=", value=2, weight=1.5, label="multiple range contractions"),
                ScannerCondition(field="range_compression", op="<", value=0.92, weight=1.25, label="recent range is compressed"),
                ScannerCondition(field="volume_ratio", op="<", value=1.25, weight=1.0, label="volume not overheated"),
                ScannerCondition(field="near_resistance", op="truthy", weight=1.0, required=False, label="coiled near resistance"),
                ScannerCondition(field="higher_lows", op="truthy", weight=0.8, required=False, label="higher lows into pivot"),
            ],
        ),
        ScannerRule(
            id="preset_rejection_short",
            name="Rejection Short at Supply",
            description="Upper-wick rejection at resistance with bearish confirmation.",
            side_bias="short",
            min_score=72,
            tags=["rejection", "short", "supply"],
            conditions=[
                ScannerCondition(field="rejection_at_resistance", op="truthy", weight=2.0, label="upper wick rejection at resistance"),
                ScannerCondition(field="volume_ratio", op=">=", value=1.1, weight=1.0, required=False, label="participation on rejection"),
                ScannerCondition(field="rsi", op=">", value=55, weight=0.8, required=False, label="RSI extended enough to fade"),
                ScannerCondition(field="macd_bearish", op="truthy", weight=0.8, required=False, label="MACD bearish/rolling"),
            ],
        ),
        ScannerRule(
            id="preset_trend_continuation_long",
            name="Trend Continuation Pullback Long",
            description="Bullish EMA stack, constructive pullback, continuation candle.",
            side_bias="long",
            min_score=70,
            tags=["trend", "pullback", "long"],
            conditions=[
                ScannerCondition(field="ema_stack_bullish", op="truthy", weight=1.5, label="bullish EMA stack"),
                ScannerCondition(field="trend_pullback_long", op="truthy", weight=1.5, label="pullback held dynamic support"),
                ScannerCondition(field="rsi", op="between", value=[42, 72], weight=0.75, required=False, label="RSI pullback reset"),
                ScannerCondition(field="close", op=">", value="vwap", weight=0.75, required=False, label="close above VWAP"),
            ],
        ),
        ScannerRule(
            id="preset_liquidation_risk_short",
            name="Crowded Long Liquidation-Risk Short",
            description="Crowded positive-funding context with resistance rejection or support loss.",
            side_bias="short",
            min_score=70,
            tags=["futures", "funding", "liquidation", "short"],
            conditions=[
                ScannerCondition(field="funding_rate", op=">", value=0.00015, weight=1.0, required=False, label="positive funding/crowded longs"),
                ScannerCondition(field="open_interest_change_pct", op=">", value=1.0, weight=1.0, required=False, label="open interest rising"),
                ScannerCondition(field="rejection_at_resistance", op="truthy", weight=1.5, required=False, label="resistance rejection"),
                ScannerCondition(field="support_break", op="truthy", weight=1.5, required=False, label="support break"),
                ScannerCondition(field="volume_ratio", op=">=", value=1.2, weight=0.8, required=False, label="liquidation-volume expansion"),
            ],
        ),
        ScannerRule(
            id="preset_support_reclaim_long",
            name="Sweep-Reclaim Long",
            description="Lower-wick sweep at support with reclaim candle.",
            side_bias="long",
            min_score=72,
            tags=["sweep", "reclaim", "long"],
            conditions=[
                ScannerCondition(field="rejection_at_support", op="truthy", weight=2.0, label="lower-wick rejection at support"),
                ScannerCondition(field="lower_wick_pct", op=">=", value=42, weight=1.0, label="large lower wick"),
                ScannerCondition(field="close", op=">", value="open", weight=1.0, label="reclaimed into green close"),
                ScannerCondition(field="volume_ratio", op=">=", value=1.0, weight=0.6, required=False, label="volume participates"),
            ],
        ),
    ]
