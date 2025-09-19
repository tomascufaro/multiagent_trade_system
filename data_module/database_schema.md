# Portfolio Tracking Database Schema

## Database Overview
**Database Type**: SQLite  
**File Location**: `data/portfolio.db`  
**Purpose**: Track investment progress, positions, trades, and performance metrics

---

## Table Structure

### 1. `portfolio_snapshots`
**Purpose**: Daily snapshots of overall portfolio performance

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID | 1, 2, 3... |
| `timestamp` | TEXT NOT NULL | ISO timestamp of snapshot | "2025-01-15T16:00:00Z" |
| `account_id` | TEXT | Alpaca account identifier | "6be4d920-6015-4900-8506-354368617eea" |
| `total_equity` | REAL | Total portfolio value | 99992.09 |
| `cash` | REAL | Available cash | 99706.03 |
| `invested_capital` | REAL | Capital in positions | 286.06 |
| `unrealized_pnl` | REAL | Unrealized profit/loss | 20.50 |
| `realized_pnl` | REAL | Realized profit/loss | 150.25 |
| `total_pnl` | REAL | Total profit/loss | 170.75 |
| `day_change` | REAL | Dollar change from previous day | -7.91 |
| `day_change_pct` | REAL | Percentage change from previous day | -0.79 |

**Unique Constraint**: `(timestamp, account_id)`

**Sample Data**:
```sql
INSERT INTO portfolio_snapshots VALUES (
    1, '2025-01-15T16:00:00Z', '6be4d920-6015-4900-8506-354368617eea',
    99992.09, 99706.03, 286.06, 20.50, 150.25, 170.75, -7.91, -0.79
);
```

---

### 2. `positions`
**Purpose**: Track individual position details and performance

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID | 1, 2, 3... |
| `timestamp` | TEXT NOT NULL | ISO timestamp of position | "2025-01-15T16:00:00Z" |
| `symbol` | TEXT NOT NULL | Trading symbol | "AAPL", "BTC/USD" |
| `side` | TEXT | Position direction | "LONG", "SHORT" |
| `quantity` | REAL | Number of shares/units | 10.0 |
| `avg_entry_price` | REAL | Average entry price | 150.25 |
| `current_price` | REAL | Current market price | 152.30 |
| `market_value` | REAL | Current position value | 1523.00 |
| `cost_basis` | REAL | Total cost of position | 1502.50 |
| `unrealized_pnl` | REAL | Unrealized profit/loss | 20.50 |
| `unrealized_pnl_pct` | REAL | Unrealized P&L percentage | 1.36 |
| `position_size_pct` | REAL | % of total portfolio | 1.52 |
| `days_held` | INTEGER | Days position held | 5 |

**Sample Data**:
```sql
INSERT INTO positions VALUES (
    1, '2025-01-15T16:00:00Z', 'AAPL', 'LONG', 10.0, 150.25, 152.30,
    1523.00, 1502.50, 20.50, 1.36, 1.52, 5
);
```

---

### 3. `trades`
**Purpose**: Record of all buy/sell transactions

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID | 1, 2, 3... |
| `trade_id` | TEXT UNIQUE | Unique trade identifier | "trade_20250115_001" |
| `timestamp` | TEXT NOT NULL | ISO timestamp of trade | "2025-01-15T14:30:00Z" |
| `symbol` | TEXT NOT NULL | Trading symbol | "AAPL" |
| `action` | TEXT | Trade action | "BUY", "SELL", "CLOSE" |
| `quantity` | REAL | Number of shares/units | 10.0 |
| `price` | REAL | Execution price | 150.25 |
| `total_value` | REAL | Total trade value | 1502.50 |
| `commission` | REAL | Commission paid | 0.0 |
| `net_amount` | REAL | Net amount after commission | 1502.50 |
| `reason` | TEXT | Trade reasoning | "Strong bullish conviction" |
| `analysis_confidence` | REAL | Analysis confidence (0-1) | 0.75 |

**Sample Data**:
```sql
INSERT INTO trades VALUES (
    1, 'trade_20250115_001', '2025-01-15T14:30:00Z', 'AAPL', 'BUY',
    10.0, 150.25, 1502.50, 0.0, 1502.50, 'Strong bullish conviction', 0.75
);
```

---

