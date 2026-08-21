const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
const pct = value => `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
async function loadJson(path) { const response = await fetch(path, { cache: "no-store" }); if (!response.ok) throw new Error(`${path}: ${response.status}`); return response.json(); }
function setText(id, value) { document.getElementById(id).textContent = value; }
function renderStatus(status) {
  const signal = status.signal, band = document.getElementById("signal-band");
  band.classList.toggle("cash", signal.signal === "CASH"); setText("signal", signal.signal);
  setText("signal-copy", signal.watch_band ? "均线距离进入观察区，等待确认交叉" : "仅在 SMA35 与 SMA300 交叉时切换");
  setText("price", euro.format(signal.last_price)); setText("short-sma", euro.format(signal.short_sma)); setText("long-sma", euro.format(signal.long_sma)); setText("gap", pct(signal.gap_pct));
  setText("cross-count", signal.crossover_count_12m); setText("rapid-count", signal.rapid_reversal_count_12m);
  setText("data-health", status.data_health.status.toUpperCase()); setText("divergence", pct(status.data_health.divergence_pct));
  setText("freshness", `Signal ${signal.as_of} UTC · Updated ${new Date(status.generated_at).toLocaleString()}`);
}
function renderChart(rows) {
  const canvas = document.getElementById("trend-chart"), context = canvas.getContext("2d"), ratio = window.devicePixelRatio || 1, bounds = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.floor(bounds.width * ratio)); canvas.height = Math.max(1, Math.floor(bounds.height * ratio)); context.scale(ratio, ratio);
  const width = bounds.width, height = bounds.height, pad = { left: 58, right: 14, top: 14, bottom: 30 };
  const values = rows.flatMap(row => [row.price, row.short_sma, row.long_sma]), min = Math.min(...values) * 0.96, max = Math.max(...values) * 1.04;
  const x = index => pad.left + index * (width - pad.left - pad.right) / Math.max(1, rows.length - 1), y = value => pad.top + (max - value) * (height - pad.top - pad.bottom) / (max - min);
  context.clearRect(0, 0, width, height); context.strokeStyle = "#dce2e8"; context.fillStyle = "#66717f"; context.font = "11px sans-serif";
  for (let i = 0; i <= 4; i++) { const value = min + (max - min) * i / 4, yy = y(value); context.beginPath(); context.moveTo(pad.left, yy); context.lineTo(width - pad.right, yy); context.stroke(); context.fillText(euro.format(value), 0, yy + 4); }
  [["price", "#2b63c6", 1.4], ["short_sma", "#167a5b", 2], ["long_sma", "#7254a7", 2]].forEach(([key, color, lineWidth]) => { context.beginPath(); context.strokeStyle = color; context.lineWidth = lineWidth; rows.forEach((row, index) => index ? context.lineTo(x(index), y(row[key])) : context.moveTo(x(index), y(row[key]))); context.stroke(); });
  [0, Math.floor(rows.length / 2), rows.length - 1].forEach(index => { context.fillStyle = "#66717f"; context.fillText(rows[index].date, Math.min(width - 80, Math.max(pad.left, x(index) - 34)), height - 8); });
}
async function init() {
  try { const [status, history] = await Promise.all([loadJson("data/status.json"), loadJson("data/history.json")]); renderStatus(status); renderChart(history); window.addEventListener("resize", () => renderChart(history), { passive: true }); }
  catch (error) { setText("freshness", `Monitor unavailable: ${error.message}`); }
}
init();
