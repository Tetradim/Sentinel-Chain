# Sentinel-Chain UI Prototype Gallery

This folder contains five static UI iterations for selecting the first production interface direction. It is intentionally separate from the FastAPI trading engine while the design is being reviewed.

Run locally:

```powershell
cd ui-prototypes
python -m http.server 8064 --bind 127.0.0.1
```

Open `http://127.0.0.1:8064`.

## Iterations

- Command Center: operator-first signal triage, risk state, exchange health, bot runtime, and audit events.
- Trading Desk: exchange-style order ticket, candlestick chart, order book, and positions table.
- Strategy Marketplace: copy-trading and strategy-discovery flow with guardrails before import.
- Portfolio Sentinel: allocation, equity curve, exposure limits, bracket exits, and daily P&L.
- Signal Forge: Discord/TradingView alert setup, parser preview, integrations, payload inspection, and security gates.

## Research Inputs

The layout choices are based on the local reference screenshots and current product patterns from:

- [OKX trading bot mode](https://www.okx.com/help/introduction-to-trading-bot-mode): portfolio top, order placement, order book, candlestick chart modules.
- [OKX Smart Portfolio](https://www.okx.com/help/viii-smart-portfolio): rebalancing bot setup and portfolio-ratio thinking.
- [Binance Trading Bots support](https://www.binance.com/en/support/faq/list/216-225): strategy catalog grouped by spot, futures, arbitrage, rebalancing, DCA, and algo orders.
- [3Commas custom signal bots](https://help.3commas.io/en/articles/8529406-signal-bot-custom-signal-type): webhook signal intake and long/short filtering.
- [3Commas beginner FAQ](https://help.3commas.io/en/articles/8727335-beginner-faq): multi-exchange bots plus stop-loss/take-profit controls.
- [TradingView webhook alerts](https://www.tradingview.com/support/solutions/43000529348-how-to-configure-webhook-alerts/): alert-to-POST flow.
- [TradingView webhook credential guidance](https://www.tradingview.com/support/solutions/43000722015-using-credentials-for-webhooks/): avoid credentials in webhook URLs or messages.
