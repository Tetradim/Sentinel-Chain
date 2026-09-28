# Sentinel Chain Guardian Backend Wiring

This pass turns `/guardian/ui` from a standalone TP/SL planning surface into a backend-wired Guardian operator console while preserving the dark purple/gold Guardian theme and the paper-first safety posture.

## Files changed

- `src/sentinel_chain/app.py`
  - Adds a first-party `/guardian/ui` route inside `create_app()` that serves `sentinel_guardian.html` and sets the same `auto_crypto_operator_session` cookie as the legacy `/ui` route.
  - This lets Guardian call protected operator endpoints such as `/control/halt`, `/control/resume`, `/signals/submit`, `/approvals/*`, `/market/price`, and `/brackets/*` from the browser.

- `src/sentinel_chain/static/sentinel_guardian.html`
  - Expands the left rail from five planning shortcuts into real view tabs.
  - Adds global status and control strip for API state, paper engine state, approval mode, live-trading lock, halt reason, refresh, auto-refresh, halt, and resume.
  - Adds backend-matched view panels for Dashboard, Signals, Trading Desk, Risk, VCP, Lines, Portfolio, Strategies, Exchanges, War Room, Audit, and Data.

- `src/sentinel_chain/static/sentinel_guardian.css`
  - Adds responsive operator-console layout styles for the new tab system, global status ribbon, tables, strategy cards, compact action lists, KPI cards, form grids, and venue/audit panels.
  - Keeps the Guardian dark theme, purple accents, gold highlights, glass panels, and paper-first visual language.

- `src/sentinel_chain/static/sentinel_guardian.js`
  - Adds a Sentinel API helper using `credentials: "same-origin"`.
  - Adds state sync from `/ui/state` and companion loaders for exchanges, platforms, strategy presets, brackets, bracket health/risk/coverage, audit, and War Room features.
  - Converts rail items into real tabs instead of scroll shortcuts/dialog-only actions.
  - Adds UI handlers for protected paper/operator routes.

## New UI tabs and feature inventory

### Chart

Existing Guardian chart retained and connected to the new shell.

- Interactive candle chart.
- Long/short TP/SL bracket drawing.
- Entry, stop, TP1, TP2 drag handles.
- Trendline, horizontal line, risk zone, eraser, clear/reset tools.
- Local bracket calculator for R:R, position sizing, notional, fees, liquidation estimate, ATR stop check, MAE/MFE replay, and VCP score.
- Links to Classic UI and standalone War Room.

### Dashboard

Backend source: `/ui/state`, `/exchanges`, `/exchanges/platforms`, `/strategy-presets`, `/audit`.

- Operator snapshot cards.
- Signal inbox preview.
- Risk state ring summary.
- Exchange fabric status.
- Runtime table for control, approvals, runtime config, and protection state.
- Audit feed preview.
- Mode pills for webhook/approval/paper flow.
- Last refresh indicator.

### Signals

Backend source: `/signals/parse-text`, `/signals/preview-text`, `/signals/submit-text`, `/signals`, `/approvals`, `/approvals/{signal_id}/approve`, `/approvals/{signal_id}/reject`.

- Discord / TradingView / Operator channel selector.
- Text signal parser.
- Sample signal generator from current Guardian bracket.
- Parse, Preview Risk, Submit Paper Signal actions.
- Pending approvals list.
- Approve/reject actions.
- Reject reason input.
- Payload preview and copy.
- Signal history table.
- Signal search/filter.
- Load signal into Trading Desk ticket.

### Trading Desk

Backend source: `/signals/preview`, `/signals/submit`, `/market/price/preview`, `/market/price`, `/ui/state`.

- Paper order ticket builder.
- Strategy selector from `/strategy-presets`.
- BTC / ETH / SOL quick pair buttons.
- Buy/Sell side selector.
- Quote/base/risk sizing mode.
- Size presets: `$25`, `$100`, Max Order, Remaining Cap.
- Entry price, stop, take profit, trailing stop, trail activation, breakeven fields.
- Build Alert.
- Preview Risk.
- Submit to paper/approval flow.
- Copy Alert and Copy JSON.
- Local draft save and Forget Draft.
- Timeframe quick buttons.
- Mark-price preview/apply for paper trigger simulation.
- Positions / Orders toggle table.
- Desk search/filter.
- Order inspect action.

### Risk

