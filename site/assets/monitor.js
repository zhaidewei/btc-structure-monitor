const euro = new Intl.NumberFormat("en-IE", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
const pct = value => `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;

async function loadJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) throw new Error(`${path}: ${response.status}`);
  return response.json();
}

function setText(id, value) { document.getElementById(id).textContent = value; }

function renderStatus(status) {
  const signal = status.signal;
  const band = document.getElementById("signal-band");
  band.classList.toggle("cash", signal.signal === "CASH");
  setText("signal", signal.signal);
  setText("signal-copy", signal.watch_band ? "均线距离进入观察区，等待确认交叉" : "仅在 SMA35 与 SMA300 交叉时切换");
  setText("price", euro.format(signal.last_price));
  setText("short-sma", euro.format(signal.short_sma));
  setText("long-sma", euro.format(signal.long_sma));
  setText("gap", pct(signal.gap_pct));
  setText("cross-count", signal.crossover_count_12m);
  setText("rapid-count", signal.rapid_reversal_count_12m);
  setText("data-health", status.data_health.status.toUpperCase());
  setText("divergence", pct(status.data_health.divergence_pct));
  setText("freshness", `Signal ${signal.as_of} UTC · Updated ${new Date(status.generated_at).toLocaleString()}`);
}

function buildPeriods(rows) {
  const starts = [0];
  for (let index = 1; index < rows.length; index++) {
    if (rows[index].signal !== rows[index - 1].signal) starts.push(index);
  }
  return starts.map((startIndex, index) => {
    const endIndex = index + 1 < starts.length ? starts[index + 1] : rows.length - 1;
    const start = rows[startIndex];
    const end = rows[endIndex];
    const btcReturnPct = (end.price / start.price - 1) * 100;
    return {
      startIndex,
      endIndex,
      startDate: start.date,
      endDate: end.date,
      signal: start.signal,
      strategyReturnPct: start.signal === "BTC" ? btcReturnPct : 0,
      btcReturnPct,
      current: index === starts.length - 1,
    };
  });
}

function renderChart(rows, periods, activePeriodIndex = -1) {
  const canvas = document.getElementById("trend-chart");
  const context = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const bounds = canvas.getBoundingClientRect();
  canvas.width = Math.max(1, Math.floor(bounds.width * ratio));
  canvas.height = Math.max(1, Math.floor(bounds.height * ratio));
  context.scale(ratio, ratio);

  const width = bounds.width;
  const height = bounds.height;
  const pad = { left: 58, right: 14, top: 48, bottom: 30 };
  const plotWidth = width - pad.left - pad.right;
  const plotHeight = height - pad.top - pad.bottom;
  const values = rows.flatMap(row => [row.price, row.short_sma, row.long_sma]);
  const min = Math.min(...values) * 0.96;
  const max = Math.max(...values) * 1.04;
  const x = index => pad.left + index * plotWidth / Math.max(1, rows.length - 1);
  const y = value => pad.top + (max - value) * plotHeight / (max - min);

  context.clearRect(0, 0, width, height);
  periods.forEach((period, index) => {
    const left = x(period.startIndex);
    const right = x(period.endIndex);
    context.fillStyle = period.signal === "BTC" ? "rgba(22, 122, 91, 0.10)" : "rgba(187, 62, 56, 0.075)";
    context.fillRect(left, pad.top, Math.max(1, right - left), plotHeight);
    if (index === activePeriodIndex) {
      context.fillStyle = period.signal === "BTC" ? "rgba(22, 122, 91, 0.10)" : "rgba(187, 62, 56, 0.10)";
      context.fillRect(left, pad.top, Math.max(2, right - left), plotHeight);
    }
  });

  context.strokeStyle = "#dce2e8";
  context.fillStyle = "#66717f";
  context.font = "11px sans-serif";
  context.lineWidth = 1;
  for (let index = 0; index <= 4; index++) {
    const value = min + (max - min) * index / 4;
    const yy = y(value);
    context.beginPath();
    context.moveTo(pad.left, yy);
    context.lineTo(width - pad.right, yy);
    context.stroke();
    context.fillText(euro.format(value), 0, yy + 4);
  }

  periods.slice(1).forEach(period => {
    const xx = x(period.startIndex);
    context.beginPath();
    context.strokeStyle = period.signal === "BTC" ? "#167a5b" : "#bb3e38";
    context.lineWidth = 1.5;
    context.moveTo(xx, pad.top - 5);
    context.lineTo(xx, height - pad.bottom);
    context.stroke();
  });

  periods.forEach(period => {
    const left = x(period.startIndex);
    const right = x(period.endIndex);
    const label = `${period.signal === "BTC" ? "BTC" : "CASH"} ${pct(period.strategyReturnPct)}`;
    context.font = "600 10px sans-serif";
    const labelWidth = context.measureText(label).width;
    if (right - left >= labelWidth + 10) {
      context.fillStyle = period.signal === "BTC" ? "#126449" : "#a33631";
      context.fillText(label, left + (right - left - labelWidth) / 2, 25);
    }
  });

  [["price", "#2b63c6", 1.4], ["short_sma", "#167a5b", 2], ["long_sma", "#7254a7", 2]].forEach(([key, color, lineWidth]) => {
    context.beginPath();
    context.strokeStyle = color;
    context.lineWidth = lineWidth;
    rows.forEach((row, index) => index ? context.lineTo(x(index), y(row[key])) : context.moveTo(x(index), y(row[key])));
    context.stroke();
  });

  [0, Math.floor(rows.length / 2), rows.length - 1].forEach(index => {
    context.fillStyle = "#66717f";
    context.font = "11px sans-serif";
    context.fillText(rows[index].date, Math.min(width - 80, Math.max(pad.left, x(index) - 34)), height - 8);
  });
  canvas.chartLayout = { pad, plotWidth, periods, rowCount: rows.length };
}

function renderPeriodTable(periods) {
  const body = document.getElementById("period-body");
  body.replaceChildren();
  periods.forEach(period => {
    const row = document.createElement("tr");
    const values = [
      `${period.startDate} — ${period.endDate}`,
      period.signal === "BTC" ? "ALL BTC" : "ALL CASH",
      pct(period.strategyReturnPct),
      pct(period.btcReturnPct),
      period.current ? "进行中" : "已完成",
    ];
    values.forEach((value, index) => {
      const cell = document.createElement(index === 1 ? "th" : "td");
      if (index === 1) cell.scope = "row";
      cell.textContent = value;
      if (index === 1) cell.className = period.signal === "BTC" ? "state-btc" : "state-cash";
      if (index === 2 || index === 3) cell.className = value.startsWith("-") ? "negative" : "positive";
      row.appendChild(cell);
    });
    body.appendChild(row);
  });
}

function showPeriodTooltip(event, period, tooltip) {
  setText("tooltip-title", period.signal === "BTC" ? "ALL BTC" : "ALL CASH");
  setText("tooltip-dates", `${period.startDate} — ${period.endDate}${period.current ? " · 进行中" : ""}`);
  setText("tooltip-strategy", pct(period.strategyReturnPct));
  setText("tooltip-btc", pct(period.btcReturnPct));
  tooltip.hidden = false;
  const wrap = tooltip.parentElement.getBoundingClientRect();
  const tooltipBounds = tooltip.getBoundingClientRect();
  const left = Math.min(wrap.width - tooltipBounds.width - 8, Math.max(8, event.clientX - wrap.left + 14));
  const top = Math.min(wrap.height - tooltipBounds.height - 8, Math.max(8, event.clientY - wrap.top - tooltipBounds.height - 14));
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function bindChartInteraction(rows, periods) {
  const canvas = document.getElementById("trend-chart");
  const tooltip = document.getElementById("chart-tooltip");
  let activePeriodIndex = -1;
  canvas.addEventListener("pointermove", event => {
    const layout = canvas.chartLayout;
    const bounds = canvas.getBoundingClientRect();
    const localX = event.clientX - bounds.left;
    const normalized = (localX - layout.pad.left) / layout.plotWidth;
    const rowIndex = Math.max(0, Math.min(rows.length - 1, Math.round(normalized * (rows.length - 1))));
    const nextPeriodIndex = periods.findIndex((period, index) => rowIndex >= period.startIndex && (index === periods.length - 1 || rowIndex < periods[index + 1].startIndex));
    if (nextPeriodIndex < 0) return;
    if (nextPeriodIndex !== activePeriodIndex) {
      activePeriodIndex = nextPeriodIndex;
      renderChart(rows, periods, activePeriodIndex);
    }
    showPeriodTooltip(event, periods[activePeriodIndex], tooltip);
  });
  canvas.addEventListener("pointerleave", () => {
    activePeriodIndex = -1;
    tooltip.hidden = true;
    renderChart(rows, periods);
  });
  window.addEventListener("resize", () => renderChart(rows, periods, activePeriodIndex), { passive: true });
}

async function init() {
  try {
    const [status, history] = await Promise.all([loadJson("data/status.json"), loadJson("data/history.json")]);
    const periods = buildPeriods(history);
    renderStatus(status);
    renderChart(history, periods);
    renderPeriodTable(periods);
    bindChartInteraction(history, periods);
  } catch (error) {
    setText("freshness", `Monitor unavailable: ${error.message}`);
  }
}

init();
