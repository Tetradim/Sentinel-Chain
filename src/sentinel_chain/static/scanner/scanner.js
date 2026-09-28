const state = {
  presets: [],
  hits: [],
  selectedHit: null,
  liveTimer: null,
  ws: null,
};

const fields = [
  'price_change_pct','volume_ratio','atr_pct','range_compression','contraction_count','vcp_score',
  'breakout_above_resistance','support_break','rejection_at_resistance','rejection_at_support',
  'ema_stack_bullish','ema_stack_bearish','trend_pullback_long','trend_pullback_short','rsi','macd_hist',
  'macd_bullish','macd_bearish','bb_width_pct','adx','close','open','vwap','support','resistance',
  'support_distance_pct','resistance_distance_pct','spread_pct','bid_ask_imbalance','funding_rate','open_interest_change_pct'
];
const ops = ['>','>=','<','<=','==','!=','between','outside','crosses_above','crosses_below','near','not_near','truthy','falsy'];

function $(id){ return document.getElementById(id); }
function fmt(v, digits=4){
  if(v === null || v === undefined || Number.isNaN(Number(v))) return '—';
  const n = Number(v);
  if(Math.abs(n) >= 1000) return n.toLocaleString(undefined,{maximumFractionDigits:2});
  if(Math.abs(n) >= 1) return n.toLocaleString(undefined,{maximumFractionDigits:digits});
  return n.toPrecision(4);
}
function esc(s){ return String(s ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch])); }
function parseList(raw){ return raw.split(/[\s,]+/).map(x=>x.trim().toUpperCase()).filter(Boolean); }
function selectedTimeframes(){ return [...document.querySelectorAll('#timeframes input:checked')].map(x=>x.value); }
function selectedPresets(){ return [...document.querySelectorAll('.preset-check:checked')].map(x=>x.value); }
function setStatus(text){ $('statusText').textContent = text; }

async function api(path, options={}){
  const res = await fetch(path, {headers:{'Content-Type':'application/json'}, ...options});
  const text = await res.text();
  let data;
  try{ data = text ? JSON.parse(text) : {}; }catch{ data = {raw:text}; }
  if(!res.ok){ throw new Error(data.detail || data.message || `${res.status} ${res.statusText}`); }
  return data;
}

async function loadPresets(){
  try{
    const data = await api('/scanner/presets');
    state.presets = data.presets || [];
    const grid = $('presetGrid');
    grid.innerHTML = state.presets.map((p, idx) => `
      <label class="preset-card">
        <input class="preset-check" type="checkbox" value="${esc(p.id)}" ${idx < 4 ? 'checked' : ''}/>
        <span><strong>${esc(p.name)}</strong><span>${esc(p.description || '')}</span></span>
      </label>
    `).join('');
  }catch(err){
    $('presetGrid').innerHTML = `<div class="muted">Could not load presets: ${esc(err.message)}</div>`;
  }
}

function addConditionRow(row={field:'volume_ratio',op:'>=',value:'1.5',weight:1,required:true}){
  const wrap = document.createElement('div');
  wrap.className = 'condition-row';
  wrap.innerHTML = `
    <select class="cond-field">${fields.map(f=>`<option ${f===row.field?'selected':''}>${f}</option>`).join('')}</select>
    <select class="cond-op">${ops.map(op=>`<option ${op===row.op?'selected':''}>${op}</option>`).join('')}</select>
    <input class="cond-value" value="${esc(row.value ?? '')}" placeholder="value or feature" />
    <input class="cond-weight" type="number" min="0" step="0.25" value="${Number(row.weight ?? 1)}" />
    <label title="Required condition"><input class="cond-required" type="checkbox" ${row.required!==false?'checked':''}/> req</label>
    <button class="ghost cond-remove" title="Remove">×</button>
  `;
  wrap.querySelector('.cond-remove').addEventListener('click', () => wrap.remove());
  $('conditionRows').appendChild(wrap);
}

