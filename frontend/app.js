const formatMoney = (value) => {
  if (value === null || value === undefined || Number.isNaN(value)) return '--';
  return `$${Number(value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

const summaryEls = {
  totalEquity: document.getElementById('totalEquity'),
  totalPnl: document.getElementById('totalPnl'),
  netContributed: document.getElementById('netContributed'),
  numPositions: document.getElementById('numPositions'),
};

const positionsBody = document.querySelector('#positionsTable tbody');
const tradesBody = document.querySelector('#tradesTable tbody');
const analysisResult = document.getElementById('analysisResult');

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

const loadPositions = async () => {
  const positions = await fetchJson('/api/positions');
  positionsBody.innerHTML = '';
  positions.forEach((pos) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${pos.symbol}</td>
      <td>${Number(pos.quantity).toFixed(2)}</td>
      <td>${formatMoney(pos.avg_entry_price)}</td>
      <td>${formatMoney(pos.current_price)}</td>
      <td>${formatMoney(pos.market_value)}</td>
      <td>${formatMoney(pos.unrealized_pnl)}</td>
    `;
    positionsBody.appendChild(row);
  });
};

const loadTrades = async () => {
  const trades = await fetchJson('/api/trades');
  tradesBody.innerHTML = '';
  trades.forEach((trade) => {
    const row = document.createElement('tr');
    row.innerHTML = `
      <td>${String(trade.timestamp).slice(0, 10)}</td>
      <td>${trade.action}</td>
      <td>${trade.symbol}</td>
      <td>${Number(trade.quantity).toFixed(2)}</td>
      <td>${formatMoney(trade.price)}</td>
      <td>${formatMoney(trade.total_value)}</td>
      <td>${formatMoney(trade.fees || 0)}</td>
    `;
    tradesBody.appendChild(row);
  });
};

const refreshAll = async () => {
  try {
    await Promise.all([loadSummary(), loadPositions(), loadTrades()]);
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
};

const flowForm = document.getElementById('flowForm');
flowForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const type = document.getElementById('flowType').value;
  const amount = Number(document.getElementById('flowAmount').value);
  const notes = document.getElementById('flowNotes').value || null;

  try {
    await fetchJson(`/api/${type}`, {
      method: 'POST',
      body: JSON.stringify({ amount, notes }),
    });
    flowForm.reset();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const tradeForm = document.getElementById('tradeForm');
tradeForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const payload = {
    action: document.getElementById('tradeAction').value,
    symbol: document.getElementById('tradeSymbol').value,
    quantity: Number(document.getElementById('tradeQuantity').value),
    price: Number(document.getElementById('tradePrice').value),
    fees: Number(document.getElementById('tradeFees').value || 0),
    notes: document.getElementById('tradeNotes').value || null,
  };

  try {
    await fetchJson('/api/trades', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    tradeForm.reset();
    await refreshAll();
  } catch (error) {
    alert(`Error: ${error.message}`);
  }
});

const analysisForm = document.getElementById('analysisForm');
analysisForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const symbol = document.getElementById('analysisSymbol').value.trim();
  if (!symbol) return;

  analysisResult.textContent = 'Analyzing...';
  try {
    const data = await fetchJson(`/api/analysis/${symbol}`, { method: 'POST' });
    analysisResult.textContent = JSON.stringify(data, null, 2);
  } catch (error) {
    analysisResult.textContent = `Error: ${error.message}`;
  }
});

const refreshBtn = document.getElementById('refresh');
refreshBtn.addEventListener('click', refreshAll);

refreshAll();