Backend source: `/ui/state`, `/futures/risk/preview`, `/brackets`, `/brackets/health`, `/brackets/risk-summary`, `/brackets/coverage`, `/brackets/{signal_id}/breakeven`, `/brackets/{signal_id}/lock-profit`, `/brackets/{signal_id}/cancel`, `/brackets/{signal_id}/close`.

- Risk KPI summary.
- Guardian local guardrail mirror.
- Futures risk backend preview.
- Active bracket ledger.
- Active bracket actions: breakeven, lock profit, cancel bracket, close bracket.
- Account risk cap, daily P&L, worst-case bracket loss, and coverage summary.

### VCP

Backend source: local Guardian candles plus `/backtest/signal` when quick backtesting.

- VCP score dashboard.
- Pivot, final contraction low, contraction count, and volume dry-up summary.
- Contraction list.
- VCP playbook safety notes.
- Build breakout ticket from Guardian bracket.
- Quick Sentinel backtest.
- Load VCP demo.

### Lines

Backend source: local Guardian drawings plus `/war-room/analyze` results when loaded.

- Dedicated drawing inventory tab.
- Activate trendline, horizontal level, and risk-zone tools.
- Copy/clear drawings.
- Nearest local S/R levels.
- War Room S/R level table after Auto Map/Analyze.

### Portfolio

Backend source: `/ui/state`, `/brackets`, `/brackets/coverage`, `/brackets/risk-summary`.

- Export full state JSON.
- Allocation/risk KPIs.
- Daily P&L / equity mini-panel.
- Exposure limits from risk config.
- Positions table.
- Bracket coverage summary.

### Strategies

Backend source: `/strategy-presets`, `/backtest/signal`.

- Strategy preset cards.
- Filters: All / Signals / Grid / DCA.
- Search.
- Sort: name, pinned first, type.
- Pin/unpin local strategies.
- Load Ticket.
- Backtest strategy.
- Import/checklist preview.

### Exchanges

Backend source: `/exchanges`, `/exchanges/platforms`, `/exchanges/{exchange_id}/capabilities`, `/exchanges/{exchange_id}/integration`, `/exchanges/bitunix/futures/tickers`, `/exchanges/bitunix/futures/account`.

- Exchange search.
- Refresh venues.
- Trading platform grid.
- Venue list.
- Capability viewer.
- Integration viewer.
- Copy capability/integration JSON.
- Bitunix futures ticker loader.
- Bitunix account check.

### War Room

Backend source: `/war-room/features`, `/war-room/demo`, `/war-room/analyze`, `/war-room/ticket`, `/war-room/backtest`, `/signals/submit`.

- Auto Map demo.
- Analyze current Guardian candles.
- Feature list: S/R, pivots, trendline scoring, volume profile, FVG, order blocks, candlestick/chart patterns, divergence, BOS/CHOCH, ticket builder, DOM projection.
- How / When / Why panel.
- Build bracket ticket.
- Copy current candles.
- Quick backtest.
- Submit paper signal from War Room ticket.

### Audit

Backend source: `/audit`.

- Audit event table.
- Audit search/filter.
- Refresh audit.
- Export CSV.
- Inspect event into JSON preview.

### Data

Backend source: local parser, embedded Edge sample, `/exchanges/bitunix/futures/klines`.

- Paste JSON/CSV candles.
- Existing paste dialog retained.
- Bitunix candle loader.
- Edge GEX sample loader.
- Copy current candles.
- Current data status and latest candle preview.

## Moved / folded in

- The former standalone Guardian Risk/VCP/Lines/Data rail shortcuts are now actual tab panels.
- Legacy operator Dashboard, Signals, Trading Desk, Strategies, Portfolio, Exchanges, and Audit workflows are folded into the Guardian shell rather than duplicating the legacy `/ui` markup.
- War Room analysis is folded into a Guardian tab while preserving the existing standalone `/war-room/ui` link.

## Removed

- No backend route was removed.
- No live broker submission was added.
- The standalone local paper-plan export remains, but it now sits alongside backend paper/approval flows.

## Still intentionally gated

- Live broker submission remains locked out of the Guardian UI.
- Sentinel Edge streaming is still represented by the embedded/uploaded Edge snapshot loader and can later be replaced by a real stream endpoint.
- Private Bitunix account checks still depend on configured credentials and the operator session cookie.