function buildCustomRule(){
  const name = $('ruleName').value.trim() || 'Custom Scanner Rule';
  const side = $('ruleSide').value;
  const symbols = parseList($('watchlist').value);
  const timeframes = selectedTimeframes();
  const conditions = [...document.querySelectorAll('.condition-row')].map(row => ({
    field: row.querySelector('.cond-field').value,
    op: row.querySelector('.cond-op').value,
    value: coerceValue(row.querySelector('.cond-value').value),
    weight: Number(row.querySelector('.cond-weight').value || 1),
    required: row.querySelector('.cond-required').checked,
  }));
  return { name, side_bias: side, symbols, timeframes, min_score: 70, action: 'create_guardian_plan', conditions };
}

function coerceValue(raw){
  const s = String(raw ?? '').trim();
  if(!s) return null;
  if(s.includes(',') && !fields.includes(s)) return s.split(',').map(x=>coerceValue(x));
  if(s === 'true') return true;
  if(s === 'false') return false;
  const n = Number(s);
  return Number.isFinite(n) ? n : s;
}

async function saveRule(){
  try{
    const rule = buildCustomRule();
    const data = await api('/scanner/rules', {method:'POST', body:JSON.stringify({rule})});
    setStatus(`Saved ${data.rule.name}`);
  }catch(err){ setStatus(`Save failed: ${err.message}`); }
}

function buildRunRequest(){
  const watchlist = parseList($('watchlist').value);
  const timeframes = selectedTimeframes();
  const preset_ids = selectedPresets();
  const req = {
    exchange: $('exchange').value,
    source: $('source').value,
    watchlist,
    timeframes,
    preset_ids,
    synthesize_missing: true,
    persist_hits: true,
    include_features: true,
    max_hits: 200,
    edge_by_symbol: {},
    ticker_by_symbol: {},
    orderbook_by_symbol: {},
    candles_by_symbol: {}
  };
  const candleText = $('candlesJson').value.trim();
  if(candleText && watchlist.length){
    try{
      const candles = JSON.parse(candleText);
      const tf = timeframes[0] || '15m';
      req.candles_by_symbol[watchlist[0]] = {[tf]: candles};
      req.synthesize_missing = true;
    }catch(err){
      setStatus(`Candle JSON ignored: ${err.message}`);
    }
  }
  return req;
}

async function runScan(){
  setStatus('Scanning…');
  $('wsDot').classList.add('live');
  try{
    const data = await api('/scanner/run', {method:'POST', body:JSON.stringify(buildRunRequest())});
    state.hits = data.hits || [];
    renderHits();
    setStatus(`Scan complete · ${data.markets_evaluated} markets`);
    setTimeout(()=>$('wsDot').classList.remove('live'), 650);
    if(data.warnings && data.warnings.length){ console.warn('scanner warnings', data.warnings); }
  }catch(err){
    setStatus(`Scan failed: ${err.message}`);
    $('wsDot').classList.remove('live');
  }
}

async function refreshHits(){
  try{
    const data = await api('/scanner/hits?limit=200');
    state.hits = data.hits || [];
    renderHits();
    setStatus('Hits refreshed');
  }catch(err){ setStatus(`Refresh failed: ${err.message}`); }
}

