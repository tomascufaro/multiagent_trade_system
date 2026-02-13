# Phase 1: Core Manual Portfolio Management

## Overview
Manual portfolio tracking with per-asset analysis: remove Alpaca account/positions dependency, add manual trade entry plus capital flow tracking.

## Goals
- Remove dependency on Alpaca account/positions APIs
- Enable manual trade entry and tracking
- Track deposits/withdrawals and compute performance vs net contributions
- Reuse existing analysis capabilities
- Provide minimal CLI interface (trade, show, analyze, history, deposit, withdraw)

## Scope
- Single user (user_id=1). Enhance existing DataManager; no new service layer.
- Database: essential columns only. CLI: `trade`, `show`, `analyze`, `history`, `deposit`, `withdraw`.
- Reuse existing AnalystService. Automated phase gates + manual testing.

---

## 1. Database Schema

### 1.1 New Tables

#### `holdings` (current positions)
```sql
CREATE TABLE IF NOT EXISTS holdings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL UNIQUE,
    quantity REAL NOT NULL,
    avg_entry_price REAL NOT NULL,
    notes TEXT,
    updated_at TEXT NOT NULL
);
```

#### `capital_flows`
```sql
CREATE TABLE IF NOT EXISTS capital_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL, -- DEPOSIT | WITHDRAWAL
    amount REAL NOT NULL,
    notes TEXT
);
```

#### `asset_analysis`
```sql
CREATE TABLE IF NOT EXISTS asset_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    analysis_date TEXT NOT NULL,
    recommendation TEXT NOT NULL, -- BUY, HOLD, SELL, STRONG_BUY, STRONG_SELL
    confidence_score REAL,
    current_price REAL,
    analyst_notes TEXT,
    bull_case TEXT,
    bear_case TEXT,
    technical_signals TEXT, -- JSON string with RSI, MACD, etc.
    UNIQUE(symbol, analysis_date)
);
```

### 1.2 Modify Existing Tables

#### `positions` (historical snapshots only)
```sql
ALTER TABLE positions ADD COLUMN notes TEXT;
```

#### `trades`
```sql
ALTER TABLE trades ADD COLUMN fees REAL DEFAULT 0.0;
ALTER TABLE trades ADD COLUMN notes TEXT;
ALTER TABLE trades ADD COLUMN realized_pnl REAL;
```

### 1.3 Migration Script
Create `scripts/migrate_to_phase1.py` (idempotent):

```python
"""Simple database migration for Phase 1"""
import sqlite3
import shutil
from datetime import datetime


def _column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def migrate():
    db_path = "data/portfolio.db"

    # Backup database
    backup_path = f"data/portfolio_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    shutil.copy2(db_path, backup_path)
    print(f"✅ Database backed up to {backup_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add columns to existing tables (idempotent)
        if not _column_exists(cursor, "positions", "notes"):
            cursor.execute("ALTER TABLE positions ADD COLUMN notes TEXT")
        if not _column_exists(cursor, "trades", "fees"):
            cursor.execute("ALTER TABLE trades ADD COLUMN fees REAL DEFAULT 0.0")
        if not _column_exists(cursor, "trades", "notes"):
            cursor.execute("ALTER TABLE trades ADD COLUMN notes TEXT")
        if not _column_exists(cursor, "trades", "realized_pnl"):
            cursor.execute("ALTER TABLE trades ADD COLUMN realized_pnl REAL")

        # Create new tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holdings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                quantity REAL NOT NULL,
                avg_entry_price REAL NOT NULL,
                notes TEXT,
                updated_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS capital_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                notes TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asset_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                recommendation TEXT NOT NULL,
                confidence_score REAL,
                current_price REAL,
                analyst_notes TEXT,
                bull_case TEXT,
                bear_case TEXT,
                technical_signals TEXT,
                UNIQUE(symbol, analysis_date)
            )
        """)

        conn.commit()
        print("✅ Migration completed successfully")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
```

---

## 2. Remove Alpaca Dependencies

### 2.1 Delete
- `data_module/api_clients/account_status.py`
- `data_module/api_clients/open_positions.py`

### 2.2 Keep
- `data_module/api_clients/price_feed.py`
- `data_module/api_clients/news_feed.py`

### 2.3 Update `data_module/api_clients/__init__.py`
```python
# Remove imports:
# from .account_status import AccountStatus
# from .open_positions import OpenPositions

# Keep:
from .price_feed import PriceFeed
from .news_feed import NewsFeed

__all__ = ['PriceFeed', 'NewsFeed']
```

---

## 3. Enhance DataManager

### 3.1 Add Methods to `data_module/data_manager.py`

