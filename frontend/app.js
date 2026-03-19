const formatMoney = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--';
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const formatPct = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--';
  return `${Number(value).toFixed(2)}%`;
};

const summaryEls = {
  totalEquity: document.getElementById('totalEquity'),
  totalPnl: document.getElementById('totalPnl'),
  netContributed: document.getElementById('netContributed'),
  numPositions: document.getElementById('numPositions'),
  totalReturn: document.getElementById('totalReturn'),
  maxDrawdown: document.getElementById('maxDrawdown'),
};

const metricsBody = document.querySelector('#metricsTable tbody');
let equityChart = null;

const fetchJson = async (url, options = {}) => {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  return response.json();
};

const loadSummary = async () => {
  const summary = await fetchJson('/api/portfolio/summary');
  summaryEls.totalEquity.textContent = formatMoney(summary.total_equity);
  summaryEls.totalPnl.textContent = `${formatMoney(summary.total_pnl)} (${Number(summary.total_pnl_pct || 0).toFixed(2)}%)`;
  summaryEls.netContributed.textContent = formatMoney(summary.net_contributed);
  summaryEls.numPositions.textContent = summary.num_positions ?? 0;
};

const loadPerformance = async () => {
  const perf = await fetchJson('/api/portfolio/performance');
  summaryEls.totalReturn.textContent = formatPct(perf.total_return_pct ?? 0);
  summaryEls.maxDrawdown.textContent = formatPct((perf.max_drawdown ?? 0) * 100);
};

const renderEquityChart = (points) => {
  const ctx = document.getElementById('equityChart');
  if (!ctx) return;

  const labels = points.map((p) => p.date);
  const values = points.map((p) => p.equity);

  if (equityChart) {
    equityChart.data.labels = labels;
    equityChart.data.datasets[0].data = values;
    equityChart.update();
    return;
  }

  equityChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Equity',
          data: values,
          borderColor: '#1b4d3e',
          backgroundColor: 'rgba(27, 77, 62, 0.1)',
          tension: 0.2,
        },
      ],
    },
    options: {
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { display: true },
        y: { display: true },
      },
    },
  });
};

const loadEquityCurve = async () => {
  const curve = await fetchJson('/api/portfolio/equity-curve?days=90');
  renderEquityChart(curve);
};

const signalBadge = (signals) => {
  const values = Object.values(signals || {});
  const bull = values.filter((s) => s.signal === 'BULL').length;
  const sell = values.filter((s) => s.signal === 'SELL').length;
  const neutral = values.filter((s) => s.signal === 'NEUTRAL').length;
  let cls = 'neutral';
  if (bull > sell) cls = 'bull';
  if (sell > bull) cls = 'sell';
  return `<span class="badge ${cls}">${bull} Bull / ${sell} Sell / ${neutral} Neutral</span>`;
};