function renderHits(){
  const filter = $('filterText').value.trim().toLowerCase();
  let hits = state.hits;
  if(filter){ hits = hits.filter(h => `${h.symbol} ${h.rule_name} ${h.side} ${h.trigger}`.toLowerCase().includes(filter)); }
  $('hitCount').textContent = hits.length;
  $('bestScore').textContent = hits.length ? fmt(Math.max(...hits.map(h=>h.score)),1) : '—';
  const tbody = $('resultsTable').querySelector('tbody');
  if(!hits.length){ tbody.innerHTML = '<tr><td colspan="9" class="muted">No scanner hits matched the current filters.</td></tr>'; return; }
  tbody.innerHTML = hits.map(h => `
    <tr data-hit="${esc(h.id)}">
      <td>${esc((h.created_at || '').replace('T',' ').replace('+00:00','Z'))}</td>
      <td><strong>${esc(h.symbol)}</strong></td>
      <td>${esc(h.timeframe)}</td>
      <td class="side-${esc(h.side)}">${esc(h.side.toUpperCase())}</td>
      <td><span class="score">${fmt(h.score,1)}</span></td>
      <td>${esc(h.rule_name)}</td>
      <td>${fmt(h.price,4)}</td>
      <td>${esc(h.trigger)}</td>
      <td><div class="mini-btns"><button class="ghost action-intent" data-hit="${esc(h.id)}">Intent</button><button class="ghost action-ticket" data-hit="${esc(h.id)}">Ticket</button><button class="ghost action-live" data-hit="${esc(h.id)}">Live Preview</button></div></td>
    </tr>
  `).join('');
  tbody.querySelectorAll('tr[data-hit]').forEach(row => row.addEventListener('click', ev => {
    const hit = state.hits.find(x => x.id === row.dataset.hit);
    if(hit){ selectHit(hit); }
  }));
  tbody.querySelectorAll('.action-intent').forEach(btn => btn.addEventListener('click', ev => { ev.stopPropagation(); postPromotion(btn.dataset.hit,'intent'); }));
  tbody.querySelectorAll('.action-ticket').forEach(btn => btn.addEventListener('click', ev => { ev.stopPropagation(); postPromotion(btn.dataset.hit,'ticket'); }));
  tbody.querySelectorAll('.action-live').forEach(btn => btn.addEventListener('click', ev => { ev.stopPropagation(); postPromotion(btn.dataset.hit,'live-preview'); }));
  if(!state.selectedHit && hits[0]) selectHit(hits[0]);
}

function selectHit(hit){
  state.selectedHit = hit;
  $('confidenceBadge').textContent = `${hit.confidence || 'low'} · ${fmt(hit.score,1)}`.toUpperCase();
  $('chartTitle').textContent = `${hit.symbol} ${hit.timeframe} · ${hit.rule_name}`;
  renderDetail(hit);
  drawChart(hit);
}

function renderDetail(hit){
  const t = hit.suggested_ticket || {};
  const reasons = (hit.reasons || []).map(r=>`<li>${esc(r)}</li>`).join('') || '<li>No reasons supplied.</li>';
  const warnings = (hit.warnings || []).map(w=>`<li>${esc(w)}</li>`).join('');
  const tps = (t.take_profits || []).map(tp=>`<li>${esc(tp.label)}: <strong>${fmt(tp.price,6)}</strong> · ${esc(tp.size_pct)}%</li>`).join('');
  $('hitDetail').innerHTML = `
    <div class="hit-card">
      <h3><span class="side-${esc(hit.side)}">${esc(hit.side.toUpperCase())}</span> ${esc(hit.symbol)} · ${esc(hit.timeframe)}</h3>
      <div class="muted">${esc(hit.trigger)}</div>
      <ul class="reason-list">${reasons}</ul>
      ${warnings ? `<h3>Warnings</h3><ul class="reason-list">${warnings}</ul>` : ''}
      <div class="ticket-grid">
        <div><span>Entry</span><strong>${fmt(t.entry,6)}</strong></div>
        <div><span>Stop</span><strong>${fmt(t.stop_loss,6)}</strong></div>
        <div><span>R/R</span><strong>${fmt(t.risk_reward,2)}</strong></div>
        <div><span>Leverage</span><strong>${fmt(t.leverage,1)}x</strong></div>
      </div>
      <h3>Take Profit Ladder</h3>
      <ol class="tp-list">${tps || '<li>No targets available.</li>'}</ol>
      <h3>Invalidation</h3>
      <p class="muted">${esc(t.invalidation || 'No invalidation supplied.')}</p>
      <div class="action-stack">
        <button onclick="postPromotion('${esc(hit.id)}','intent')">Trade Intent</button>
        <button onclick="postPromotion('${esc(hit.id)}','ticket')">Build Bracket</button>
        <button class="secondary" onclick="postPromotion('${esc(hit.id)}','guardian-plan')">Guardian Plan</button>
        <button class="secondary" onclick="postPromotion('${esc(hit.id)}','signal-preview')">Signal Preview</button>
        <button class="danger" onclick="postPromotion('${esc(hit.id)}','live-preview')">Live Preview</button>
      </div>
      <pre class="json-box" id="promotionOutput">Select an action to view the generated payload.</pre>
    </div>`;
  const f = hit.features || {};
  $('supportValue').textContent = fmt(f.support,6);
  $('resistanceValue').textContent = fmt(f.resistance,6);
  $('vwapValue').textContent = fmt(f.vwap,6);
  $('atrValue').textContent = `${fmt(f.atr_pct,2)}%`;
  $('volValue').textContent = `${fmt(f.volume_ratio,2)}x`;
}