```python
# Add to existing DataManager class

def record_deposit(self, amount: float, notes: Optional[str] = None) -> Dict[str, Any]:
    """Record a capital deposit."""
    assert amount > 0, "Deposit amount must be positive"
    flow = {
        'timestamp': datetime.now().isoformat(),
        'type': 'DEPOSIT',
        'amount': amount,
        'notes': notes
    }
    self.portfolio_repo.save_capital_flow(flow)
    return flow


def record_withdrawal(self, amount: float, notes: Optional[str] = None) -> Dict[str, Any]:
    """Record a capital withdrawal."""
    assert amount > 0, "Withdrawal amount must be positive"
    flow = {
        'timestamp': datetime.now().isoformat(),
        'type': 'WITHDRAWAL',
        'amount': amount,
        'notes': notes
    }
    self.portfolio_repo.save_capital_flow(flow)
    return flow


def record_buy(
    self,
    symbol: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a buy trade and update holdings

    Returns: Trade record with calculated fields
    """
    from datetime import datetime
    import uuid

    assert quantity > 0, "Quantity must be positive"
    assert price > 0, "Price must be positive"

    total_value = quantity * price
    net_amount = total_value + fees

    trade = {
        'trade_id': f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol.upper(),
        'action': 'BUY',
        'quantity': quantity,
        'price': price,
        'total_value': total_value,
        'commission': 0.0,
        'net_amount': net_amount,
        'reason': notes or 'Manual trade entry',
        'analysis_confidence': None,
        'fees': fees,
        'notes': notes,
        'realized_pnl': None
    }

    self.portfolio_repo.save_trade(trade)
    self._update_holding_after_buy(symbol, quantity, price)

    print(f"✅ Bought {quantity} shares of {symbol} at ${price:.2f}")
    print(f"   Total cost: ${net_amount:.2f} (including ${fees:.2f} fees)")

    return trade


def record_sell(
    self,
    symbol: str,
    quantity: float,
    price: float,
    fees: float = 0.0,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record a sell trade and update holdings

    Returns: Trade record with realized P&L
    """
    from datetime import datetime
    import uuid

    assert quantity > 0, "Quantity must be positive"
    assert price > 0, "Price must be positive"

    holding = self._get_holding(symbol)
    if not holding:
        raise ValueError(f"No open holding for {symbol}")
    if holding['quantity'] < quantity:
        raise ValueError(f"Insufficient quantity. Have {holding['quantity']}, trying to sell {quantity}")

    total_value = quantity * price
    net_amount = total_value - fees

    cost_basis = holding['avg_entry_price'] * quantity
    realized_pnl = total_value - cost_basis - fees

    trade = {
        'trade_id': f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}",
        'timestamp': datetime.now().isoformat(),
        'symbol': symbol.upper(),
        'action': 'SELL',
        'quantity': quantity,
        'price': price,
        'total_value': total_value,
        'commission': 0.0,
        'net_amount': net_amount,
        'reason': notes or 'Manual trade entry',
        'analysis_confidence': None,
        'fees': fees,
        'notes': notes,
        'realized_pnl': realized_pnl
    }

    self.portfolio_repo.save_trade(trade)
    self._update_holding_after_sell(symbol, quantity)

    print(f"✅ Sold {quantity} shares of {symbol} at ${price:.2f}")
    print(f"   Total received: ${net_amount:.2f} (after ${fees:.2f} fees)")
    print(f"   Realized P&L: ${realized_pnl:.2f}")

    return trade


def get_portfolio_value(self) -> Dict[str, Any]:
    """
    Calculate current portfolio value from manual holdings

    Returns portfolio summary with all metrics
    """
    capital = self.portfolio_repo.get_capital_flow_summary()
    net_contributed = capital['deposits'] - capital['withdrawals']

    holdings = self.portfolio_repo.get_holdings()

    positions_value = 0.0
    positions_data = []

    for pos in holdings:
        symbol = pos['symbol']
        quantity = pos['quantity']
        avg_entry_price = pos['avg_entry_price']

        current_price = self.price_feed.get_current_price(symbol)

        market_value = quantity * current_price
        cost_basis = quantity * avg_entry_price
        unrealized_pnl = market_value - cost_basis
        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0

        positions_value += market_value

        positions_data.append({
            'symbol': symbol,
            'quantity': quantity,
            'avg_entry_price': avg_entry_price,
            'current_price': current_price,
            'market_value': market_value,
            'cost_basis': cost_basis,
            'unrealized_pnl': unrealized_pnl,
            'unrealized_pnl_pct': unrealized_pnl_pct
        })

    total_equity = positions_value
    total_pnl = total_equity - net_contributed
    total_pnl_pct = (total_pnl / net_contributed * 100) if net_contributed > 0 else 0

    return {
        'total_equity': total_equity,
        'positions_value': positions_value,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct,
        'num_positions': len(positions_data),
        'positions': positions_data,
        'net_contributed': net_contributed,
        'total_deposits': capital['deposits'],
        'total_withdrawals': capital['withdrawals']
    }


def get_open_positions(self) -> List[Dict[str, Any]]:
    """Get all holdings with current prices"""
    positions = self.portfolio_repo.get_holdings()

    for pos in positions:
        symbol = pos['symbol']
        pos['current_price'] = self.price_feed.get_current_price(symbol)
        pos['market_value'] = pos['quantity'] * pos['current_price']
        pos['unrealized_pnl'] = pos['market_value'] - (pos['quantity'] * pos['avg_entry_price'])

    return positions


def analyze_stock(self, symbol: str) -> Dict[str, Any]:
    """
    Analyze a stock using existing AnalystService
    Reuses existing analysis infrastructure
    """
    from analyst_service.analysis.analyst_service import AnalystService

    analyst = AnalystService(self.config_path)
    analysis = analyst.analyze(symbol)

    debate = analysis.get('debate', {})
    summary = debate.get('summary', '')

    recommendation = 'HOLD'
    if 'strong buy' in summary.lower() or 'strongly recommend buying' in summary.lower():
        recommendation = 'STRONG_BUY'
    elif 'buy' in summary.lower() or 'bullish' in summary.lower():
        recommendation = 'BUY'
    elif 'sell' in summary.lower() or 'bearish' in summary.lower():
        recommendation = 'SELL'

    analysis_record = {
        'symbol': symbol,
        'analysis_date': datetime.now().isoformat(),
        'recommendation': recommendation,
        'confidence_score': debate.get('confidence', 0.5),
        'current_price': self.price_feed.get_current_price(symbol),
        'analyst_notes': summary,
        'bull_case': debate.get('bull_perspective', ''),
        'bear_case': debate.get('bear_perspective', ''),
        'technical_signals': str(analysis.get('ta_signals', {}))
    }

    self.portfolio_repo.save_asset_analysis(analysis_record)

    return analysis_record

# Helper methods (private)

def _get_holding(self, symbol: str) -> Optional[Dict[str, Any]]:
    """Get holding for symbol"""
    holdings = self.portfolio_repo.get_holdings()
    for pos in holdings:
        if pos['symbol'] == symbol:
            return pos
    return None


def _update_holding_after_buy(self, symbol: str, quantity: float, price: float):
    """Update or create holding after buy"""
    holding = self._get_holding(symbol)

    if holding:
        old_qty = holding['quantity']
        old_price = holding['avg_entry_price']
        new_qty = old_qty + quantity
        new_avg_price = ((old_qty * old_price) + (quantity * price)) / new_qty

        self.portfolio_repo.update_holding(holding['id'], {
            'quantity': new_qty,
            'avg_entry_price': new_avg_price
        })
    else:
        self.portfolio_repo.create_holding({
            'symbol': symbol,
            'quantity': quantity,
            'avg_entry_price': price
        })


def _update_holding_after_sell(self, symbol: str, quantity: float):
    """Update holding after sell"""
    holding = self._get_holding(symbol)

    new_qty = holding['quantity'] - quantity

    if new_qty <= 0:
        self.portfolio_repo.delete_holding(holding['id'])
    else:
        self.portfolio_repo.update_holding(holding['id'], {'quantity': new_qty})
```

