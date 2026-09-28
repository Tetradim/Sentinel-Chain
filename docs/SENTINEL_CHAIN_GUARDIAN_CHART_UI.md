# Sentinel Chain Guardian Chart UI Notes

## Design intent

The Guardian Chart UI combines the existing Sentinel Chain futures/war-room direction with a dedicated TP/SL planning surface. The main change is manual chart interaction: the operator can draw trendlines and zones, then drag entry, stop, and target handles directly on the chart.

## Main UI concepts

### Interactive TP/SL bracket

The bracket draws a red risk zone and green reward zone, similar to common charting-platform long/short position tools. Entry, stop, TP1, and TP2 lines are draggable. The right panel mirrors the chart handles as numeric fields.

### Sentinel Guardrails

The guardrail list turns plan checks into pass/warn/fail items:

- correct bracket geometry
- TP1 reward:risk threshold
- account risk percentage
- stop distance measured in ATR
- leverage governor
- estimated liquidation relative to stop
- support/resistance invalidation
- market vs limit style trade-off
- VCP pivot gate
- MAE/MFE replay after bracket start

### VCP / contraction gate

The UI scans recent pivots for high-to-low contraction legs. A cleaner candidate has multiple shrinking pullbacks, decreasing volume, and price near a pivot. For futures, the VCP score is treated as context, not a standalone entry command.

### MAE / MFE replay

Once a bracket exists, the UI replays candles from the bracket start index and reports maximum adverse excursion and maximum favorable excursion in R multiples. This is designed to catch stop placement that sits inside ordinary noise.

### Edge packet loader

The included `data/sentinel-edge-heatmap-SPY-GEX-1782995757698.json` is embedded into the JS as a sample Edge/GEX context. It can be loaded with the **Load Edge GEX** button to verify support/resistance, regime, and risk-score rendering.

## Route integration

The add-on registers:

```text
GET /guardian/health
GET /guardian/ui
GET /guardian/static/sentinel_guardian.css
GET /guardian/static/sentinel_guardian.js
```

The route module is:

```text
src/sentinel_chain/sentinel_guardian_routes.py
```

The installer patches `src/sentinel_chain/app.py` using an idempotent marker block:

```text
# BEGIN SENTINEL CHAIN GUARDIAN CHART ROUTES
# END SENTINEL CHAIN GUARDIAN CHART ROUTES
```

## No-live-execution boundary

The Guardian UI intentionally has no submit-live button and no exchange API routes. It exports JSON only. This keeps the surface safe while still making bracket planning more visual and explicit.
