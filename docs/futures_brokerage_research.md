# Sentinel Chain futures brokerage research notes

Prepared for the futures add-on patch. These notes are meant to guide code review and future adapter work; always re-check live exchange documentation before enabling new venues.

## Existing Sentinel Chain baseline

Sentinel Chain is already designed as a paper-first crypto bot with TradingView/custom alert intake, risk checks, paper fills, bracket exits, audit history, CCXT discovery, Bitunix market-data/backtest helpers, and a backend-served operator UI. Live trading is disabled by default, so this add-on preserves that model and adds dry-run-first futures execution surfaces rather than silently enabling live orders.

The current alert schema already supports futures-relevant fields such as `market_type`, `leverage`, `reduce_only`, staged take-profit targets, absolute/percentage stops, trailing stop settings, breakeven triggers, profit locks, max hold marks, and OCA/OCO group metadata.

## Bitunix USDT futures

Official Bitunix REST pages reviewed for this patch show these native endpoints:

- `POST /api/v1/futures/trade/place_order` for opening or closing futures orders. The reviewed fields include `symbol`, `qty`, `side`, `tradeSide`, `orderType`, `effect`, `reduceOnly`, `clientId`, `positionId`, and embedded `tp*`/`sl*` fields.
- `POST /api/v1/futures/tpsl/place_order` for batch TP/SL orders by `positionId`, requiring at least one TP or SL price and at least one TP or SL quantity.
- `POST /api/v1/futures/tpsl/position/place_order` for whole-position TP/SL orders.
- `GET /api/v1/futures/market/funding_rate` for mark/last price, funding rate, next funding timestamp, funding interval, and funding-rate limits.
- `POST /api/v1/futures/account/change_leverage` and `POST /api/v1/futures/account/change_margin_mode` for account setup.

Bitunix authentication signs a SHA-256 digest using `nonce`, `timestamp`, `apiKey`, sorted query parameters, compact JSON body, and `secretKey`. The add-on reuses Sentinel Chain's existing Bitunix signed-request implementation and only adds mutation body builders around it.

Bitunix help material says the product UI supports trailing stop orders and describes activation price plus retracement percentage behavior. However, the reviewed official REST pages for `place_order`, batch TP/SL, and position TP/SL did not expose a confirmed trailing-stop mutation schema. The patch therefore treats Bitunix trailing stops as Sentinel-managed synthetic exits until a specific official REST endpoint/field map is confirmed.

## CCXT and other futures venues

CCXT documents unified trigger, stop-loss, take-profit, attached stop-loss/take-profit, reduce-only, and trailing order parameters. It also warns that not every exchange supports every conditional order style, so code must inspect capabilities/features and fall back to separate conditional orders or synthetic management.

This add-on's generic venue plan emits CCXT-style `create_order` parameter maps for:

- Attached `stopLoss` / `takeProfit` when a venue advertises support.
- Separate reduce-only conditional exits using `stopLossPrice`, `takeProfitPrice`, or `triggerPrice` when attached exits are not available.
- Trailing exits using `trailingPercent`, `trailingAmount`, and optional `trailingTriggerPrice` only when advertised by the target venue.

Futures venues vary on whether `amount` means base asset quantity, contract count, or quote notional. Any future live CCXT adapter must call `loadMarkets()` and account for `market['contractSize']`, minimum amount, precision, and whether the market is linear or inverse.

## Broker UI behavior to account for

Coinbase derivatives describes TP/SL bracket orders as reduce-only exits for futures and indicates that when one side of the bracket triggers, the other side is canceled. Bybit describes entire-position versus partial-position TP/SL modes. Bitunix help material similarly distinguishes full-position and batch TP/SL behavior. Sentinel Chain should keep both concepts visible in the UI:

- Simple full-position brackets can often be attached to the entry or submitted as one whole-position TP/SL pair.
- Staged exits need partial close percentages and may require multiple TP/SL orders after the entry is filled and a position ID is known.
- Trailing, breakeven, profit-lock, and time-stop features are often synthetic or venue-specific rather than portable.

## Safety posture implemented in the patch

- Every Bitunix mutation defaults to `dry_run=True`.
- Live mutations require `AUTO_CRYPTO_BITUNIX_LIVE_ENABLED=true` plus the exact confirmation phrase `I_UNDERSTAND_THIS_PLACES_LIVE_FUTURES_ORDERS`.
- The UI sends regular spot/paper brackets to the existing `POST /webhooks/tradingview` intake and futures previews to the new `/futures/*` endpoints.
- The live submit route only submits selected Bitunix POST legs that have concrete request bodies and skips synthetic, placeholder, and post-fill-position-ID legs.
- Operators should use trade-only API keys with withdrawal disabled and run sandbox/paper validation before enabling any live futures path.