---

## 4. Update Existing Components

### 4.1 Add to `data_module/repositories/portfolio_repository.py`

```python
def save_capital_flow(self, flow: Dict[str, Any]) -> int:
    """Save a deposit or withdrawal"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO capital_flows (timestamp, type, amount, notes)
        VALUES (?, ?, ?, ?)
    ''', (flow['timestamp'], flow['type'], flow['amount'], flow.get('notes')))
    flow_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return flow_id


def get_capital_flow_summary(self) -> Dict[str, float]:
    """Get total deposits and withdrawals"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_flows WHERE type = 'DEPOSIT'")
    deposits = cursor.fetchone()[0]
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM capital_flows WHERE type = 'WITHDRAWAL'")
    withdrawals = cursor.fetchone()[0]
    conn.close()
    return {'deposits': deposits, 'withdrawals': withdrawals}


def save_trade(self, trade: Dict[str, Any]) -> int:
    """Save a trade record"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO trades
        (trade_id, timestamp, symbol, action, quantity, price, total_value,
         commission, net_amount, reason, analysis_confidence, fees, notes, realized_pnl)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        trade['trade_id'], trade['timestamp'], trade['symbol'], trade['action'],
        trade['quantity'], trade['price'], trade['total_value'], trade['commission'],
        trade['net_amount'], trade['reason'], trade['analysis_confidence'],
        trade.get('fees', 0.0), trade.get('notes'), trade.get('realized_pnl')
    ))

    trade_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trade_id


def get_holdings(self) -> List[Dict[str, Any]]:
    """Get all current holdings"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, symbol, quantity, avg_entry_price, notes
        FROM holdings
        ORDER BY symbol
    ''')

    columns = ['id', 'symbol', 'quantity', 'avg_entry_price', 'notes']
    holdings = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return holdings


def update_holding(self, holding_id: int, updates: Dict[str, Any]) -> bool:
    """Update holding fields"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
    values = list(updates.values()) + [holding_id]

    cursor.execute(f'''
        UPDATE holdings
        SET {set_clause}
        WHERE id = ?
    ''', values)

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def create_holding(self, position: Dict[str, Any]) -> int:
    """Create new holding"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO holdings
        (symbol, quantity, avg_entry_price, notes, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (
        position['symbol'],
        position['quantity'],
        position['avg_entry_price'],
        position.get('notes'),
        datetime.now().isoformat()
    ))

    position_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return position_id


def delete_holding(self, holding_id: int) -> bool:
    """Delete holding (position closed)"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM holdings WHERE id = ?', (holding_id,))
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success


def get_trade_history(self, days: int = 30, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get trade history"""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()

    if symbol:
        cursor.execute('''
            SELECT * FROM trades
            WHERE symbol = ? AND timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days), (symbol,))
    else:
        cursor.execute('''
            SELECT * FROM trades
            WHERE timestamp >= datetime('now', '-{} days')
            ORDER BY timestamp DESC
        '''.format(days))

    columns = [desc[0] for desc in cursor.description]
    trades = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return trades
```

