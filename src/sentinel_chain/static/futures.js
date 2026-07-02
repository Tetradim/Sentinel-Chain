const $ = (id) => document.getElementById(id);
const payloadOutput = $("payload-output");
const responseOutput = $("response-output");
const summary = $("summary");

function clean(obj) {
  if (Array.isArray(obj)) {
    return obj.map(clean).filter((value) => value !== undefined && value !== null && value !== "");
  }
  if (obj && typeof obj === "object") {
    const out = {};
    for (const [key, value] of Object.entries(obj)) {
      const cleaned = clean(value);
      if (cleaned !== undefined && cleaned !== null && cleaned !== "" && !(Array.isArray(cleaned) && cleaned.length === 0)) {
        out[key] = cleaned;
      }
    }
    return out;
  }
  return obj;
}

function val(id) {
  const el = $(id);
  if (!el) return "";
  if (el.type === "checkbox") return el.checked;
  return String(el.value || "").trim();
}

function addTargetRow(data = {}) {
  const list = $("target-list");
  const row = document.createElement("div");
  row.className = "target-row";
  row.innerHTML = `
    <label>Target price<input class="target-price" inputmode="decimal" value="${data.trigger_price || ""}" /></label>
    <label>Target %<input class="target-pct" inputmode="decimal" value="${data.pct || ""}" /></label>
    <label>Close %<input class="target-close" inputmode="decimal" value="${data.close_pct || "50"}" /></label>
    <button type="button" class="remove-target">Remove</button>
  `;
  row.querySelector(".remove-target").addEventListener("click", () => {
    row.remove();
    renderPayload();
  });
  row.querySelectorAll("input").forEach((input) => input.addEventListener("input", renderPayload));
  list.appendChild(row);
}

function targetsPayload() {
  return [...document.querySelectorAll(".target-row")]
    .map((row) => clean({
      trigger_price: row.querySelector(".target-price").value.trim(),
      pct: row.querySelector(".target-pct").value.trim(),
      close_pct: row.querySelector(".target-close").value.trim() || "100",
    }))
    .filter((target) => target.trigger_price || target.pct);
}

function signalPayload() {
  const targets = targetsPayload();
  const signal = clean({
    signal_id: val("signal_id"),
    symbol: val("symbol"),
    side: val("side"),
    exchange: val("exchange"),
    market_type: val("market_type"),
    quote_amount: val("quote_amount"),
    base_amount: val("base_amount"),
    risk_amount: val("risk_amount"),
    risk_pct: val("risk_pct"),
    price: val("price"),
    stop_loss_pct: val("stop_loss_pct"),
    stop_loss_price: val("stop_loss_price"),
    take_profit_pct: val("take_profit_pct"),
    take_profit_price: val("take_profit_price"),
    take_profit_targets: targets,
    trailing_stop_pct: val("trailing_stop_pct"),
    trailing_stop_amount: val("trailing_stop_amount"),
    trailing_stop_price: val("trailing_stop_price"),
    trailing_stop_close_pct: val("trailing_stop_close_pct"),
    trailing_step_pct: val("trailing_step_pct"),
    trailing_step_amount: val("trailing_step_amount"),
    trailing_activation_pct: val("trailing_activation_pct"),
    trailing_activation_price: val("trailing_activation_price"),
    trail_after_take_profit: val("trail_after_take_profit"),
    breakeven_trigger_pct: val("breakeven_trigger_pct"),
    breakeven_after_take_profit: val("breakeven_after_take_profit"),
    profit_lock_after_take_profit_pct: val("profit_lock_after_take_profit_pct"),
    max_hold_marks: val("max_hold_marks"),
    oca_group: val("oca_group"),
    leverage: val("leverage"),
    max_slippage_bps: val("max_slippage_bps"),
    reduce_only: val("reduce_only"),
    strategy_id: val("strategy_id"),
  });
  return signal;
}

function requestPayload() {
  return clean({
    source: "futures-ui",
    venue: val("exchange"),
    mark_price: val("mark_price"),
    equity: val("equity"),
    position_id: val("position_id"),
    margin_mode: val("margin_mode"),
    margin_coin: val("margin_coin"),
    trigger_price_type: val("trigger_price_type"),
    order_effect: val("order_effect"),
    ccxt_capabilities: {
      attachedStopLossTakeProfit: val("ccxt_attached"),
      trailing: val("ccxt_trailing"),
      reduceOnly: val("ccxt_reduce_only"),
    },
    signal: signalPayload(),
  });
}

function renderPayload() {
  payloadOutput.textContent = JSON.stringify(requestPayload(), null, 2);
  document.querySelectorAll(".futures-only").forEach((node) => {
    node.style.display = val("market_type") === "spot" ? "none" : "grid";
  });
}

