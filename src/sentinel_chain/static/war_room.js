(() => {
  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));
  const state = {
    analysis: null,
    candles: [],
    ticket: null,
    activePanel: "automap",
    layers: { sr: true, trend: true, fvg: true, ob: true, fib: true, vp: true, markers: true },
    autoTimer: null,
  };

  const colors = {
    bg: "#071019",
    grid: "rgba(137,159,188,.14)",
    text: "#dce8f8",
    muted: "#7f8ea3",
    green: "#16d991",
    greenSoft: "rgba(22,217,145,.22)",
    red: "#ff4b6a",
    redSoft: "rgba(255,75,106,.22)",
    amber: "#ffd166",
    cyan: "#55d5ff",
    violet: "#9f7aea",
    blue: "#407bff",
  };

  function setStatus(message, tone = "") {
    const line = $("#statusLine");
    line.textContent = message;
    line.className = tone;
  }

  async function api(path, options = {}) {
    const response = await fetch(path, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    const text = await response.text();
    let payload;
    try { payload = text ? JSON.parse(text) : {}; } catch { payload = { raw: text }; }
    if (!response.ok) {
      throw new Error(payload.detail || payload.error || response.statusText);
    }
    return payload;
  }

  const format = {
    price(value) {
      const n = Number(value);
      if (!Number.isFinite(n)) return "-";
      if (Math.abs(n) >= 1000) return n.toLocaleString(undefined, { maximumFractionDigits: 2 });
      if (Math.abs(n) >= 1) return n.toLocaleString(undefined, { maximumFractionDigits: 4 });
      return n.toLocaleString(undefined, { maximumFractionDigits: 8 });
    },
    pct(value) {
      const n = Number(value);
      return Number.isFinite(n) ? `${n.toFixed(2)}%` : "-";
    },
    money(value) {
      const n = Number(value);
      return Number.isFinite(n) ? `$${n.toLocaleString(undefined, { maximumFractionDigits: 2 })}` : "-";
    },
    title(value) {
      return String(value || "").replaceAll("_", " ").replace(/\b\w/g, (m) => m.toUpperCase());
    },
  };

  function currentSymbol() { return $("#symbolInput").value.trim().toUpperCase() || "BTCUSDT"; }
  function currentTimeframe() { return $("#timeframeInput").value || "15m"; }

  function payloadSettings() {
    return {
      posture: $("#postureInput").value,
      volume_bins: 52,
      risk: {
        account_equity: Number($("#equityInput")?.value || 10000),
        risk_pct: Number($("#riskPctInput")?.value || 1),
      },
    };
  }

  async function loadDemo() {
    const symbol = currentSymbol();
    const timeframe = currentTimeframe();
    const bars = Number($("#barsInput").value || 280);
    setStatus(`Loading ${symbol} ${timeframe} demo auto-map...`);
    const payload = await api(`/war-room/demo?symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&bars=${bars}`);
    ingestAnalysis(payload);
    setStatus(`Auto-map ready for ${symbol} ${timeframe}.`, "ok");
  }

  async function analyzeCurrent() {
    if (!state.candles.length) return loadDemo();
    const payload = await api("/war-room/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol: currentSymbol(), timeframe: currentTimeframe(), candles: state.candles, settings: payloadSettings() }),
    });
    ingestAnalysis(payload);
    setStatus(`Re-analyzed ${payload.symbol} with ${payload.bar_count} bars.`, "ok");
  }

  function ingestAnalysis(payload) {
    state.analysis = payload;
    state.candles = payload.candles || [];
    $("#apiState").textContent = payload.ok ? "API connected" : "API warning";
    $("#apiState").classList.toggle("error", !payload.ok);
    renderEverything();
  }

  function resizeCanvas(canvas) {
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(1, Math.floor(rect.width * ratio));
    const height = Math.max(1, Math.floor(rect.height * ratio));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { ctx, width: rect.width, height: rect.height, ratio };
  }

  function chartBounds(candles, analysis, width, height) {
    const pad = { left: 58, right: 118, top: 24, bottom: 32 };
    let min = Math.min(...candles.map((c) => Number(c.low)));
    let max = Math.max(...candles.map((c) => Number(c.high)));
    const levels = analysis?.overlays?.support_resistance || [];
    levels.forEach((l) => {
      const p = Number(l.price);
      if (Number.isFinite(p)) { min = Math.min(min, p); max = Math.max(max, p); }
    });
    const fib = analysis?.overlays?.fibonacci?.levels || [];
    fib.forEach((l) => {
      const p = Number(l.price);
      if (Number.isFinite(p)) { min = Math.min(min, p); max = Math.max(max, p); }
    });
    const spread = Math.max(1e-9, max - min);
    min -= spread * 0.08;
    max += spread * 0.08;
    const innerW = Math.max(1, width - pad.left - pad.right);
    const innerH = Math.max(1, height - pad.top - pad.bottom);
    const x = (index) => pad.left + (index / Math.max(1, candles.length - 1)) * innerW;
    const y = (price) => pad.top + (1 - (price - min) / (max - min)) * innerH;
    return { pad, min, max, innerW, innerH, x, y };
  }

  function drawGrid(ctx, bounds, width, height) {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = colors.bg;
    ctx.fillRect(0, 0, width, height);
    ctx.strokeStyle = colors.grid;
    ctx.lineWidth = 1;
    ctx.fillStyle = colors.muted;
    ctx.font = "11px Inter, sans-serif";
    for (let i = 0; i <= 6; i++) {
      const y = bounds.pad.top + (bounds.innerH / 6) * i;
      ctx.beginPath(); ctx.moveTo(bounds.pad.left, y); ctx.lineTo(width - bounds.pad.right + 72, y); ctx.stroke();
      const price = bounds.max - ((bounds.max - bounds.min) / 6) * i;
      ctx.fillText(format.price(price), width - bounds.pad.right + 78, y + 4);
    }
    for (let i = 0; i <= 8; i++) {
      const x = bounds.pad.left + (bounds.innerW / 8) * i;
      ctx.beginPath(); ctx.moveTo(x, bounds.pad.top); ctx.lineTo(x, height - bounds.pad.bottom); ctx.stroke();
    }
  }

  function drawCandles(ctx, candles, bounds) {
    const candleW = Math.max(2, Math.min(13, bounds.innerW / Math.max(20, candles.length) * 0.72));
    candles.forEach((c, i) => {
      const x = bounds.x(i);
      const openY = bounds.y(Number(c.open));
      const closeY = bounds.y(Number(c.close));
      const highY = bounds.y(Number(c.high));
      const lowY = bounds.y(Number(c.low));
      const up = Number(c.close) >= Number(c.open);
      ctx.strokeStyle = up ? colors.green : colors.red;
      ctx.fillStyle = up ? colors.green : colors.red;
      ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, highY); ctx.lineTo(x, lowY); ctx.stroke();
      const bodyTop = Math.min(openY, closeY);
      const bodyHeight = Math.max(1, Math.abs(closeY - openY));
      ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyHeight);
    });
  }

  function drawMAs(ctx, analysis, bounds) {
    const series = analysis?.indicators?.series || {};
    const lines = [
      ["ema20", colors.amber, "EMA20"],
      ["ema50", colors.violet, "EMA50"],
      ["ema200", colors.cyan, "EMA200"],
      ["vwap", colors.blue, "VWAP"],
    ];
    ctx.lineWidth = 1.4;
    lines.forEach(([key, color, label]) => {
      const values = series[key] || [];
      ctx.strokeStyle = color;
      ctx.beginPath();
      let started = false;
      values.forEach((v, i) => {
        if (v === null || v === undefined) return;
        const x = bounds.x(i), y = bounds.y(Number(v));
        if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
      });
      if (started) ctx.stroke();
    });
  }

  function drawSupportResistance(ctx, analysis, bounds, width) {
    if (!state.layers.sr) return;
    const levels = analysis?.overlays?.support_resistance || [];
    ctx.font = "11px Inter, sans-serif";
    levels.slice(0, 14).forEach((level) => {
      const y = bounds.y(Number(level.price));
      const isSupport = level.kind === "support";
      ctx.strokeStyle = isSupport ? "rgba(22,217,145,.58)" : "rgba(255,75,106,.58)";
      ctx.fillStyle = isSupport ? "rgba(22,217,145,.08)" : "rgba(255,75,106,.08)";
      const yLow = bounds.y(Number(level.zone_low));
      const yHigh = bounds.y(Number(level.zone_high));
      ctx.fillRect(bounds.pad.left, Math.min(yLow, yHigh), bounds.innerW, Math.abs(yHigh - yLow));
      ctx.setLineDash([8, 5]);
      ctx.beginPath(); ctx.moveTo(bounds.pad.left, y); ctx.lineTo(width - bounds.pad.right + 70, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = isSupport ? colors.green : colors.red;
      ctx.fillText(`${isSupport ? "S" : "R"} ${format.price(level.price)} • ${level.touches}x`, bounds.pad.left + 8, y - 5);
    });
  }

  function drawTrendlines(ctx, analysis, bounds) {
    if (!state.layers.trend) return;
    const lines = analysis?.overlays?.trendlines || [];
    ctx.lineWidth = 1.6;
    lines.forEach((line) => {
      const support = line.kind === "support_trend";
      ctx.strokeStyle = support ? "rgba(22,217,145,.72)" : "rgba(255,75,106,.72)";
      ctx.beginPath();
      ctx.moveTo(bounds.x(line.start_index), bounds.y(Number(line.start_price)));
      ctx.lineTo(bounds.x(state.candles.length - 1), bounds.y(Number(line.projected_price)));
      ctx.stroke();
      ctx.fillStyle = support ? colors.green : colors.red;
      ctx.fillText(`${support ? "Demand" : "Supply"} trend`, bounds.x(line.end_index), bounds.y(Number(line.end_price)) - 7);
    });
  }

  function drawZones(ctx, analysis, bounds) {
    const fvg = analysis?.overlays?.imbalances || [];
    const blocks = analysis?.overlays?.order_blocks || [];
    if (state.layers.fvg) {
      fvg.slice(0, 18).forEach((z) => {
        const bull = String(z.kind).includes("bullish");
        ctx.fillStyle = bull ? "rgba(85,213,255,.11)" : "rgba(159,122,234,.11)";
        ctx.strokeStyle = bull ? "rgba(85,213,255,.38)" : "rgba(159,122,234,.38)";
        const x = bounds.x(z.start_index);
        const x2 = bounds.x(Math.min(state.candles.length - 1, z.end_index));
        const y1 = bounds.y(Number(z.zone_high));
        const y2 = bounds.y(Number(z.zone_low));
        ctx.fillRect(x, y1, Math.max(6, x2 - x), y2 - y1);
        ctx.strokeRect(x, y1, Math.max(6, x2 - x), y2 - y1);
      });
    }
    if (state.layers.ob) {
      blocks.slice(0, 12).forEach((z) => {
        const bull = String(z.kind).includes("bullish");
        ctx.fillStyle = bull ? "rgba(22,217,145,.12)" : "rgba(255,75,106,.12)";
        ctx.strokeStyle = bull ? "rgba(22,217,145,.35)" : "rgba(255,75,106,.35)";
        const x = bounds.x(z.start_index);
        const x2 = bounds.x(Math.min(state.candles.length - 1, z.end_index));
        const y1 = bounds.y(Number(z.zone_high));
        const y2 = bounds.y(Number(z.zone_low));
        ctx.fillRect(x, y1, Math.max(10, x2 - x), y2 - y1);
        ctx.strokeRect(x, y1, Math.max(10, x2 - x), y2 - y1);
      });
    }
  }

  function drawFibonacci(ctx, analysis, bounds, width) {
    if (!state.layers.fib) return;
    const levels = analysis?.overlays?.fibonacci?.levels || [];
    ctx.font = "10px Inter, sans-serif";
    levels.forEach((level) => {
      const y = bounds.y(Number(level.price));
      ctx.strokeStyle = "rgba(255,209,102,.24)";
      ctx.setLineDash([3, 4]);
      ctx.beginPath(); ctx.moveTo(bounds.pad.left, y); ctx.lineTo(width - bounds.pad.right + 40, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = colors.amber;
      ctx.fillText(`Fib ${level.label}`, width - bounds.pad.right + 44, y + 3);
    });
  }

  function drawVolumeProfile(ctx, analysis, bounds, width) {
    if (!state.layers.vp) return;
    const bins = analysis?.overlays?.volume_profile?.bins || [];
    const x0 = width - bounds.pad.right + 8;
    const maxW = 80;
    bins.forEach((bin) => {
      const y1 = bounds.y(Number(bin.price_high));
      const y2 = bounds.y(Number(bin.price_low));
      const w = maxW * Number(bin.ratio || 0);
      ctx.fillStyle = Number(bin.mid) < state.candles[state.candles.length - 1].close ? "rgba(22,217,145,.22)" : "rgba(255,75,106,.19)";
      ctx.fillRect(x0, y1, w, Math.max(1, y2 - y1));
    });
    const poc = analysis?.overlays?.volume_profile?.poc;
    if (poc) {
      const y = bounds.y(Number(poc.mid));
      ctx.strokeStyle = colors.cyan;
      ctx.beginPath(); ctx.moveTo(x0 - 4, y); ctx.lineTo(x0 + maxW, y); ctx.stroke();
      ctx.fillStyle = colors.cyan;
      ctx.fillText("POC", x0 + 42, y - 4);
    }
  }

  function drawMarkers(ctx, analysis, bounds) {
    if (!state.layers.markers) return;
    const markers = analysis?.signals?.markers || [];
    markers.forEach((m) => {
      const x = bounds.x(Number(m.index));
      const y = bounds.y(Number(m.price));
      const buy = m.side === "buy";
      ctx.fillStyle = buy ? colors.green : colors.red;
      ctx.strokeStyle = "rgba(0,0,0,.55)";
      ctx.beginPath();
      if (buy) {
        ctx.moveTo(x, y - 11); ctx.lineTo(x - 8, y + 6); ctx.lineTo(x + 8, y + 6);
      } else {
        ctx.moveTo(x, y + 11); ctx.lineTo(x - 8, y - 6); ctx.lineTo(x + 8, y - 6);
      }
      ctx.closePath(); ctx.fill(); ctx.stroke();
      ctx.fillStyle = buy ? colors.green : colors.red;
      ctx.font = "10px Inter, sans-serif";
      ctx.fillText(m.label || (buy ? "BUY" : "SELL"), x + 9, y + (buy ? 12 : -8));
    });
  }

  function drawPivots(ctx, analysis, bounds) {
    const pivots = analysis?.overlays?.pivots || [];
    ctx.fillStyle = "rgba(85,213,255,.75)";
    pivots.slice(-80).forEach((p) => {
      const x = bounds.x(Number(p.index));
      const y = bounds.y(Number(p.price));
      ctx.beginPath(); ctx.arc(x, y, 2.6, 0, Math.PI * 2); ctx.fill();
    });
  }

  function renderMainChart() {
    const canvas = $("#mainCanvas");
    const { ctx, width, height } = resizeCanvas(canvas);
    const candles = state.candles;
    if (!candles.length) {
      ctx.fillStyle = colors.bg; ctx.fillRect(0,0,width,height);
      return;
    }
    const bounds = chartBounds(candles, state.analysis, width, height);
    drawGrid(ctx, bounds, width, height);
    drawZones(ctx, state.analysis, bounds);
    drawFibonacci(ctx, state.analysis, bounds, width);
    drawSupportResistance(ctx, state.analysis, bounds, width);
    drawTrendlines(ctx, state.analysis, bounds);
    drawVolumeProfile(ctx, state.analysis, bounds, width);
    drawMAs(ctx, state.analysis, bounds);
    drawCandles(ctx, candles, bounds);
    drawPivots(ctx, state.analysis, bounds);
    drawMarkers(ctx, state.analysis, bounds);
    drawLastPrice(ctx, bounds, width);
    canvas._bounds = bounds;
  }

  function drawLastPrice(ctx, bounds, width) {
    const last = state.candles[state.candles.length - 1];
    if (!last) return;
    const y = bounds.y(Number(last.close));
    ctx.strokeStyle = colors.cyan;
    ctx.setLineDash([2, 4]);
    ctx.beginPath(); ctx.moveTo(bounds.pad.left, y); ctx.lineTo(width - bounds.pad.right + 72, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = colors.cyan;
    ctx.fillRect(width - bounds.pad.right + 12, y - 12, 86, 24);
    ctx.fillStyle = "#031018";
    ctx.font = "bold 12px Inter, sans-serif";
    ctx.fillText(format.price(last.close), width - bounds.pad.right + 17, y + 4);
  }

  function drawLineSeries(ctx, values, bounds, yMin, yMax, color, width = 1.4) {
    ctx.strokeStyle = color;
    ctx.lineWidth = width;
    ctx.beginPath();
    let started = false;
    values.forEach((v, i) => {
      if (v === null || v === undefined) return;
      const x = bounds.left + (i / Math.max(1, values.length - 1)) * bounds.w;
      const y = bounds.top + (1 - (Number(v) - yMin) / Math.max(1e-9, yMax - yMin)) * bounds.h;
      if (!started) { ctx.moveTo(x, y); started = true; } else { ctx.lineTo(x, y); }
    });
    if (started) ctx.stroke();
  }

  function renderRsiChart() {
    const canvas = $("#rsiCanvas");
    const { ctx, width, height } = resizeCanvas(canvas);
    ctx.fillStyle = "rgba(3,7,11,.55)"; ctx.fillRect(0, 0, width, height);
    const series = state.analysis?.indicators?.series || {};
    const rsi = series.rsi14 || [];
    const stoch = series.stoch_k || [];
    const bounds = { left: 42, top: 18, w: width - 62, h: height - 34 };
    ctx.strokeStyle = colors.grid; ctx.lineWidth = 1;
    [30, 50, 70].forEach((level) => {
      const y = bounds.top + (1 - level / 100) * bounds.h;
      ctx.beginPath(); ctx.moveTo(bounds.left, y); ctx.lineTo(bounds.left + bounds.w, y); ctx.stroke();
      ctx.fillStyle = colors.muted; ctx.font = "10px Inter"; ctx.fillText(level, 8, y + 3);
    });
    drawLineSeries(ctx, rsi, bounds, 0, 100, colors.amber, 1.7);
    drawLineSeries(ctx, stoch, bounds, 0, 100, colors.cyan, 1.1);
  }

  function renderMacdChart() {
    const canvas = $("#macdCanvas");
    const { ctx, width, height } = resizeCanvas(canvas);
    ctx.fillStyle = "rgba(3,7,11,.55)"; ctx.fillRect(0, 0, width, height);
    const series = state.analysis?.indicators?.series || {};
    const hist = (series.macd_histogram || []).map((v) => v ?? 0);
    const macd = series.macd || [];
    const sig = series.macd_signal || [];
    const absMax = Math.max(1e-9, ...hist.map((v) => Math.abs(Number(v))), ...macd.filter(Number.isFinite).map((v) => Math.abs(Number(v))));
    const bounds = { left: 38, top: 16, w: width - 58, h: height - 32 };
    const zeroY = bounds.top + bounds.h / 2;
    ctx.strokeStyle = colors.grid; ctx.beginPath(); ctx.moveTo(bounds.left, zeroY); ctx.lineTo(bounds.left + bounds.w, zeroY); ctx.stroke();
    const barW = Math.max(1, bounds.w / Math.max(1, hist.length) * .7);
    hist.forEach((v, i) => {
      const x = bounds.left + (i / Math.max(1, hist.length - 1)) * bounds.w;
      const y = bounds.top + (1 - ((Number(v) + absMax) / (absMax * 2))) * bounds.h;
      ctx.fillStyle = Number(v) >= 0 ? colors.greenSoft : colors.redSoft;
      ctx.fillRect(x - barW / 2, Math.min(zeroY, y), barW, Math.max(1, Math.abs(zeroY - y)));
    });
    drawLineSeries(ctx, macd, bounds, -absMax, absMax, colors.cyan, 1.4);
    drawLineSeries(ctx, sig, bounds, -absMax, absMax, colors.amber, 1.2);
  }

  function renderTickerStrip() {
    const last = state.candles[state.candles.length - 1];
    const prev = state.candles[Math.max(0, state.candles.length - 24)];
    const mainChange = last && prev ? ((last.close - prev.close) / prev.close) * 100 : 0;
    const symbols = [
      [currentSymbol(), last?.close || 0, mainChange],
      ["ETHUSDT", 3285.4, 1.32], ["SOLUSDT", 147.2, -0.63], ["BTC.D", 54.1, 0.18], ["TOTAL3", 825.8, 2.4],
    ];
    $("#tickerStrip").innerHTML = symbols.map(([sym, price, ch]) => `<div class="ticker ${ch >= 0 ? "up" : "down"}"><b>${sym}</b><span>${format.price(price)} • ${ch >= 0 ? "+" : ""}${Number(ch).toFixed(2)}%</span></div>`).join("");
  }

  function renderScore() {
    const signals = state.analysis?.signals || {};
    const rec = String(signals.recommendation || "wait_for_trigger");
    const confidence = Number(signals.confidence || 0);
    const title = rec === "long_bias" ? "LONG" : rec === "short_bias" ? "SHORT" : "WAIT";
    $("#recommendation").textContent = title;
    $("#recommendationSub").textContent = format.title(rec);
    $("#confidenceValue").textContent = confidence.toFixed(0);
    $(".score-ring").style.setProperty("--score", `${confidence}%`);
    $("#longMeter").value = Number(signals.long_score || 0);
    $("#shortMeter").value = Number(signals.short_score || 0);
    $("#longScore").textContent = Number(signals.long_score || 0).toFixed(0);
    $("#shortScore").textContent = Number(signals.short_score || 0).toFixed(0);
    $("#whyHeadline").textContent = signals.why?.headline || "Waiting for evidence.";
  }

  function renderMetrics() {
    const latest = state.analysis?.indicators?.latest || {};
    const risk = state.analysis?.risk || {};
    const cards = [
      ["Close", format.price(latest.close)], ["ATR", `${format.price(latest.atr14)} (${format.pct(latest.atr_pct)})`],
      ["RSI", Number(latest.rsi14 || 0).toFixed(1)], ["MACD Hist", format.price(latest.macd_histogram)],
      ["ADX", Number(latest.adx14 || 0).toFixed(1)], ["VWAP", format.price(latest.vwap)],
      ["EMA20/50", `${format.price(latest.ema20)} / ${format.price(latest.ema50)}`], ["Max Lev", `${risk.recommended_max_leverage || "-"}x`],
    ];
    $("#metricGrid").innerHTML = cards.map(([label, value]) => `<div class="metric-card"><span>${label}</span><b>${value}</b></div>`).join("");
  }

  function renderReasons() {
    const reasons = state.analysis?.signals?.reasons || [];
    $("#reasonList").innerHTML = reasons.length ? reasons.map((r) => `<div class="reason-card ${r.direction}"><b>${r.direction.toUpperCase()} • ${r.title}</b><p>${r.detail}</p></div>`).join("") : `<div class="reason-card neutral"><b>No evidence yet</b><p>Run an auto-map to populate signal reasons.</p></div>`;
  }

  function renderPatterns() {
    const candles = state.analysis?.patterns?.candles || [];
    const chart = state.analysis?.patterns?.chart || [];
    const divs = state.analysis?.patterns?.divergences || [];
    const items = [...chart, ...divs, ...candles.slice(-16)];
    $("#patternList").innerHTML = items.length ? items.map((p) => `<span class="tag ${p.direction || "neutral"}">${format.title(p.kind)}${p.status ? ` • ${p.status}` : ""}</span>`).join("") : `<span class="tag">No major patterns</span>`;
  }

  function renderFeatures() {
    const flags = state.analysis?.feature_flags || {};
    $("#featureList").innerHTML = Object.entries(flags).filter(([, v]) => v).map(([k]) => `<div>✓ ${format.title(k)}</div>`).join("");
  }

  function renderLevels() {
    const s = state.analysis?.signals?.nearest_support;
    const r = state.analysis?.signals?.nearest_resistance;
    const levels = [s, r].filter(Boolean);
    $("#nearestLevels").innerHTML = levels.map((l) => `<div class="level-item"><div><b>${format.title(l.kind)} ${format.price(l.price)}</b><br><span>${l.polarity} • ${l.touches} touches • ${format.pct(l.distance_pct)}</span></div><small>${Number(l.strength || 0).toFixed(1)}</small></div>`).join("") || `<div class="level-item"><b>No levels yet</b><span>Load candles to map support and resistance.</span></div>`;
  }

  function renderDomLadder() {
    const last = state.candles[state.candles.length - 1];
    if (!last) return;
    const price = Number(last.close);
    const atr = Number(state.analysis?.indicators?.latest?.atr14 || price * .01);
    const step = atr / 8 || price * .001;
    const levels = state.analysis?.overlays?.support_resistance || [];
    const rows = [];
    for (let i = 12; i >= -12; i--) {
      const p = price + i * step;
      const nearby = levels.find((l) => Math.abs(Number(l.price) - p) < step * .55);
      const base = nearby ? Math.min(100, 22 + Number(nearby.strength || 0) * 8) : Math.max(5, 72 - Math.abs(i) * 5 + (Math.sin(i * 2.1) * 10));
      const bid = i <= 0 ? base : base * .38;
      const ask = i >= 0 ? base : base * .38;
      rows.push(`<div class="dom-row ${i === 0 ? "mark" : ""}"><div class="dom-bid" style="--w:${bid}%"></div><div class="dom-price">${format.price(p)}</div><div class="dom-ask" style="--w:${ask}%"></div></div>`);
    }
    $("#domLadder").innerHTML = rows.join("");
    $("#domSpread").textContent = `step ${format.price(step)}`;
  }

  function renderWhyBlocks() {
    const why = state.analysis?.signals?.why || {};
    const groups = [
      ["Why", [why.headline, ...(why.why_good_or_bad || [])]],
      ["When to trade", why.when_to_trade || []],
      ["How to trade", why.how_to_trade || []],
      ["Risk warnings", state.analysis?.risk?.warnings || []],
    ];
    $("#whyBlocks").innerHTML = groups.map(([title, lines]) => `<div class="why-card"><b>${title}</b><p>${(lines || []).filter(Boolean).map((x) => `• ${x}`).join("<br>") || "No notes yet."}</p></div>`).join("");
    const playbooks = state.analysis?.playbooks || [];
    $("#playbookList").innerHTML = playbooks.map((p) => `<div class="playbook-card"><b>${p.name}</b><p><strong>Best for:</strong> ${p.best_for}<br><strong>Rules:</strong> ${(p.entry_rules || []).join("; ")}<br><strong>Risk:</strong> ${p.risk}</p></div>`).join("");
  }

  function renderPlanSummary(plan) {
    if (!plan) { $("#planSummary").innerHTML = ""; return; }
    const rows = [
      ["Bias", plan.bias], ["Entry", `${format.price(plan.entry_zone_low)} - ${format.price(plan.entry_zone_high)}`],
      ["Stop", format.price(plan.stop_loss)], ["Risk", `${format.money(plan.risk_amount)} / ${format.price(plan.risk_per_unit)} per unit`],
      ["Qty", plan.suggested_quantity], ["Notional", format.money(plan.suggested_quote_notional)],
      ["Blended R/R", plan.rr_blended], ["Management", (plan.management || []).join(" | ")],
    ];
    $("#planSummary").innerHTML = rows.map(([label, value]) => `<div class="plan-row"><span>${label}</span><b>${value}</b></div>`).join("");
  }

  async function buildTicket() {
    if (!state.candles.length) await loadDemo();
    const sideRaw = $("#sideInput").value;
    const payload = {
      symbol: currentSymbol(), timeframe: currentTimeframe(), venue: $("#venueInput").value,
      market_type: $("#marketTypeInput").value, side: sideRaw === "auto" ? null : sideRaw,
      account_equity: Number($("#equityInput").value || 10000), risk_pct: Number($("#riskPctInput").value || 1),
      leverage: Number($("#leverageInput").value || 1), candles: state.candles, settings: payloadSettings(),
    };
    const result = await api("/war-room/ticket", { method: "POST", body: JSON.stringify(payload) });
    state.ticket = result.signal;
    $("#ticketJson").textContent = JSON.stringify(result.signal, null, 2);
    renderPlanSummary(result.plan);
    setStatus("Built paper-first bracket/futures ticket from current map.", "ok");
  }

  async function submitPaperSignal() {
    if (!state.ticket) await buildTicket();
    const ok = confirm("Submit this payload to Sentinel Chain paper signal intake? Live execution stays subject to existing bot gates.");
    if (!ok) return;
    const result = await api("/webhooks/tradingview", { method: "POST", body: JSON.stringify(state.ticket) });
    setStatus(`Paper signal submitted: ${result.status || result.message || "accepted"}.`, "ok");
  }

  function parsePastedData(text) {
    const trimmed = text.trim();
    if (!trimmed) return [];
    if (trimmed.startsWith("[") || trimmed.startsWith("{")) {
      const parsed = JSON.parse(trimmed);
      return Array.isArray(parsed) ? parsed : (parsed.candles || []);
    }
    const lines = trimmed.split(/\r?\n/).filter(Boolean);
    const header = lines[0].split(",").map((x) => x.trim().toLowerCase());
    return lines.slice(1).map((line, idx) => {
      const cells = line.split(",").map((x) => x.trim());
      const row = {};
      header.forEach((name, i) => row[name] = cells[i]);
      return {
        time: row.time ?? row.timestamp ?? idx,
        open: Number(row.open), high: Number(row.high), low: Number(row.low), close: Number(row.close), volume: Number(row.volume || 0),
      };
    });
  }

  async function loadPastedData() {
    const candles = parsePastedData($("#dataInput").value);
    if (candles.length < 30) throw new Error("Need at least 30 candles.");
    const payload = await api("/war-room/analyze", {
      method: "POST",
      body: JSON.stringify({ symbol: currentSymbol(), timeframe: currentTimeframe(), candles, settings: payloadSettings() }),
    });
    ingestAnalysis(payload);
    setStatus(`Analyzed ${candles.length} pasted candles.`, "ok");
  }

  async function runBacktest() {
    if (!state.candles.length) await loadDemo();
    const payload = await api("/war-room/backtest", {
      method: "POST",
      body: JSON.stringify({
        symbol: currentSymbol(), timeframe: currentTimeframe(), candles: state.candles,
        settings: { fast_ema: Number($("#fastEmaInput").value || 20), slow_ema: Number($("#slowEmaInput").value || 50), risk_pct: Number($("#btRiskInput").value || 1), max_bars: Number($("#maxBarsInput").value || 48), allow_short: true },
      }),
    });
    renderBacktest(payload);
    setStatus("Backtest complete.", "ok");
  }

  function renderBacktest(result) {
    const metrics = result.metrics || {};
    const cards = Object.entries({ Return: format.pct(metrics.return_pct), Trades: metrics.total_trades, "Win rate": format.pct(metrics.win_rate_pct), "Profit factor": metrics.profit_factor, Drawdown: format.pct(metrics.max_drawdown_pct), "End equity": format.money(metrics.ending_equity) });
    $("#backtestMetrics").innerHTML = cards.map(([k, v]) => `<div class="metric-card"><span>${k}</span><b>${v}</b></div>`).join("");
    drawEquity(result.equity_curve || []);
    $("#tradeList").innerHTML = (result.trades || []).slice(-20).reverse().map((t) => `<div class="trade-card"><span>${t.side.toUpperCase()} ${t.entry_index} → ${t.exit_index} • ${t.reason}</span><b class="${t.pnl >= 0 ? "gain" : "loss"}">${format.money(t.pnl)}</b></div>`).join("") || `<div class="trade-card"><span>No trades</span><b>-</b></div>`;
  }

  function drawEquity(curve) {
    const canvas = $("#equityCanvas");
    const { ctx, width, height } = resizeCanvas(canvas);
    ctx.fillStyle = "rgba(3,7,11,.55)"; ctx.fillRect(0,0,width,height);
    if (!curve.length) return;
    const min = Math.min(...curve.map((p) => Number(p.equity)));
    const max = Math.max(...curve.map((p) => Number(p.equity)));
    const pad = 20;
    ctx.strokeStyle = colors.green; ctx.lineWidth = 1.6; ctx.beginPath();
    curve.forEach((p, i) => {
      const x = pad + (i / Math.max(1, curve.length - 1)) * (width - pad * 2);
      const y = pad + (1 - (Number(p.equity) - min) / Math.max(1e-9, max - min)) * (height - pad * 2);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  function renderEverything() {
    if (!state.analysis) return;
    $("#chartTitle").textContent = `${state.analysis.symbol} ${state.analysis.timeframe} Auto Map`;
    $("#chartSubtitle").textContent = `${state.analysis.bar_count} candles • ${format.title(state.analysis.patterns?.structure?.state)} • ${format.title(state.analysis.signals?.recommendation)}`;
    renderTickerStrip();
    renderMainChart();
    renderRsiChart();
    renderMacdChart();
    renderScore();
    renderMetrics();
    renderReasons();
    renderPatterns();
    renderFeatures();
    renderLevels();
    renderDomLadder();
    renderWhyBlocks();
    renderPlanSummary(state.analysis.signals?.trade_plans?.primary);
  }

  function showPanel(name) {
    state.activePanel = name;
    $$(".rail-btn").forEach((btn) => btn.classList.toggle("active", btn.dataset.panel === name));
    $$(".side-drawer").forEach((panel) => panel.classList.remove("active"));
    const panel = $(`#${name}Panel`);
    if (panel) panel.classList.add("active");
  }

  function toggleAuto() {
    const btn = $("#autoBtn");
    if (state.autoTimer) {
      clearInterval(state.autoTimer); state.autoTimer = null;
      btn.textContent = "Auto off"; btn.setAttribute("aria-pressed", "false");
      setStatus("Auto refresh disabled.");
      return;
    }
    state.autoTimer = setInterval(() => analyzeCurrent().catch((err) => setStatus(err.message, "error")), 10000);
    btn.textContent = "Auto 10s"; btn.setAttribute("aria-pressed", "true");
    setStatus("Auto refresh enabled every 10 seconds.", "ok");
  }

  function wireEvents() {
    $("#loadDemoBtn").addEventListener("click", () => loadDemo().catch((e) => setStatus(e.message, "error")));
    $("#analyzeBtn").addEventListener("click", () => analyzeCurrent().catch((e) => setStatus(e.message, "error")));
    $("#autoBtn").addEventListener("click", toggleAuto);
    $("#buildTicketBtn").addEventListener("click", () => buildTicket().catch((e) => setStatus(e.message, "error")));
    $("#submitPaperBtn").addEventListener("click", () => submitPaperSignal().catch((e) => setStatus(e.message, "error")));
    $("#copyTicketBtn").addEventListener("click", async () => { await navigator.clipboard.writeText($("#ticketJson").textContent); setStatus("Ticket JSON copied.", "ok"); });
    $("#loadDataBtn").addEventListener("click", () => loadPastedData().catch((e) => setStatus(e.message, "error")));
    $("#sampleDataBtn").addEventListener("click", () => { $("#dataInput").value = JSON.stringify(state.candles, null, 2); setStatus("Current candles copied into loader.", "ok"); });
    $("#runBacktestBtn").addEventListener("click", () => runBacktest().catch((e) => setStatus(e.message, "error")));
    $$(".rail-btn").forEach((btn) => btn.addEventListener("click", () => showPanel(btn.dataset.panel)));
    $$(".drawer-close").forEach((btn) => btn.addEventListener("click", () => $$(".side-drawer").forEach((p) => p.classList.remove("active"))));
    $$(".layer-toggle").forEach((box) => box.addEventListener("change", () => { state.layers[box.dataset.layer] = box.checked; renderMainChart(); }));
    window.addEventListener("resize", () => renderEverything());
    $("#mainCanvas").addEventListener("mousemove", (event) => {
      const canvas = event.currentTarget;
      const bounds = canvas._bounds;
      if (!bounds || !state.candles.length) return;
      const rect = canvas.getBoundingClientRect();
      const mx = event.clientX - rect.left;
      const idx = Math.max(0, Math.min(state.candles.length - 1, Math.round(((mx - bounds.pad.left) / bounds.innerW) * (state.candles.length - 1))));
      const c = state.candles[idx];
      $("#crosshairReadout").textContent = `${c.time} • O ${format.price(c.open)} H ${format.price(c.high)} L ${format.price(c.low)} C ${format.price(c.close)} V ${format.price(c.volume)}`;
    });
  }

  wireEvents();
  loadDemo().catch((error) => {
    $("#apiState").textContent = "API offline";
    $("#apiState").classList.add("error");
    setStatus(`Unable to load War Room demo: ${error.message}`, "error");
  });
})();