async function postPromotion(hitId, mode){
  const route = mode === 'ticket' ? `/scanner/hits/${hitId}/ticket` : `/scanner/hits/${hitId}/${mode}`;
  try{
    const requestMode = mode === 'intent' ? 'ticket' : mode.replace('-','_');
    const body = {mode: requestMode, live_ready:true};
    const data = await api(route, {method:'POST', body:JSON.stringify(body)});
    const box = $('promotionOutput');
    if(box) box.textContent = JSON.stringify(data, null, 2);
    setStatus(`${mode} payload ready`);
  }catch(err){ setStatus(`${mode} failed: ${err.message}`); }
}
window.postPromotion = postPromotion;

function drawChart(hit){
  const canvas = $('chartCanvas');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  ctx.clearRect(0,0,W,H);
  ctx.fillStyle = '#080c12'; ctx.fillRect(0,0,W,H);
  const f = hit.features || {};
  const candles = (f.chart_candles || []).slice(-90);
  if(!candles.length){
    ctx.fillStyle = '#8c98aa'; ctx.fillText('No chart candles in hit payload.', 30, 40); return;
  }
  const topPad = 24, bottomPad = 54, leftPad = 48, rightPad = 90;
  const highs = candles.map(c=>Number(c.h));
  const lows = candles.map(c=>Number(c.l));
  const levels = [f.support,f.resistance,f.vwap].filter(x=>Number.isFinite(Number(x))).map(Number);
  let maxP = Math.max(...highs, ...levels);
  let minP = Math.min(...lows, ...levels);
  const pad = (maxP-minP)*0.12 || maxP*0.01;
  maxP += pad; minP -= pad;
  const x = i => leftPad + i * ((W-leftPad-rightPad)/Math.max(1,candles.length-1));
  const y = p => topPad + (maxP-Number(p))/(maxP-minP) * (H-topPad-bottomPad);
  // grid
  ctx.strokeStyle = '#182233'; ctx.lineWidth = 1;
  ctx.font = '12px Segoe UI'; ctx.fillStyle = '#667388';
  for(let i=0;i<6;i++){
    const yy = topPad + i*(H-topPad-bottomPad)/5;
    ctx.beginPath(); ctx.moveTo(leftPad, yy); ctx.lineTo(W-rightPad, yy); ctx.stroke();
    const price = maxP - i*(maxP-minP)/5;
    ctx.fillText(fmt(price,4), W-rightPad+10, yy+4);
  }
  // supply/demand zones
  drawZone(ctx, y, W, leftPad, rightPad, f.support, '#0f5f45');
  drawZone(ctx, y, W, leftPad, rightPad, f.resistance, '#69303f');
  // candles
  const cw = Math.max(3, (W-leftPad-rightPad)/candles.length*0.58);
  candles.forEach((c,i)=>{
    const open = Number(c.o), close = Number(c.c), high = Number(c.h), low = Number(c.l);
    const up = close >= open;
    ctx.strokeStyle = up ? '#19d18f' : '#ff4c6a';
    ctx.fillStyle = up ? '#19d18f' : '#ff4c6a';
    const xx = x(i);
    ctx.beginPath(); ctx.moveTo(xx, y(high)); ctx.lineTo(xx, y(low)); ctx.stroke();
    const bodyY = Math.min(y(open), y(close));
    const bodyH = Math.max(2, Math.abs(y(open)-y(close)));
    ctx.fillRect(xx-cw/2, bodyY, cw, bodyH);
  });
  // levels
  drawLevel(ctx, y, W, leftPad, rightPad, f.support, '#ffd65a', 'Support');
  drawLevel(ctx, y, W, leftPad, rightPad, f.resistance, '#ffd65a', 'Resistance');
  drawLevel(ctx, y, W, leftPad, rightPad, f.vwap, '#54d6ff', 'VWAP');
  drawLevel(ctx, y, W, leftPad, rightPad, f.volume_profile_poc, '#a77dff', 'POC');
  // entry/stop/tp
  const t = hit.suggested_ticket || {};
  drawLevel(ctx, y, W, leftPad, rightPad, t.entry, hit.side==='short'?'#ff4c6a':'#19d18f', 'Entry');
  drawLevel(ctx, y, W, leftPad, rightPad, t.stop_loss, '#ff8f3c', 'Stop');
  (t.take_profits || []).forEach(tp => drawLevel(ctx, y, W, leftPad, rightPad, tp.price, '#54d6ff', tp.label));
  // marker
  const lastX = x(candles.length-1), lastY = y(candles[candles.length-1].c);
  ctx.fillStyle = hit.side === 'short' ? '#ff4c6a' : '#19d18f';
  ctx.beginPath(); ctx.arc(lastX, lastY, 7, 0, Math.PI*2); ctx.fill();
  ctx.fillStyle = '#e7edf7'; ctx.fillText(hit.side.toUpperCase(), lastX+12, lastY+4);
}