const renderMetrics = (metrics) => {
  metricsBody.innerHTML = '';

  metrics.forEach((item) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${item.symbol}</td>
      <td>${formatMoney(item.price)}</td>
      <td>${formatPct(item.position_pct)}</td>
      <td>${formatMoney(item.unrealized_pnl)}</td>
      <td>${signalBadge(item.signals)}</td>
      <td><button class="btn small" data-analyze="${item.symbol}">Analyze</button></td>
      <td><button class="expand-btn" data-expand="${item.symbol}">▾</button></td>
    `;

    const detail = document.createElement('tr');
    detail.className = 'detail-row hidden';
    detail.setAttribute('data-detail', item.symbol);
    detail.innerHTML = `
      <td colspan="7">
        <div class="detail-grid">
          <div class="detail-item"><strong>RSI</strong>${formatPct(item.signals?.rsi?.value)}</div>
          <div class="detail-item"><strong>MACD</strong>${item.signals?.macd?.value?.toFixed?.(3) ?? '--'}</div>
          <div class="detail-item"><strong>SMA50/200</strong>${item.signals?.sma50_200?.signal ?? 'N/A'}</div>
          <div class="detail-item"><strong>EMA20</strong>${item.signals?.ema20?.signal ?? '--'}</div>
          <div class="detail-item"><strong>EMA50</strong>${item.signals?.ema50?.signal ?? '--'}</div>
          <div class="detail-item"><strong>7d Return</strong>${formatPct(item.returns_7d)}</div>
          <div class="detail-item"><strong>30d Return</strong>${formatPct(item.returns_30d)}</div>
          <div class="detail-item"><strong>Volatility</strong>${formatPct(item.volatility_90d)}</div>
          <div class="detail-item"><strong>Drawdown</strong>${formatPct(item.drawdown_30d)}</div>
          <div class="detail-item"><strong>Realized P&L</strong>${formatMoney(item.realized_pnl)}</div>
          <div class="detail-item"><strong>AI Summary</strong><div id="analysis-${item.symbol}" class="muted">Not analyzed</div></div>
        </div>
      </td>
    `;

    metricsBody.appendChild(row);
    metricsBody.appendChild(detail);
  });
};

const loadMetrics = async () => {
  const metrics = await fetchJson('/api/portfolio/asset-metrics?days=90');
  renderMetrics(metrics);
  const cachedAnalyses = await fetchJson('/api/analysis/latest');
  Object.entries(cachedAnalyses || {}).forEach(([symbol, analysis]) => {
    const target = document.getElementById(`analysis-${symbol}`);
    if (!target) return;
    target.textContent = `${analysis.recommendation}: ${analysis.analyst_notes || ''}`;
  });
};

const refreshAll = async () => {
  try {
    await Promise.all([loadSummary(), loadPerformance(), loadEquityCurve(), loadMetrics()]);
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
};

metricsBody.addEventListener('click', async (event) => {
  const expandBtn = event.target.closest('[data-expand]');
  if (expandBtn) {
    const symbol = expandBtn.getAttribute('data-expand');
    const detail = document.querySelector(`[data-detail="${symbol}"]`);
    detail.classList.toggle('hidden');
    expandBtn.textContent = detail.classList.contains('hidden') ? '▾' : '▴';
    return;
  }

  const analyzeBtn = event.target.closest('[data-analyze]');
  if (analyzeBtn) {
    const symbol = analyzeBtn.getAttribute('data-analyze');
    const target = document.getElementById(`analysis-${symbol}`);
    if (target) target.textContent = 'Analyzing...';
    try {
      const result = await fetchJson(`/api/analysis/${symbol}`, { method: 'POST' });
      if (target) {
        target.textContent = `${result.recommendation}: ${result.analyst_notes || ''}`;
      }
    } catch (error) {
      if (target) target.textContent = `Error: ${error.message}`;
    }
  }
});

// Modal logic
const modal = document.getElementById('transactionModal');
const openModalBtn = document.getElementById('addTransaction');
const closeTargets = modal.querySelectorAll('[data-close]');
const tabs = modal.querySelectorAll('.tab');
const forms = modal.querySelectorAll('form[data-form]');

const openModal = () => {
  modal.classList.add('open');
  modal.setAttribute('aria-hidden', 'false');
};

const closeModal = () => {
  modal.classList.remove('open');
  modal.setAttribute('aria-hidden', 'true');
};

openModalBtn.addEventListener('click', openModal);
closeTargets.forEach((el) => el.addEventListener('click', closeModal));

const showForm = (name) => {
  forms.forEach((form) => form.classList.toggle('hidden', form.dataset.form !== name));
  tabs.forEach((tab) => tab.classList.toggle('active', tab.dataset.tab === name));
};

tabs.forEach((tab) => {
  tab.addEventListener('click', () => showForm(tab.dataset.tab));
});

const submitFlow = async (type, amount, notes) => {
  await fetchJson(`/api/${type}`, {
    method: 'POST',
    body: JSON.stringify({ amount, notes }),
  });
};

const submitTrade = async (action, payload) => {
  await fetchJson('/api/trades', {
    method: 'POST',
    body: JSON.stringify({ action, ...payload }),
  });
};

const flowForm = document.getElementById('flowForm');
flowForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await submitFlow('deposit', Number(flowForm.querySelector('#flowAmount').value), flowForm.querySelector('#flowNotes').value || null);
    flowForm.reset();
    closeModal();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const withdrawForm = document.getElementById('withdrawForm');
withdrawForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await submitFlow('withdraw', Number(withdrawForm.querySelector('#withdrawAmount').value), withdrawForm.querySelector('#withdrawNotes').value || null);
    withdrawForm.reset();
    closeModal();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const buyForm = document.getElementById('buyForm');
buyForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await submitTrade('BUY', {
      symbol: buyForm.querySelector('#buySymbol').value,
      quantity: Number(buyForm.querySelector('#buyQuantity').value),
      price: Number(buyForm.querySelector('#buyPrice').value),
      fees: Number(buyForm.querySelector('#buyFees').value || 0),
      notes: buyForm.querySelector('#buyNotes').value || null,
    });
    buyForm.reset();
    closeModal();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const sellForm = document.getElementById('sellForm');
sellForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await submitTrade('SELL', {
      symbol: sellForm.querySelector('#sellSymbol').value,
      quantity: Number(sellForm.querySelector('#sellQuantity').value),
      price: Number(sellForm.querySelector('#sellPrice').value),
      fees: Number(sellForm.querySelector('#sellFees').value || 0),
      notes: sellForm.querySelector('#sellNotes').value || null,
    });
    sellForm.reset();
    closeModal();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const refreshBtn = document.getElementById('refresh');
refreshBtn.addEventListener('click', refreshAll);

refreshAll();
