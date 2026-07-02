# Sentinel Chain Trading War Room

The Trading War Room adds an operator-facing charting and decision-support layer to Sentinel Chain. It is paper-first and does not bypass the existing risk, approval, or live-execution gates.

## UI route

After installing and restarting Sentinel Chain, open:

```text
http://127.0.0.1:8004/war-room/ui
```

The classic UI remains available at `/ui`.

## Backend routes

- `GET /war-room/ui` serves the War Room UI.
- `GET /war-room/demo?symbol=BTCUSDT&timeframe=15m&bars=280` returns deterministic demo candles plus full analysis.
- `POST /war-room/analyze` accepts OHLCV candles and returns overlays, indicators, patterns, scores, and plans.
- `POST /war-room/ticket` builds a paper-first Sentinel Chain signal payload from the current map.
- `POST /war-room/backtest` runs a lightweight EMA/RSI bracket backtest for quick strategy triage.
- `GET /war-room/features` lists feature flags and trading playbooks.

## Auto-charting features

The backend currently maps:

- adaptive pivot highs/lows and inflection points
- clustered support and resistance zones with touch count, volume, recency, proximity, and polarity scoring
- support/resistance trendlines using pairwise pivot line scoring
- volume profile with POC, value area high/low, high-volume nodes, and low-volume nodes
- Fibonacci anchors and extension/retracement levels
- fair value gaps / imbalance zones
- simple bullish and bearish order-block zones
- candlestick patterns such as engulfing candles, hammers, shooting stars, doji, and marubozu candles
- chart structures such as double tops/bottoms, triangles, wedges, flags, flat bases, cup-with-handle heuristics, and volatility squeeze
- RSI and MACD divergence
- break of structure and market-state classification
- long/short confidence scoring
- bracket plan with entry zone, stop, staged targets, risk sizing, breakeven, and trailing management notes

## Data format

`POST /war-room/analyze` expects:

```json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "candles": [
    {"time": 0, "open": 100, "high": 105, "low": 98, "close": 103, "volume": 1200}
  ],
  "settings": {
    "risk": {"account_equity": 10000, "risk_pct": 1}
  }
}
```

## Safety notes

The War Room is decision support. It explains when to trade, how to bracket the trade, and why the setup is or is not attractive. Paper submission still goes through Sentinel Chain's existing `/webhooks/tradingview` path and the bot's existing risk controls.