### 4. `performance_metrics`
**Purpose**: Calculated performance metrics by period

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | INTEGER PRIMARY KEY | Auto-incrementing ID | 1, 2, 3... |
| `timestamp` | TEXT NOT NULL | ISO timestamp of calculation | "2025-01-15T16:00:00Z" |
| `period` | TEXT | Time period | "daily", "weekly", "monthly", "ytd", "all_time" |
| `total_return` | REAL | Total return (decimal) | 0.0175 |
| `total_return_pct` | REAL | Total return percentage | 1.75 |
| `sharpe_ratio` | REAL | Risk-adjusted return | 1.25 |
| `max_drawdown` | REAL | Maximum drawdown (decimal) | -0.05 |
| `win_rate` | REAL | Percentage of winning trades | 0.65 |
| `avg_win` | REAL | Average winning trade | 125.50 |
| `avg_loss` | REAL | Average losing trade | -75.25 |
| `profit_factor` | REAL | Gross profit / Gross loss | 1.45 |
| `total_trades` | INTEGER | Total number of trades | 20 |
| `winning_trades` | INTEGER | Number of winning trades | 13 |
| `losing_trades` | INTEGER | Number of losing trades | 7 |

**Sample Data**:
```sql
INSERT INTO performance_metrics VALUES (
    1, '2025-01-15T16:00:00Z', 'all_time', 0.0175, 1.75, 1.25, -0.05,
    0.65, 125.50, -75.25, 1.45, 20, 13, 7
);
```

---

## Database Relationships

```
portfolio_snapshots (1) ←→ (many) positions
    ↓
    └── Links via timestamp and account_id

trades (many) ←→ (1) positions
    ↓
    └── Links via symbol and timestamp

performance_metrics (1) ←→ (many) portfolio_snapshots
    ↓
    └── Calculated from portfolio_snapshots data
```

---

## Key Queries

### 1. Get Latest Portfolio Status
```sql
SELECT * FROM portfolio_snapshots 
ORDER BY timestamp DESC LIMIT 1;
```

### 2. Get Position History for Symbol
```sql
SELECT * FROM positions 
WHERE symbol = 'AAPL' 
ORDER BY timestamp DESC;
```

### 3. Get Trade History
```sql
SELECT * FROM trades 
WHERE symbol = 'AAPL' 
ORDER BY timestamp DESC;
```

### 4. Calculate Daily Returns
```sql
SELECT 
    timestamp,
    total_equity,
    LAG(total_equity) OVER (ORDER BY timestamp) as prev_equity,
    (total_equity - LAG(total_equity) OVER (ORDER BY timestamp)) / 
    LAG(total_equity) OVER (ORDER BY timestamp) as daily_return
FROM portfolio_snapshots 
ORDER BY timestamp;
```

### 5. Get Performance Summary
```sql
SELECT 
    COUNT(*) as total_trades,
    SUM(CASE WHEN action = 'BUY' THEN total_value ELSE 0 END) as total_bought,
    SUM(CASE WHEN action = 'SELL' THEN total_value ELSE 0 END) as total_sold,
    AVG(analysis_confidence) as avg_confidence
FROM trades;
```

---

## Indexes (Recommended)

```sql
-- Performance indexes
CREATE INDEX idx_portfolio_timestamp ON portfolio_snapshots(timestamp);
CREATE INDEX idx_positions_symbol_timestamp ON positions(symbol, timestamp);
CREATE INDEX idx_trades_symbol_timestamp ON trades(symbol, timestamp);
CREATE INDEX idx_trades_trade_id ON trades(trade_id);
CREATE INDEX idx_performance_period ON performance_metrics(period);
```

---

## Data Flow

1. **Daily Snapshot**: Save portfolio_snapshots every day
2. **Position Updates**: Update positions when prices change
3. **Trade Recording**: Record every trade in trades table
4. **Metrics Calculation**: Calculate performance_metrics periodically
5. **Analysis**: Query data for analysis and reporting

---

## Backup Strategy

1. **SQLite Backup**: Copy `portfolio.db` file
2. **JSON Export**: Export to JSON for human readability
3. **CSV Export**: Export tables to CSV for Excel analysis
4. **Cloud Backup**: Sync database file to cloud storage

---

## File Sizes (Estimated)

- **portfolio_snapshots**: ~1KB per day (365KB/year)
- **positions**: ~500 bytes per position per day
- **trades**: ~200 bytes per trade
- **performance_metrics**: ~100 bytes per calculation

**Total estimated size**: <10MB for 1 year of data