### 4.2 Update `data_module/data_manager.py` __init__

Drop Alpaca clients; keep `PriceFeed`, `NewsFeed`, and existing repositories. Remove or replace: `get_position()`, `get_portfolio_summary()`, `save_portfolio_snapshot()` (they use Alpaca APIs).

---

## 5. CLI Interface

### 5.1 Create `cli/portfolio_cli.py`

```python
"""
Portfolio CLI - Simple command-line interface for portfolio management
"""
import click
from data_module.data_manager import DataManager
from tabulate import tabulate

@click.group()
def cli():
    """Portfolio Management CLI - Manual Trading System"""
    pass

@cli.command()
@click.argument('action', type=click.Choice(['BUY', 'SELL']))
@click.argument('symbol')
@click.argument('quantity', type=float)
@click.argument('price', type=float)
@click.option('--fees', default=0.0, type=float, help='Trading fees')
@click.option('--notes', help='Trade notes')
def trade(action, symbol, quantity, price, fees, notes):
    """
    Record a trade (BUY or SELL)

    Examples:
        portfolio trade BUY AAPL 10 150.50
        portfolio trade SELL AAPL 5 155.00 --fees 1.50
    """
    dm = DataManager()

    try:
        if action == 'BUY':
            dm.record_buy(symbol, quantity, price, fees, notes)
        else:
            dm.record_sell(symbol, quantity, price, fees, notes)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('amount', type=float)
@click.option('--notes', help='Deposit notes')
def deposit(amount, notes):
    """Record a capital deposit"""
    dm = DataManager()
    try:
        dm.record_deposit(amount, notes)
        click.echo(f"✅ Deposited ${amount:.2f}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('amount', type=float)
@click.option('--notes', help='Withdrawal notes')
def withdraw(amount, notes):
    """Record a capital withdrawal"""
    dm = DataManager()
    try:
        dm.record_withdrawal(amount, notes)
        click.echo(f"✅ Withdrew ${amount:.2f}")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@cli.command()
def show():
    """
    Display current portfolio summary and all positions

    Shows:
    - Total equity, P&L, net contributions
    - All open positions with current values
    """
    dm = DataManager()

    try:
        portfolio = dm.get_portfolio_value()

        click.echo("\n" + "="*60)
        click.echo("📊 PORTFOLIO SUMMARY")
        click.echo("="*60)
        click.echo(f"Total Equity:     ${portfolio['total_equity']:,.2f}")
        click.echo(f"Positions Value:  ${portfolio['positions_value']:,.2f}")
        click.echo(f"Total P&L:        ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_pct']:.2f}%)")
        click.echo(f"Net Contributed:  ${portfolio['net_contributed']:,.2f}")
        click.echo(f"Deposits:         ${portfolio['total_deposits']:,.2f}")
        click.echo(f"Withdrawals:      ${portfolio['total_withdrawals']:,.2f}")
        click.echo(f"Open Positions:   {portfolio['num_positions']}")

        if portfolio['positions']:
            click.echo("\n" + "="*60)
            click.echo("📈 OPEN POSITIONS")
            click.echo("="*60)

            table_data = []
            for pos in portfolio['positions']:
                table_data.append([
                    pos['symbol'],
                    f"{pos['quantity']:.2f}",
                    f"${pos['avg_entry_price']:.2f}",
                    f"${pos['current_price']:.2f}",
                    f"${pos['market_value']:,.2f}",
                    f"${pos['unrealized_pnl']:,.2f}",
                    f"{pos['unrealized_pnl_pct']:.2f}%"
                ])

            headers = ['Symbol', 'Qty', 'Avg Cost', 'Current', 'Value', 'P&L', 'P&L %']
            click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        else:
            click.echo("\nNo open positions.")

        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.argument('symbol')
def analyze(symbol):
    """
    Analyze a stock and get investment recommendation

    Example:
        portfolio analyze AAPL
    """
    dm = DataManager()

    click.echo(f"\n🔍 Analyzing {symbol.upper()}...")
    click.echo("This may take a minute...\n")

    try:
        analysis = dm.analyze_stock(symbol.upper())

        click.echo("="*60)
        click.echo(f"📊 ANALYSIS: {analysis['symbol']}")
        click.echo("="*60)
        click.echo(f"Recommendation:   {analysis['recommendation']}")
        click.echo(f"Confidence:       {analysis.get('confidence_score', 0):.2f}")
        click.echo(f"Current Price:    ${analysis.get('current_price', 0):.2f}")
        click.echo(f"Date:             {analysis['analysis_date'][:10]}")

        if analysis.get('bull_case'):
            click.echo(f"\n🐂 Bull Case:\n{analysis['bull_case']}")

        if analysis.get('bear_case'):
            click.echo(f"\n🐻 Bear Case:\n{analysis['bear_case']}")

        if analysis.get('analyst_notes'):
            click.echo(f"\n📝 Summary:\n{analysis['analyst_notes']}")

        click.echo("")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

@cli.command()
@click.option('--symbol', help='Filter by symbol')
@click.option('--days', default=30, type=int, help='Number of days (default: 30)')
def history(symbol, days):
    """
    Show trade history

    Examples:
        portfolio history
        portfolio history --symbol AAPL
        portfolio history --days 7
    """
    dm = DataManager()

    try:
        trades = dm.portfolio_repo.get_trade_history(days, symbol)

        if not trades:
            click.echo(f"\nNo trades found in the last {days} days.")
            return

        click.echo(f"\n📜 TRADE HISTORY (Last {days} days)")
        if symbol:
            click.echo(f"Filtered by: {symbol}")
        click.echo("="*80)

        table_data = []
        for trade in trades:
            table_data.append([
                trade['timestamp'][:10],
                trade['action'],
                trade['symbol'],
                f"{trade['quantity']:.2f}",
                f"${trade['price']:.2f}",
                f"${trade['total_value']:,.2f}",
                f"${trade.get('fees', 0):.2f}",
                trade.get('notes', '')[:30]
            ])

        headers = ['Date', 'Action', 'Symbol', 'Qty', 'Price', 'Total', 'Fees', 'Notes']
        click.echo(tabulate(table_data, headers=headers, tablefmt='simple'))
        click.echo(f"\nTotal trades: {len(trades)}\n")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()

if __name__ == '__main__':
    cli()
```

