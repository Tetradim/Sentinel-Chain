# Sentinel Chain Guardian Live Wiring

This patch wires the Guardian TP/SL console into the live-capable Sentinel Chain backend while keeping execution locked by default.

## What was added

### Live Sentinel Edge streaming

Routes:

- `GET /guardian/edge/latest?symbol=&mode=`
- `POST /guardian/edge/snapshot`
- `WS /guardian/ws/edge`

Guardian can now publish and receive Sentinel Edge / GEX-style snapshots. Snapshots are persisted through `runtime_state` when a repository is configured, and otherwise fall back to process memory.

The Edge stream accepts snapshots with fields such as `symbol`, `mode`, `current_price`, `support`, `resistance`, `risk_score`, `regime`, `levels`, and `series`.

### Production candle websocket stream

Routes:

- `WS /guardian/ws/candles?symbol=BTCUSDT&interval=1m&transport=bitunix_ws&price_type=market&limit=120`

The stream sends an initial Bitunix REST kline snapshot, then attempts the Bitunix public kline websocket. If the upstream websocket is unavailable or the optional `websockets` package is not installed, Guardian falls back to REST polling with `AUTO_CRYPTO_CANDLE_STREAM_POLL_SECONDS`.

Supporting module:

- `src/sentinel_chain/market_streaming.py`

### Actual live broker execution and real exchange order placement

Routes:

- `GET /guardian/live/status`
- `POST /guardian/live/preview`
- `POST /guardian/live/submit`
- `POST /exchanges/bitunix/futures/order/preview`
- `POST /exchanges/bitunix/futures/order`
- `POST /exchanges/bitunix/futures/orders/cancel`

Supporting module:

- `src/sentinel_chain/live_execution.py`

The live submit route calls the native Bitunix futures REST client method:

- `POST /api/v1/futures/trade/place_order`

The cancel route calls:

- `POST /api/v1/futures/trade/cancel_orders`

### Broad CCXT brokerage wiring

Routes:

- `GET /exchanges/ccxt/catalog`
- `GET /exchanges/{exchange_id}/ccxt/status`
- `GET /exchanges/{exchange_id}/ccxt/ticker?symbol=BTC/USDT`
- `GET /exchanges/{exchange_id}/ccxt/tickers?symbols=BTC/USDT,ETH/USDT`
- `GET /exchanges/{exchange_id}/ccxt/balance`
- `POST /exchanges/{exchange_id}/ccxt/order/preview`
- `POST /exchanges/{exchange_id}/ccxt/order`
- `POST /exchanges/{exchange_id}/ccxt/order/cancel`

This generic layer lets Sentinel Chain expose any exchange installed through CCXT, which CCXT documents as a unified API for 100+ crypto exchanges. Public ticker routes are read-only. Balance, order preview, submit, and cancel routes require the normal operator session/signature checks. Generic live order submit is locked unless credentials, risk approval, runtime controls, global live-readiness, exchange-specific live enablement, a fresh preview ticket, and the exact `PLACE LIVE ORDER` confirmation all pass.

For non-curated CCXT ids, credentials use this convention:

```env
AUTO_CRYPTO_<CCXTID>_API_KEY=<key>
AUTO_CRYPTO_<CCXTID>_API_SECRET=<secret>
AUTO_CRYPTO_<CCXTID>_PASSPHRASE=<optional>
AUTO_CRYPTO_<CCXTID>_LIVE_ENABLED=false
```

`<CCXTID>` is the uppercased CCXT id with non-alphanumeric characters removed.

### Persistent server-side Guardian drawing storage

Routes:

- `GET /guardian/drawings?symbol=BTCUSDT`
- `POST /guardian/drawings`
- `DELETE /guardian/drawings?symbol=BTCUSDT`

Drawings are stored under `runtime_state` keys when the SQLite repository is active. The in-memory fallback is only for no-repository development runs.

Supported drawing types:

- `line`
- `trend`
- `hline`
- `horizontal`
- `zone`
- `risk_reward`
- `note`

## Safety gates for live execution

Live submit is intentionally locked until all gates pass.

A live order requires:

1. Operator session cookie from `/guardian/ui`, or a valid signed operator request.
2. A fresh preview ticket from `/guardian/live/preview`.
3. Risk engine approval.
4. Runtime controls not halted or blocked.
5. Bitunix futures signal only.
6. Native-safe single entry order mapping.
7. Configured Bitunix credentials.
8. Bitunix live flag enabled.
9. Global live readiness satisfied.
10. Exact manual confirmation phrase: `PLACE LIVE ORDER`.
11. Unused preview ticket.
12. Audit event recording when repository is configured.

Global live readiness requires:

```env
AUTO_CRYPTO_REQUIRE_APPROVAL=true
AUTO_CRYPTO_WEBHOOK_SECRET=<32+ chars>
AUTO_CRYPTO_LIVE_TRADING_CONFIRMATION=ENABLE LIVE CRYPTO TRADING
AUTO_CRYPTO_ALLOWED_EXCHANGES=paper,bitunix
AUTO_CRYPTO_BITUNIX_LIVE_ENABLED=true
AUTO_CRYPTO_BITUNIX_API_KEY=<key>
AUTO_CRYPTO_BITUNIX_SECRET_KEY=<secret>
```

Without those values, Guardian still previews the normalized Bitunix payload but refuses to submit live orders.

## What remains intentionally locked or conservative

The live submit path is implemented, but these remain non-native-safe and are rejected for direct live submit until a managed bracket/orchestration worker is added:

- Staged take-profit ladders.
- Partial take-profit exits below 100%.
- Trailing stops.
- Time exits.
- Any exchange other than Bitunix futures.

Those can still be planned, paper submitted, and managed by Sentinel paper/bracket logic, but the direct Bitunix live route blocks them.

## UI changes

Guardian now includes:

- Live execution gate panel in `Venue`.
- Live preview and submit controls in `Desk`.
- Edge stream status pill.
- Candle websocket status pill.
- Server drawing save/load/delete controls in `Lines`.
- Data tab controls for candle stream, Edge stream, Edge sample publish, and stream stop.
- Live order preview JSON pane.
- Persistent drawing status card.

## Files changed or added

```text
src/sentinel_chain/app.py
src/sentinel_chain/live_execution.py
src/sentinel_chain/market_streaming.py
src/sentinel_chain/exchanges/bitunix_adapter.py
src/sentinel_chain/sentinel_guardian_routes.py
src/sentinel_chain/static/sentinel_guardian.html
src/sentinel_chain/static/sentinel_guardian.css
src/sentinel_chain/static/sentinel_guardian.js
.env.example
docs/SENTINEL_CHAIN_GUARDIAN_LIVE_WIRING.md
tests/test_guardian_chart_ui.py
tests/test_guardian_live_wiring.py
tests/test_market_streaming.py
tests/test_bitunix_adapter.py
```

## Validation

The patch was validated with:

```bash
node --check src/sentinel_chain/static/sentinel_guardian.js
python -m compileall -q src/sentinel_chain
pytest -q
```
