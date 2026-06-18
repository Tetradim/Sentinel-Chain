const screens = Array.from(document.querySelectorAll(".screen"));
const navItems = Array.from(document.querySelectorAll(".nav-item"));

function activateScreen(screenName) {
  const next = screens.some((screen) => screen.dataset.screen === screenName) ? screenName : "command";

  screens.forEach((screen) => {
    screen.classList.toggle("is-active", screen.dataset.screen === next);
  });

  navItems.forEach((item) => {
    item.classList.toggle("is-active", item.dataset.screen === next);
  });

  if (location.hash.slice(1) !== next) {
    history.replaceState(null, "", `#${next}`);
  }

  drawCharts();
}

navItems.forEach((item) => {
  item.addEventListener("click", () => activateScreen(item.dataset.screen));
});

window.addEventListener("hashchange", () => activateScreen(location.hash.slice(1)));
window.addEventListener("resize", drawCharts);

function setupCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(1, Math.floor(rect.width || canvas.width));
  const height = Math.max(1, Math.floor((rect.width ? rect.width * (canvas.height / canvas.width) : canvas.height)));
  canvas.width = Math.floor(width * ratio);
  canvas.height = Math.floor(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { ctx, width, height };
}

function linePath(ctx, points, width, height, color, fill) {
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min || 1;
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = (index / (points.length - 1)) * width;
    const y = height - ((point - min) / range) * (height * 0.72) - height * 0.14;
    if (index === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  });
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.stroke();
  if (fill) {
    ctx.lineTo(width, height);
    ctx.lineTo(0, height);
    ctx.closePath();
    ctx.fillStyle = fill;
    ctx.fill();
  }
}

function drawGrid(ctx, width, height) {
  ctx.strokeStyle = "rgba(154, 168, 187, 0.12)";
  ctx.lineWidth = 1;
  for (let x = 0; x <= width; x += width / 8) {
    ctx.beginPath();
    ctx.moveTo(x, 0);
    ctx.lineTo(x, height);
    ctx.stroke();
  }
  for (let y = 0; y <= height; y += height / 5) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
}

function drawCandles(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  drawGrid(ctx, width, height);

  const values = [61, 64, 63, 67, 65, 69, 72, 70, 68, 73, 76, 74, 77, 79, 75, 72, 69, 71, 68, 66, 70, 73, 75, 74, 76, 78, 77, 80, 83, 81, 79, 82, 85, 84, 86, 83, 81, 84, 87, 89];
  const max = Math.max(...values) + 4;
  const min = Math.min(...values) - 4;
  const candleWidth = Math.max(5, width / values.length - 6);

  values.forEach((value, index) => {
    const previous = values[Math.max(0, index - 1)];
    const open = previous + ((index % 4) - 1.5);
    const close = value;
    const high = Math.max(open, close) + 2 + (index % 3);
    const low = Math.min(open, close) - 2 - (index % 2);
    const x = (index / values.length) * width + 8;
    const yHigh = height - ((high - min) / (max - min)) * (height - 44) - 20;
    const yLow = height - ((low - min) / (max - min)) * (height - 44) - 20;
    const yOpen = height - ((open - min) / (max - min)) * (height - 44) - 20;
    const yClose = height - ((close - min) / (max - min)) * (height - 44) - 20;
    const bullish = close >= open;
    ctx.strokeStyle = bullish ? "#28d8a1" : "#ff5470";
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.moveTo(x + candleWidth / 2, yHigh);
    ctx.lineTo(x + candleWidth / 2, yLow);
    ctx.stroke();
    ctx.fillRect(x, Math.min(yOpen, yClose), candleWidth, Math.max(3, Math.abs(yOpen - yClose)));
  });

  const ma = values.map((_, i) => {
    const slice = values.slice(Math.max(0, i - 5), i + 1);
    return slice.reduce((sum, item) => sum + item, 0) / slice.length;
  });
  linePath(ctx, ma, width, height, "#ffbe3d");
}