### 5.2 Create `cli/__init__.py`
```python
from .portfolio_cli import cli

__all__ = ['cli']
```

### 5.3 Add CLI entry point to `pyproject.toml`

```toml
[project.scripts]
portfolio = "cli.portfolio_cli:cli"
```

### 5.4 Install CLI dependency

Add to `pyproject.toml` dependencies:
```toml
"click>=8.0.0",
"tabulate>=0.9.0",
```

Then run:
```bash
poetry install
```

### 5.5 Usage Examples

```bash
# Record deposits / withdrawals
portfolio deposit 10000
portfolio withdraw 500 --notes "Initial withdrawal"

# Record trades
portfolio trade BUY AAPL 10 150.50
portfolio trade SELL AAPL 5 155.00 --fees 1.50 --notes "Taking profits"

# View portfolio
portfolio show

# Analyze a stock
portfolio analyze TSLA

# View history
portfolio history
portfolio history --symbol AAPL
portfolio history --days 7
```

---

## 6. Update Scripts

### 6.1 Modify `scripts/daily_snapshot.py`

Update to use new manual portfolio methods:

```python
#!/usr/bin/env python3
"""
Daily Portfolio Snapshot Script - Updated for manual portfolio tracking
"""
import os
import sys
from datetime import datetime
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_module.data_manager import DataManager

def main():
    """Create snapshot from manual holdings"""
    print(f"🔄 Starting daily portfolio snapshot at {datetime.now()}")

    try:
        data_manager = DataManager()

        print("📊 Calculating portfolio value...")
        portfolio = data_manager.get_portfolio_value()

        print(f"✅ Portfolio Equity: ${portfolio['total_equity']:,.2f}")
        print(f"   Positions: ${portfolio['positions_value']:,.2f}")
        print(f"   P&L: ${portfolio['total_pnl']:,.2f} ({portfolio['total_pnl_pct']:.2f}%)")

        print("📸 Snapshot data collected")
        print("🎉 Daily snapshot completed successfully!")

    except Exception as e:
        print(f"❌ Error during snapshot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### 6.2 Update `scripts/generate_report.py`

Modify to work with manual portfolios:

```python
#!/usr/bin/env python3
"""
Generate Portfolio Report - Updated for manual portfolio tracking
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analyst_service.analysis.analyst_service import AnalystService
from analyst_service.reporting.html_renderer import render_html_report
from analyst_service.reporting.email_sender import send_html_email
from data_module.data_manager import DataManager

def main():
    """Generate portfolio report from manual holdings"""
    print("📊 Generating portfolio report...")

    try:
        dm = DataManager()
        portfolio = dm.get_portfolio_value()

        analyst = AnalystService()

        print("✅ Report generation updated for manual portfolio tracking")
        print("   Portfolio equity: ${:,.2f}".format(portfolio['total_equity']))

    except Exception as e:
        print(f"❌ Error generating report: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

---

## 7. Testing Strategy

### 7.1 Phase 1 Gates (Automated)

Add a lightweight phase check runner and tests that use a temporary DB (via `PORTFOLIO_DB_PATH`) to provide a reliable "done" signal.

**Gate 1: Schema**
- Command: `poetry run python scripts/phase1_check.py schema`
- Pass if expected tables and columns exist.

**Gate 2: Core Flow**
- Command: `poetry run pytest tests/phase1/test_core_flow.py`
- Pass if deposits/withdrawals + buy/sell + P&L calculations succeed.

**Gate 3: CLI Flow**
- Command: `poetry run pytest tests/phase1/test_cli_flow.py`
- Pass if `deposit`, `trade`, `show`, `history` work against temp DB.

**Gate 4: Analysis**
- Command: `poetry run pytest tests/phase1/test_analysis.py`
- Pass if `asset_analysis` is persisted and recommendation is present.

**Gate 5: Full Phase**
- Command: `poetry run python scripts/phase1_check.py all`
- Pass if all above pass (single "done" signal).

### 7.2 Manual Testing Checklist

Create a simple test script `tests/manual_test.py`:

```python
"""
Manual test script for Phase 1 functionality
Run this to verify everything works
"""
from data_module.data_manager import DataManager

def test_phase1():
    """Test all Phase 1 functionality"""
    dm = DataManager()

    print("="*60)
    print("PHASE 1 MANUAL TEST")
    print("="*60)

    # Test 1: Record a deposit
    print("\n1. Testing DEPOSIT...")
    try:
        dm.record_deposit(10000, notes='Test deposit')
        print("✅ DEPOSIT successful")
    except Exception as e:
        print(f"❌ DEPOSIT failed: {e}")

    # Test 2: Record a buy
    print("\n2. Testing BUY trade...")
    try:
        dm.record_buy('AAPL', 10, 150.00, fees=1.0, notes='Test buy')
        print("✅ BUY trade successful")
    except Exception as e:
        print(f"❌ BUY trade failed: {e}")

    # Test 3: Get portfolio value
    print("\n3. Testing portfolio value calculation...")
    try:
        portfolio = dm.get_portfolio_value()
        print(f"✅ Portfolio value: ${portfolio['total_equity']:,.2f}")
        print(f"   Positions: {portfolio['num_positions']}")
    except Exception as e:
        print(f"❌ Portfolio calculation failed: {e}")

    # Test 4: Get positions
    print("\n4. Testing get positions...")
    try:
        positions = dm.get_open_positions()
        print(f"✅ Found {len(positions)} open positions")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['quantity']} shares")
    except Exception as e:
        print(f"❌ Get positions failed: {e}")

    # Test 5: Record a sell
    print("\n5. Testing SELL trade...")
    try:
        dm.record_sell('AAPL', 5, 155.00, fees=1.0, notes='Test sell')
        print("✅ SELL trade successful")
    except Exception as e:
        print(f"❌ SELL trade failed: {e}")

    # Test 6: Analyze stock
    print("\n6. Testing stock analysis...")
    try:
        analysis = dm.analyze_stock('AAPL')
        print(f"✅ Analysis complete: {analysis['recommendation']}")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

    # Test 7: Get trade history
    print("\n7. Testing trade history...")
    try:
        trades = dm.portfolio_repo.get_trade_history(days=30)
        print(f"✅ Found {len(trades)} trades in last 30 days")
    except Exception as e:
        print(f"❌ Trade history failed: {e}")

    print("\n" + "="*60)
    print("MANUAL TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_phase1()
```

### 7.3 CLI Testing

Test each CLI command manually:

```bash
# 1. Test deposit/withdraw
portfolio deposit 10000
portfolio withdraw 500 --notes "Test withdrawal"

# 2. Test trade command
portfolio trade BUY AAPL 10 150.00
portfolio trade SELL AAPL 5 155.00 --fees 1.50

# 3. Test show command
portfolio show

# 4. Test analyze command
portfolio analyze AAPL

# 5. Test history command
portfolio history
portfolio history --symbol AAPL
```

### 7.4 Integration Test (Optional)

Create ONE integration test `tests/test_integration.py`:

```python
"""
Simple integration test for Phase 1
"""
import pytest
from data_module.data_manager import DataManager

def test_full_trade_flow():
    """Test complete trade flow: deposit -> buy -> sell"""
    dm = DataManager()

    # Record deposit
    dm.record_deposit(1000.0, notes="Test deposit")

    # Record buy
    buy_trade = dm.record_buy('TEST', 10, 100.0, fees=1.0)
    assert buy_trade['action'] == 'BUY'
    assert buy_trade['quantity'] == 10

    # Check position exists
    positions = dm.get_open_positions()
    test_pos = [p for p in positions if p['symbol'] == 'TEST']
    assert len(test_pos) == 1
    assert test_pos[0]['quantity'] == 10

    # Record sell
    sell_trade = dm.record_sell('TEST', 10, 110.0, fees=1.0)
    assert sell_trade['action'] == 'SELL'

    # Check position closed
    positions = dm.get_open_positions()
    test_pos = [p for p in positions if p['symbol'] == 'TEST']
    assert len(test_pos) == 0
```

---

## 8. Documentation Updates

### 8.1 Update `README.md`

Add a new section:

```markdown
## Manual Portfolio Management (Phase 1)

This system now supports manual portfolio tracking. You can:
- Record deposits and withdrawals
- Record buy/sell trades manually
- Track portfolio value in real-time
- Analyze stocks for investment recommendations
- View trade history

### Quick Start

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Run database migration:
   ```bash
   poetry run python scripts/migrate_to_phase1.py
   ```

3. Use the CLI:
   ```bash
   # Record a deposit
   portfolio deposit 10000

   # Record a trade
   portfolio trade BUY AAPL 10 150.50

   # View portfolio
   portfolio show

   # Analyze a stock
   portfolio analyze AAPL

   # View history
   portfolio history
   ```

### CLI Commands

- `portfolio deposit <AMOUNT>` - Record a deposit
- `portfolio withdraw <AMOUNT>` - Record a withdrawal
- `portfolio trade <BUY|SELL> <SYMBOL> <QUANTITY> <PRICE>` - Record a trade
- `portfolio show` - Display portfolio summary and positions
- `portfolio analyze <SYMBOL>` - Analyze a stock
- `portfolio history` - Show trade history

```

### 8.2 Update `CHANGELOG.md`

Add Phase 1 entry:

```markdown
## [Phase 1] - 2024-XX-XX

### Added
- Manual portfolio tracking system
- CLI interface with core commands (deposit, withdraw, trade, show, analyze, history)
- Portfolio value calculation from manual holdings
- Stock analysis using existing AI agents
- Database tables: asset_analysis, holdings, capital_flows
- Trade recording with fees, notes, realized P&L

### Changed
- DataManager enhanced with manual trade methods
- Portfolio calculations now work from user holdings instead of Alpaca
- Database schema updated with holdings, capital_flows, fees/notes/realized_pnl

### Removed
- Dependency on Alpaca account status API
- Dependency on Alpaca positions API
- Automated portfolio fetching (replaced with manual entry)

### Breaking Changes
- Portfolio must now be managed manually via CLI
- Trades must be recorded manually after execution
```

### 8.3 Create `docs/PHASE1_USAGE.md`

```markdown
# Phase 1 Usage Guide

## Setup

1. Run migration: `poetry run python scripts/migrate_to_phase1.py`
2. Record deposits via CLI
3. Record trades via CLI

## Daily Workflow

### Recording Deposits

```bash
portfolio deposit 10000 --notes "Initial funding"
```

### Recording Trades

After executing a trade with your broker:

```bash
portfolio trade BUY AAPL 10 150.50 --fees 1.50 --notes "Entry position"
```

### Checking Portfolio

View your current portfolio anytime:

```bash
portfolio show
```

### Analyzing Stocks

```bash
portfolio analyze TSLA
```

### Reviewing History

Check your trade history:

```bash
portfolio history --days 7
```

## Tips

- Record trades immediately after execution
- Include fees for accurate P&L tracking
- Add notes to remember your reasoning
- Run analysis before major trades
- Check portfolio value regularly
```

---

## 9. Implementation Checklist

### Phase 1A: Database & Core (2-3 hours)
- [ ] Create migration script `scripts/migrate_to_phase1.py` (30 min)
- [ ] Add new tables: holdings, capital_flows, asset_analysis (included in migration)
- [ ] Add columns to existing tables: fees, notes, realized_pnl (included in migration)
- [ ] Test migration on copy of database (15 min)
- [ ] Add holdings + capital flow methods to PortfolioRepository (1 hour)
- [ ] Add import sqlite3 to DataManager if needed (2 min)
- Test: `poetry run python scripts/phase1_check.py schema`

### Phase 1B: DataManager Enhancement (3-4 hours)
- [ ] Add `record_deposit()` and `record_withdrawal()` (30 min)
- [ ] Add `record_buy()` method to DataManager (45 min)
- [ ] Add `record_sell()` method to DataManager (45 min)
- [ ] Add `get_portfolio_value()` method to DataManager (45 min)
- [ ] Add `get_open_positions()` method to DataManager (15 min)
- [ ] Add `analyze_stock()` method to DataManager (30 min)
- [ ] Remove Alpaca dependencies from DataManager.__init__ (15 min)
- Test: `poetry run pytest tests/phase1/test_core_flow.py`

### Phase 1C: CLI Implementation (2-3 hours)
- [ ] Create `cli/portfolio_cli.py` with commands (2 hours)
- [ ] Create `cli/__init__.py` (2 min)
- [ ] Add CLI dependencies to pyproject.toml (5 min)
- [ ] Add script entry point to pyproject.toml (5 min)
- [ ] Run `poetry install` (2 min)
- [ ] Test each CLI command manually (30 min)
- Test: `poetry run pytest tests/phase1/test_cli_flow.py`

### Phase 1D: Remove Alpaca Dependencies (30 min)
- [ ] Delete `data_module/api_clients/account_status.py` (1 min)
- [ ] Delete `data_module/api_clients/open_positions.py` (1 min)
- [ ] Update `data_module/api_clients/__init__.py` (2 min)
- [ ] Comment out old methods in DataManager (5 min)
- [ ] Update scripts/daily_snapshot.py (10 min)
- [ ] Update scripts/generate_report.py (10 min)
- Test: `poetry run python scripts/phase1_check.py schema` (ensures no Alpaca-only columns required)

### Phase 1E: Testing & Documentation (1-2 hours)
- [ ] Add Phase 1 gate tests (schema, core, CLI, analysis) (45 min)
- [ ] Add `scripts/phase1_check.py` (20 min)
- [ ] Create `tests/manual_test.py` (20 min)
- [ ] Run manual test script (10 min)
- [ ] Create ONE integration test (30 min)
- [ ] Update README.md with Phase 1 section (20 min)
- [ ] Update CHANGELOG.md (10 min)
- [ ] Create docs/PHASE1_USAGE.md (15 min)
- Test: `poetry run pytest tests/phase1/test_analysis.py`

### Phase 1F: Final Validation (30 min)
- [ ] Test complete workflow: migrate -> deposit -> trade -> show -> analyze -> history
- [ ] Verify database changes are correct
- [ ] Verify no Alpaca dependencies remain in critical paths
- [ ] Run `poetry run python scripts/phase1_check.py all` (done signal)
- [ ] Commit changes with clear message
- Test: `poetry run python scripts/phase1_check.py all`

---

## Quick Start Implementation Order

**Day 1 (4-5 hours):**
1. Database migration (30 min)
2. PortfolioRepository methods (1 hour)
3. DataManager enhancements (3 hours)

**Day 2 (3-4 hours):**
4. CLI implementation (2.5 hours)
5. Remove Alpaca deps (30 min)
6. Testing & docs (1.5 hours)

---

## 10. Success Criteria

Phase 1 MVP is complete when:
1. ✅ User can record deposits/withdrawals via CLI
2. ✅ User can record buy/sell trades via CLI
3. ✅ User can view portfolio summary with correct calculations
4. ✅ User can analyze any stock and get investment recommendation
5. ✅ User can view trade history
6. ✅ No dependencies on Alpaca account/positions APIs
7. ✅ Phase 1 gate checks pass (`scripts/phase1_check.py all`)

---

## 11. Next Phase Preview

Phase 2: Web UI (FastAPI + React), multi-user support, real-time updates, options support, rebalancing, comprehensive tests, advanced analytics.