function drawZone(ctx, y, W, leftPad, rightPad, level, color){
  if(!Number.isFinite(Number(level))) return;
  const yy = y(Number(level));
  ctx.fillStyle = color; ctx.globalAlpha = .14;
  ctx.fillRect(leftPad, yy-18, W-leftPad-rightPad, 36);
  ctx.globalAlpha = 1;
}
function drawLevel(ctx, y, W, leftPad, rightPad, level, color, label){
  if(!Number.isFinite(Number(level))) return;
  const yy = y(Number(level));
  ctx.strokeStyle = color; ctx.lineWidth = 1.5; ctx.setLineDash([6,5]);
  ctx.beginPath(); ctx.moveTo(leftPad, yy); ctx.lineTo(W-rightPad, yy); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle = color; ctx.font = '12px Segoe UI'; ctx.fillText(`${label} ${fmt(level,4)}`, W-rightPad+10, yy-4);
}

function startLoop(){
  if(state.liveTimer) return;
  setStatus('Live loop running');
  $('wsDot').classList.add('live');
  runScan();
  state.liveTimer = setInterval(runScan, 10000);
  startWs();
}
function stopLoop(){
  if(state.liveTimer) clearInterval(state.liveTimer);
  state.liveTimer = null;
  if(state.ws) state.ws.close();
  state.ws = null;
  $('wsDot').classList.remove('live');
  setStatus('Stopped');
}
function startWs(){
  try{
    if(state.ws) state.ws.close();
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    state.ws = new WebSocket(`${proto}//${location.host}/scanner/ws/hits?min_score=70&limit=50`);
    state.ws.onmessage = event => {
      try{
        const msg = JSON.parse(event.data);
        if(msg.type === 'scanner_hits' && msg.hits?.length){
          const ids = new Set(state.hits.map(h=>h.id));
          for(const h of msg.hits){ if(!ids.has(h.id)) state.hits.unshift(h); }
          renderHits();
        }
      }catch{}
    };
    state.ws.onopen = () => $('wsDot').classList.add('live');
    state.ws.onclose = () => { if(!state.liveTimer) $('wsDot').classList.remove('live'); };
  }catch(err){ console.warn('WS unavailable', err); }
}

document.addEventListener('DOMContentLoaded', () => {
  loadPresets();
  addConditionRow({field:'breakout_above_resistance',op:'truthy',value:'',weight:2,required:true});
  addConditionRow({field:'volume_ratio',op:'>=',value:'1.25',weight:1,required:false});
  $('runBtn').addEventListener('click', runScan);
  $('liveBtn').addEventListener('click', startLoop);
  $('stopBtn').addEventListener('click', stopLoop);
  $('refreshHitsBtn').addEventListener('click', refreshHits);
  $('filterText').addEventListener('input', renderHits);
  $('addConditionBtn').addEventListener('click', addConditionRow);
  $('saveRuleBtn').addEventListener('click', saveRule);
  drawChart({features:{chart_candles:[]}});
});