function drawRing(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.36;
  ctx.clearRect(0, 0, width, height);
  ctx.lineWidth = 18;
  ctx.strokeStyle = "rgba(154, 168, 187, 0.16)";
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
  ctx.stroke();
  ctx.strokeStyle = "#28d8a1";
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, -Math.PI / 2, Math.PI * 0.24);
  ctx.stroke();
  ctx.strokeStyle = "#ffbe3d";
  ctx.beginPath();
  ctx.arc(centerX, centerY, radius, Math.PI * 0.31, Math.PI * 0.54);
  ctx.stroke();
}

function drawDonut(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.34;
  const parts = [
    ["#ffbe3d", 0.36],
    ["#27d9ef", 0.24],
    ["#28d8a1", 0.18],
    ["#a678ff", 0.14],
    ["#ff5470", 0.08],
  ];
  let start = -Math.PI / 2;
  ctx.clearRect(0, 0, width, height);
  parts.forEach(([color, size]) => {
    ctx.strokeStyle = color;
    ctx.lineWidth = 24;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, start, start + Math.PI * 2 * size - 0.04);
    ctx.stroke();
    start += Math.PI * 2 * size;
  });
  ctx.fillStyle = "#eef4ff";
  ctx.font = "700 28px Cascadia Mono, Consolas, monospace";
  ctx.textAlign = "center";
  ctx.fillText("$12.45k", centerX, centerY - 2);
  ctx.fillStyle = "#9aa8bb";
  ctx.font = "14px Bahnschrift, Aptos, Segoe UI, sans-serif";
  ctx.fillText("paper NAV", centerX, centerY + 24);
}

function drawBars(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  const values = [12, -9, 16, 22, -4, 30, 11, 44, -14, 18, 29, 35, -7, 42];
  ctx.clearRect(0, 0, width, height);
  const zeroY = height * 0.58;
  ctx.strokeStyle = "rgba(154, 168, 187, 0.16)";
  ctx.beginPath();
  ctx.moveTo(0, zeroY);
  ctx.lineTo(width, zeroY);
  ctx.stroke();
  const barWidth = width / values.length - 7;
  values.forEach((value, index) => {
    const x = index * (barWidth + 7);
    const barHeight = Math.abs(value) / 44 * (height * 0.48);
    ctx.fillStyle = value >= 0 ? "#28d8a1" : "#ff5470";
    ctx.fillRect(x, value >= 0 ? zeroY - barHeight : zeroY, barWidth, barHeight);
  });
}

function drawSpark(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  const offset = Number(canvas.dataset.seed || canvas.parentElement.querySelector("strong").textContent.length);
  const points = Array.from({ length: 24 }, (_, index) => 42 + Math.sin((index + offset) * 0.7) * 12 + index * 1.7 + (index % 5) * 2);
  ctx.clearRect(0, 0, width, height);
  linePath(ctx, points, width, height, "#27d9ef", "rgba(39, 217, 239, 0.12)");
}

function drawEquity(canvas) {
  const { ctx, width, height } = setupCanvas(canvas);
  const points = [88, 93, 91, 96, 99, 102, 98, 104, 108, 117, 114, 119, 124, 121, 128, 134, 130, 136, 139, 143, 141, 147, 151, 148, 156, 160];
  ctx.clearRect(0, 0, width, height);
  drawGrid(ctx, width, height);
  linePath(ctx, points, width, height, "#28d8a1", "rgba(40, 216, 161, 0.14)");
  linePath(ctx, points.map((point, index) => point - 7 - Math.sin(index) * 6), width, height, "#ff5470");
}

function drawCharts() {
  document.querySelectorAll(".screen.is-active canvas").forEach((canvas) => {
    const type = canvas.dataset.chart;
    if (type === "candles") drawCandles(canvas);
    if (type === "ring") drawRing(canvas);
    if (type === "donut") drawDonut(canvas);
    if (type === "bars") drawBars(canvas);
    if (type === "spark") drawSpark(canvas);
    if (type === "equity") drawEquity(canvas);
  });
}

activateScreen(location.hash.slice(1) || "command");