function renderSummary(data) {
  summary.innerHTML = "";
  const plan = data.plan || data;
  if (!plan || !plan.legs) return;
  const cards = [
    ["Strategy", plan.strategy, `${plan.venue} · ${plan.symbol} · ${plan.side}`],
    ["Sizing", plan.sizing?.qty ? `${plan.sizing.qty} base` : "Quantity unresolved", `Notional: ${plan.sizing?.notional || "n/a"}; margin: ${plan.sizing?.margin_required || "n/a"}`],
    ["Legs", `${plan.legs.length} planned`, plan.legs.map((leg) => leg.id).join(", ")],
  ];
  if (plan.unsupported_features?.length) cards.push(["Synthetic / unsupported", `${plan.unsupported_features.length} item(s)`, plan.unsupported_features.join(" ")]);
  for (const [title, main, detail] of cards) {
    const card = document.createElement("div");
    card.className = "summary-card";
    card.innerHTML = `<strong>${title}: ${main}</strong><small>${detail || ""}</small>`;
    summary.appendChild(card);
  }
}

async function postJson(path, body) {
  responseOutput.textContent = "Submitting…";
  const res = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(body),
  });
  const text = await res.text();
  let data;
  try { data = JSON.parse(text); } catch { data = {raw: text}; }
  if (!res.ok) {
    data = {error: true, status: res.status, response: data};
  }
  responseOutput.textContent = JSON.stringify(data, null, 2);
  renderSummary(data);
  return data;
}

async function checkHealth() {
  try {
    const res = await fetch("/futures/health");
    const data = await res.json();
    $("health-dot").className = "dot ok";
    $("health-label").textContent = data.ok ? "Futures API online" : "Futures API responded";
    $("health-detail").textContent = data.live_confirmation_phrase || "/futures/health";
  } catch (err) {
    $("health-dot").className = "dot bad";
    $("health-label").textContent = "Futures API unavailable";
    $("health-detail").textContent = String(err);
  }
}

function loadSample() {
  const values = {
    market_type: "swap",
    exchange: "bitunix",
    side: "buy",
    symbol: "BTCUSDT",
    signal_id: `ui-btc-${Date.now()}`,
    strategy_id: "manual-futures-bracket",
    price: "65000",
    mark_price: "65000",
    quote_amount: "100",
    base_amount: "",
    risk_amount: "",
    risk_pct: "",
    equity: "5000",
    max_slippage_bps: "100",
    leverage: "3",
    stop_loss_price: "63500",
    stop_loss_pct: "",
    take_profit_price: "",
    take_profit_pct: "",
    trailing_stop_pct: "1.5",
    trailing_stop_amount: "",
    trailing_stop_price: "",
    trailing_stop_close_pct: "50",
    trailing_activation_price: "66500",
    breakeven_trigger_pct: "1.25",
    profit_lock_after_take_profit_pct: "0.5",
    max_hold_marks: "24",
    oca_group: "btc-breakout",
    position_id: "",
    confirm_live: "",
    leg_ids: "entry",
  };
  for (const [id, value] of Object.entries(values)) if ($(id)) $(id).value = value;
  $("reduce_only").checked = false;
  $("trail_after_take_profit").checked = true;
  $("breakeven_after_take_profit").checked = true;
  $("ccxt_attached").checked = false;
  $("ccxt_trailing").checked = true;
  $("ccxt_reduce_only").checked = true;
  $("target-list").innerHTML = "";
  addTargetRow({trigger_price: "68000", close_pct: "50"});
  addTargetRow({trigger_price: "70000", close_pct: "50"});
  renderPayload();
}

$("add-target").addEventListener("click", () => { addTargetRow(); renderPayload(); });
$("load-sample").addEventListener("click", loadSample);
$("build-plan").addEventListener("click", () => postJson("/futures/plan", requestPayload()));
$("bitunix-dry-run").addEventListener("click", () => postJson("/futures/bitunix/dry-run", requestPayload()));
$("submit-paper").addEventListener("click", () => postJson("/webhooks/tradingview", signalPayload()));
$("submit-live").addEventListener("click", () => {
  const body = requestPayload();
  body.confirm_live = val("confirm_live");
  body.leg_ids = val("leg_ids").split(",").map((item) => item.trim()).filter(Boolean);
  postJson("/futures/bitunix/submit", body);
});
$("copy-payload").addEventListener("click", () => navigator.clipboard.writeText(payloadOutput.textContent));

document.querySelectorAll("input,select").forEach((el) => el.addEventListener("input", renderPayload));
checkHealth();
loadSample();
